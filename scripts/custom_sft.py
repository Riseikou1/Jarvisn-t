"""Focused SFT for Jarvisn't identity and personality data.

Run as:

    python -m scripts.custom_sft

Or with distributed training:

    torchrun --standalone --nproc_per_node=8 -m scripts.custom_sft -- --device-batch-size=16

Unlike ``chat_sft.py``, this script trains only on the two local Jarvisn't
datasets and does not run validation, ChatCORE, or any other evaluation.
"""

import argparse
import gc
import os
import time

os.environ["PYTORCH_ALLOC_CONF"] = "expandable_segments:True"

import torch
import torch.distributed as dist
import wandb

from jarvisnt.checkpoint_manager import load_model, load_optimizer_state, save_checkpoint
from jarvisnt.common import (
    COMPUTE_DTYPE,
    COMPUTE_DTYPE_REASON,
    DummyWandb,
    autodetect_device_type,
    compute_cleanup,
    compute_init,
    get_base_dir,
    get_peak_flops,
    is_ddp_initialized,
    print0,
)
from jarvisnt.flash_attention import HAS_FA3
from tasks.common import TaskMixture
from tasks.local_jsonl import LocalJSONL


parser = argparse.ArgumentParser(description="Focused identity/personality SFT for Jarvisn't")
parser.add_argument("--run", type=str, default="dummy", help="wandb run name ('dummy' disables logging)")
parser.add_argument("--device-type", type=str, default="", help="cuda|cpu|mps (empty = autodetect)")
parser.add_argument("--model-tag", type=str, default=None, help="base model tag to load")
parser.add_argument("--model-step", type=int, default=None, help="base model step to load")
parser.add_argument("--source", choices=["base", "sft"], default="sft", help="checkpoint to specialize (default: existing chat SFT)")
parser.add_argument("--load-optimizer", type=int, default=1, help="warm-start optimizer state (0=no, 1=yes)")
parser.add_argument("--num-iterations", type=int, default=100, help="optimizer steps to run")
parser.add_argument("--max-seq-len", type=int, default=None)
parser.add_argument("--device-batch-size", type=int, default=None)
parser.add_argument("--total-batch-size", type=int, default=None)
parser.add_argument("--embedding-lr", type=float, default=None)
parser.add_argument("--unembedding-lr", type=float, default=None)
parser.add_argument("--matrix-lr", type=float, default=None)
parser.add_argument("--init-lr-frac", type=float, default=0.8)
parser.add_argument("--warmup-ratio", type=float, default=0.0)
parser.add_argument("--warmdown-ratio", type=float, default=0.5)
parser.add_argument("--final-lr-frac", type=float, default=0.0)
parser.add_argument("--identity-epochs", type=int, default=8)
parser.add_argument("--personality-epochs", type=int, default=4)
args = parser.parse_args()
if args.num_iterations <= 0:
    parser.error("--num-iterations must be a positive number of optimizer steps")
user_config = vars(args).copy()

device_type = autodetect_device_type() if args.device_type == "" else args.device_type
ddp, ddp_rank, _ddp_local_rank, ddp_world_size, device = compute_init(device_type)
master_process = ddp_rank == 0
print0(f"COMPUTE_DTYPE: {COMPUTE_DTYPE} ({COMPUTE_DTYPE_REASON})")
synchronize = torch.cuda.synchronize if device_type == "cuda" else lambda: None
get_max_memory = torch.cuda.max_memory_allocated if device_type == "cuda" else lambda: 0
if device_type == "cuda":
    gpu_peak_flops = get_peak_flops(torch.cuda.get_device_name(0))
else:
    gpu_peak_flops = float("inf")

use_dummy_wandb = args.run == "dummy" or not master_process
wandb_run = (
    DummyWandb()
    if use_dummy_wandb
    else wandb.init(project="jarvisnt-custom-sft", name=args.run, config=user_config)
)

if not HAS_FA3:
    print0("WARNING: Flash Attention 3 not available; using PyTorch SDPA fallback.")

model, tokenizer, meta = load_model(
    args.source, device, phase="train", model_tag=args.model_tag, step=args.model_step
)
pretrain_user_config = meta.get("user_config", {})
for name, fallback, source in [
    ("max_seq_len", 2048, meta),
    ("device_batch_size", 32, meta),
    ("total_batch_size", 524288, meta),
    ("embedding_lr", 0.3, pretrain_user_config),
    ("unembedding_lr", 0.004, pretrain_user_config),
    ("matrix_lr", 0.02, pretrain_user_config),
]:
    if getattr(args, name) is None:
        setattr(args, name, source.get(name, fallback))
        print0(f"Inherited {name}={getattr(args, name)}")

