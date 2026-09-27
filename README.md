# Jarvisn't

Jarvisn't is Temuujin's small language-model project: a readable, end-to-end stack for learning how tokenization, pretraining, supervised fine-tuning, evaluation, and inference fit together.

> **Status:** in development. The training infrastructure and a bootstrap SFT dataset are present, but Jarvisn't has not been pretrained or fine-tuned yet. There are no published checkpoints or benchmark results.

## What is Jarvisn't?

Jarvisn't is an independently developed language-model project built to study the whole training pipeline rather than wrap a commercial model API. The codebase keeps the deliberately compact structure of its technical foundation while giving the project its own package, documentation, identity, and web presence.

The project is maintained by **Temuujin**.

## Current status

| Area | Status |
| --- | --- |
| Tokenizer | Training and evaluation tooling is implemented; no trained artifact is committed |
| Pretraining | Pipeline is implemented; training has not started |
| SFT | A 1,320-example bootstrap corpus is prepared; training has not run |
| Evaluation | Tooling is present; results are pending a trained checkpoint |
| Inference | CLI/runtime code is present; no live model endpoint exists |

## Architecture and training stack

Jarvisn't uses a decoder-only Transformer implemented in PyTorch. The current code includes rotary embeddings, RMS normalization, QK normalization, grouped-query attention support, ReLU-squared MLPs, configurable sliding-window attention, Flash Attention 3 support with an SDPA fallback, and KV-cached generation.

The main configuration is selected per training run. Current defaults include:

- 32,768-token BPE vocabulary;
- 2,048-token training context;
- depth-driven model width and head configuration;
- ClimbMix parquet shards as the configured pretraining source;
- Muon/AdamW optimization and distributed training support.

These are code defaults, not claims about a trained Jarvisn't checkpoint.

## Setup

Jarvisn't uses [uv](https://docs.astral.sh/uv/) for Python dependency management and requires Python 3.10 or newer.

```bash
uv sync --extra cpu
source .venv/bin/activate
```

For a CUDA 12.8 environment, use the `gpu` extra instead:

```bash
uv sync --extra gpu
```

Generated artifacts default to `~/.cache/jarvisnt`. Override that location with:

```bash
export JARVISNT_BASE_DIR=/path/to/jarvisnt-cache
```

`NANOCHAT_BASE_DIR` remains an inexpensive compatibility fallback for existing caches; nothing is moved or copied automatically. `JARVISNT_DTYPE` can be set to `bfloat16`, `float16`, or `float32` when an explicit compute dtype is needed, with `NANOCHAT_DTYPE` accepted as a legacy fallback.

## Dataset preparation

The configured pretraining dataset is downloaded on demand from the upstream ClimbMix distribution. This is a large-data operation; choose a shard count deliberately.

```bash
python -m jarvisnt.dataset -n 8
```

The local bootstrap instruction dataset lives in `sft_dataset/`. Validate its structure without training:

```bash
python sft_dataset/validate.py \
  sft_dataset/train.jsonl \
  sft_dataset/valid.jsonl \
  sft_dataset/test.jsonl
```

## Tokenizer

Train and evaluate the RustBPE tokenizer after preparing source shards:

```bash
python -m scripts.tok_train --vocab-size=32768
python -m scripts.tok_eval
```

Tokenizer artifacts are written below `$JARVISNT_BASE_DIR/tokenizer` (or the default cache directory). Tokenizer training is intentionally not part of ordinary test or setup commands.

## Training

The scripts below launch real model training and can be expensive. Review their options and hardware requirements before running them.

```bash
# Pretraining
python -m scripts.base_train --help

# Supervised fine-tuning, after a compatible base checkpoint exists
python -m scripts.chat_sft --help
```

Reference recipes live in `runs/`. They are documentation and launch scripts, not evidence that Jarvisn't has already been trained. The architecture, optimizer, schedules, and dataset mixture remain intentionally close to the upstream technical foundation.

## Evaluation

Evaluation requires a compatible trained checkpoint:

```bash
python -m scripts.base_eval --help
python -m scripts.chat_eval --help
```

The repository includes bits-per-byte evaluation, CORE tasks, chat evaluation, and inference benchmarking. No Jarvisn't scores are published yet.

## Local inference API

The local HTTP API uses the same `load_model(..., phase="eval")` checkpoint
loader and `Engine` generation path as `scripts.chat_cli`. Start it from the
repository root with a local checkpoint and tokenizer installed under
`$JARVISNT_BASE_DIR`:

```bash
uv run --extra cpu python -m scripts.serve_chat \
  --source custom --model-tag d24 --step 100 --device-type cpu
```

It listens on `http://127.0.0.1:8000`. Send a new message with optional
completed conversation history:

```bash
curl http://127.0.0.1:8000/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"What did I ask before?","history":[{"role":"user","content":"Remember this: the answer is 42."},{"role":"assistant","content":"Got it. I will remember that the answer is 42."}]}'
```

The response is JSON in the form `{"response":"..."}`. History must contain
alternating user and assistant messages, beginning with a user message. Set
`JARVISNT_INFERENCE_API_KEY` in the server environment to require
`Authorization: Bearer <key>`; do not put the key in a client-side app or source
file. The API is bound to localhost by default and is intended for local use.