orig_model = model
model = torch.compile(model, dynamic=False)
depth = model.config.n_layer
num_flops_per_token = model.estimate_flops()
tokens_per_fwdbwd = args.device_batch_size * args.max_seq_len
world_tokens_per_fwdbwd = tokens_per_fwdbwd * ddp_world_size
assert args.total_batch_size % world_tokens_per_fwdbwd == 0, (
    f"total_batch_size ({args.total_batch_size}) must be a multiple of "
    f"{world_tokens_per_fwdbwd}"
)
grad_accum_steps = args.total_batch_size // world_tokens_per_fwdbwd
print0(f"Tokens / micro-batch / rank: {tokens_per_fwdbwd:,}")
print0(f"Gradient accumulation steps: {grad_accum_steps}")

optimizer = model.setup_optimizer(
    unembedding_lr=args.unembedding_lr,
    embedding_lr=args.embedding_lr,
    matrix_lr=args.matrix_lr,
    weight_decay=0.0,
)
if args.load_optimizer:
    optimizer_data = load_optimizer_state(
        args.source, device, rank=ddp_rank, model_tag=args.model_tag, step=args.model_step
    )
    if optimizer_data is not None:
        base_lrs = [group["lr"] for group in optimizer.param_groups]
        optimizer.load_state_dict(optimizer_data)
        del optimizer_data
        for group, base_lr in zip(optimizer.param_groups, base_lrs):
            group["lr"] = base_lr
        print0("Loaded optimizer state from pretrained checkpoint (learning rates reset).")
    else:
        print0("WARNING: optimizer checkpoint not found; using a fresh optimizer.")

scaler = torch.amp.GradScaler() if COMPUTE_DTYPE == torch.float16 else None
for group in optimizer.param_groups:
    group["lr"] *= args.init_lr_frac
    group["initial_lr"] = group["lr"]

identity_task = LocalJSONL("sft_dataset/identity.jsonl")
personality_task = LocalJSONL("sft_dataset/personality.jsonl")
train_dataset = TaskMixture(
    [
        *([identity_task] * args.identity_epochs),
        *([personality_task] * args.personality_epochs),
    ]
)
print0(
    f"Custom SFT mixture: {len(identity_task)} identity x{args.identity_epochs} + "
    f"{len(personality_task)} personality x{args.personality_epochs} = "
    f"{len(train_dataset):,} conversations"
)

current_epoch = 1


def sft_data_generator(buffer_size=100):
    global current_epoch
    dataset_size = len(train_dataset)
    row_capacity = args.max_seq_len + 1
    bos_token = tokenizer.get_bos_token_id()
    conv_buffer = []
    cursor = ddp_rank
    consumed = 0
    epoch = 1
    iteration = 0

    def refill_buffer():
        nonlocal cursor, epoch
        while len(conv_buffer) < buffer_size:
            conversation = train_dataset[cursor]
            ids, mask = tokenizer.render_conversation(conversation)
            conv_buffer.append((ids, mask))
            cursor += ddp_world_size
            if cursor >= dataset_size:
                cursor %= dataset_size
                epoch += 1

    while True:
        rows, mask_rows, row_lengths = [], [], []
        for _ in range(args.device_batch_size):
            row, mask_row = [], []
            padded = False
            while len(row) < row_capacity:
                while len(conv_buffer) < buffer_size:
                    refill_buffer()
                remaining = row_capacity - len(row)
                best_idx, best_len = -1, 0
                for i, (conversation, _mask) in enumerate(conv_buffer):
                    if len(conversation) <= remaining and len(conversation) > best_len:
                        best_idx, best_len = i, len(conversation)
                if best_idx < 0:
                    content_len = len(row)
                    row.extend([bos_token] * remaining)
                    mask_row.extend([0] * remaining)
                    padded = True
                    break
                conversation, conversation_mask = conv_buffer.pop(best_idx)
                row.extend(conversation)
                mask_row.extend(conversation_mask)
                consumed += ddp_world_size
            row_lengths.append(len(row) if not padded else content_len)
            rows.append(row[:row_capacity])
            mask_rows.append(mask_row[:row_capacity])

        iteration += 1
        current_epoch = epoch

        use_cuda = device_type == "cuda"
        batch = torch.tensor(rows, dtype=torch.long, pin_memory=use_cuda)
        inputs = batch[:, :-1].to(device=device, dtype=torch.int32, non_blocking=use_cuda).contiguous()
        targets = batch[:, 1:].to(device=device, dtype=torch.int64, non_blocking=use_cuda).contiguous()
        mask_targets = torch.tensor(mask_rows, dtype=torch.int8)[:, 1:].to(device=device)
        targets[mask_targets == 0] = -1
        for i, content_len in enumerate(row_lengths):
            if content_len < row_capacity:
                targets[i, content_len - 1 :] = -1
        yield inputs, targets


def get_lr_multiplier(progress):
    if args.warmup_ratio and progress < args.warmup_ratio:
        return (progress + 1e-8) / args.warmup_ratio
    if not args.warmdown_ratio or progress <= 1.0 - args.warmdown_ratio:
        return 1.0
    decay = (progress - (1.0 - args.warmdown_ratio)) / args.warmdown_ratio
    return (1 - decay) + decay * args.final_lr_frac


def get_muon_momentum(step):
    frac = min(step / 300, 1)
    return (1 - frac) * 0.85 + frac * 0.95


train_loader = sft_data_generator()
x, y = next(train_loader)
progress = 0.0
smooth_train_loss = 0.0
total_training_time = 0.0
step = 0
ema_beta = 0.9
base_dir = get_base_dir()

while step < args.num_iterations:
    synchronize()
    start = time.time()
    for _micro_step in range(grad_accum_steps):
        loss = model(x, y)
        train_loss = loss.detach()
        loss = loss / grad_accum_steps
        if scaler is not None:
            scaler.scale(loss).backward()
        else:
            loss.backward()
        x, y = next(train_loader)
        progress = (step + 1) / args.num_iterations

    learning_rate_multiplier = get_lr_multiplier(progress)
    for group in optimizer.param_groups:
        group["lr"] = group["initial_lr"] * learning_rate_multiplier
        if group["kind"] == "muon":
            group["momentum"] = get_muon_momentum(step)
    if scaler is not None:
        scaler.unscale_(optimizer)
        if is_ddp_initialized():
            for value in scaler._found_inf_per_device(optimizer).values():
                dist.all_reduce(value, op=dist.ReduceOp.MAX)
        scaler.step(optimizer)
        scaler.update()
    else:
        optimizer.step()
    model.zero_grad(set_to_none=True)
    synchronize()
    elapsed = time.time() - start
    step += 1
    smooth_train_loss = ema_beta * smooth_train_loss + (1 - ema_beta) * train_loss.item()
    displayed_loss = smooth_train_loss / (1 - ema_beta ** (step + 1))
    total_training_time += elapsed if step > 10 else 0
    tok_per_sec = int(args.total_batch_size / elapsed)
    flops_per_sec = num_flops_per_token * args.total_batch_size / elapsed
    mfu = 100 * flops_per_sec / (gpu_peak_flops * ddp_world_size)
    print0(
        f"step {step:05d} ({100 * progress:.2f}%) | loss: {displayed_loss:.6f} | "
        f"lrm: {learning_rate_multiplier:.2f} | dt: {elapsed * 1000:.2f}ms | "
        f"tok/sec: {tok_per_sec:,} | mfu: {mfu:.2f} | epoch: {current_epoch}"
    )
    if step % 10 == 0:
        wandb_run.log(
            {
                "step": step,
                "total_training_flops": num_flops_per_token * args.total_batch_size * step,
                "total_training_time": total_training_time,
                "train/loss": displayed_loss,
                "train/lrm": learning_rate_multiplier,
                "train/dt": elapsed,
                "train/tok_per_sec": tok_per_sec,
                "train/mfu": mfu,
                "train/epoch": current_epoch,
            }
        )
    if step == 1:
        gc.collect()
        gc.freeze()
        gc.disable()
    elif step % 5000 == 0:
        gc.collect()

output_dirname = args.model_tag if args.model_tag else f"d{depth}"
checkpoint_dir = os.path.join(base_dir, "customsft_checkpoints", output_dirname)
save_checkpoint(
    checkpoint_dir,
    step,
    orig_model.state_dict(),
    optimizer.state_dict(),
    {
        "step": step,
        "model_config": {
            "sequence_len": args.max_seq_len,
            "vocab_size": tokenizer.get_vocab_size(),
            "n_layer": depth,
            "n_head": model.config.n_head,
            "n_kv_head": model.config.n_kv_head,
            "n_embd": model.config.n_embd,
            "window_pattern": model.config.window_pattern,
        },
        "user_config": user_config,
    },
    rank=ddp_rank,
)

print0(f"Peak memory usage: {get_max_memory() / 1024 / 1024:.2f}MiB")
print0(f"Total training time: {total_training_time / 60:.2f}m")
wandb_run.finish()
compute_cleanup()