## RunPod Serverless worker

The repository root contains a `Dockerfile` for RunPod's **Deploy from a
GitHub repository** flow. The worker loads the custom SFT `d24` checkpoint at
step `100` once per worker process, then reuses the same model, tokenizer, and
`Engine` for requests. It does not run the interactive CLI.

Keep model files outside Git and the Docker image. At worker startup,
`huggingface_hub.snapshot_download` fetches the private
`Riseikou1/jarvisnt-custom-sft` repository with the `HF_TOKEN` environment
secret directly into `JARVISNT_BASE_DIR`. The Hub repository uses the layout
expected by `load_model`:

```text
$JARVISNT_BASE_DIR/
  tokenizer/
  customsft_checkpoints/
    d24/
      model_000100.pt
      meta_000100.json
```

The repository also contains `tokenizer/token_bytes.pt`; `load_model` uses
`tokenizer/tokenizer.pkl`. Set `HF_TOKEN` as a RunPod secret with read access
to the private model repo. Never put it in the repository, Docker build
arguments, or request payload. The Docker image contains only code and
dependencies. The default artifact directory is `/runpod-volume/jarvisnt`; you
can mount a persistent volume there and set `JARVISNT_BASE_DIR` to preserve the
download cache across worker restarts. `.dockerignore` excludes local model,
tokenizer, dataset, and secret files. The checkpoint download is about 4.2 GiB,
so allow enough free volume space and startup time.

Set `JARVISNT_DEVICE_TYPE=cpu` to test on CPU, or `auto` (the default) to use
CUDA when available and CPU otherwise. The same image and inference code can
therefore be used when switching the endpoint to a GPU worker. You can tune
the worker generation ceiling with `JARVISNT_MAX_NEW_TOKENS` (default 512).

The RunPod job input uses ordered chat messages. Include the existing system
prompt as the first message when your application supplies one; the final
message must be the current user turn:

```json
{
  "input": {
    "messages": [
      {"role": "user", "content": "Remember 42."},
      {"role": "assistant", "content": "I will remember 42."},
      {"role": "user", "content": "What number did I mention?"}
    ],
    "temperature": 0.6,
    "top_k": 50,
    "max_tokens": 256
  }
}
```

The response is `{"response":"..."}`. Any supplied system prompt is retained,
only the newest three complete user/assistant history exchanges are sent to the model,
and the current user message is always included. Assistant-end tokens are
omitted from the response.

Run the focused worker tests locally:

```bash
uv run --extra cpu --group dev python -m pytest tests/test_runpod_worker.py tests/test_chat_context.py tests/test_serve_chat.py -q
```

You can verify the Docker build locally (the model weights are downloaded only
when a worker starts):

```bash
docker build -t jarvisnt-runpod-worker .
```

To test against the real private checkpoint without starting a RunPod worker,
set `HF_TOKEN` in your local environment and run:

```bash
JARVISNT_BASE_DIR=/path/to/jarvisnt-cache JARVISNT_DEVICE_TYPE=cpu \
uv run --extra cpu python - <<'PY'
from runpod_worker.handler import handler, initialize_worker

initialize_worker()
job = {"input": {"messages": [{"role": "user", "content": "Say hello briefly."}]}}
print(handler(job))
PY
```

This downloads the model files into the configured local cache on first run.

For RunPod's GitHub flow, create a Serverless endpoint from this repository
with the repository root as the build context, so it detects the root
`Dockerfile`. Add `HF_TOKEN` as a secret and set `JARVISNT_DEVICE_TYPE` to
`auto` (or `cpu` for CPU testing). Set `JARVISNT_BASE_DIR` if the worker's
model cache is mounted at a different path. Then let RunPod build and start
the endpoint. This repository change does not create or start it.

## Web interface

The site in `web/` documents the project and its current status. It deliberately does not expose a chat button while no trained model endpoint exists.

```bash
cd web
npm install
npm run dev
```

Then open `http://localhost:3000`.

## Project structure

```text
jarvisnt/       Python package: model, tokenizer, data, checkpoints, and inference
scripts/        Training, evaluation, tokenizer, and CLI entry points
tasks/          Evaluation task adapters
runs/           Reference launch recipes
tests/          Inexpensive unit and behavior tests
sft_dataset/    Local bootstrap supervised fine-tuning corpus
dev/            Analysis and data-preparation references
web/            Project website
```

## Acknowledgements

Jarvisn't is built on top of [nanochat](https://github.com/karpathy/nanochat), an open-source language-model training project by [Andrej Karpathy](https://github.com/karpathy). The repository intentionally preserves upstream implementation references, dataset links, and attribution where they explain the technical foundation.

Important dependencies and related projects include [PyTorch](https://pytorch.org/), [RustBPE](https://github.com/karpathy/rustbpe), [FlashAttention](https://github.com/Dao-AILab/flash-attention), and [Next.js](https://nextjs.org/).

## License

No root project license file is currently included. Add an explicit license before distributing Jarvisn't as a separately licensed project. Upstream and third-party attribution must remain intact.
