#!/usr/bin/env bash
set -Eeuo pipefail

# Specialize the chat checkpoint produced by runs/speedrun.sh using only
# sft_dataset/identity.jsonl and sft_dataset/personality.jsonl.
#
# Usage:
#   bash runs/speedrun.sh
#   bash runs/custom_sft.sh
#
# Override defaults, for example:
#   NPROC_PER_NODE=4 CUSTOM_SFT_STEPS=500 bash runs/custom_sft.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export JARVISNT_BASE_DIR="${JARVISNT_BASE_DIR:-$HOME/.cache/jarvisnt}"
export WANDB_RUN="${WANDB_RUN:-jarvisnt-custom-sft}"

MODEL_SOURCE="${MODEL_SOURCE:-sft}"
MODEL_TAG="${MODEL_TAG:-d24}"
MODEL_STEP_ARG=()
if [[ -n "${MODEL_STEP:-}" ]]; then
  MODEL_STEP_ARG=("--model-step=${MODEL_STEP}")
fi

NPROC_PER_NODE="${NPROC_PER_NODE:-8}"
CUSTOM_SFT_STEPS="${CUSTOM_SFT_STEPS:-1000}"
IDENTITY_EPOCHS="${IDENTITY_EPOCHS:-8}"
PERSONALITY_EPOCHS="${PERSONALITY_EPOCHS:-4}"
DEVICE_BATCH_SIZE="${DEVICE_BATCH_SIZE:-16}"

case "$MODEL_SOURCE" in
  base) CHECKPOINT_DIR="$JARVISNT_BASE_DIR/base_checkpoints/$MODEL_TAG" ;;
  sft) CHECKPOINT_DIR="$JARVISNT_BASE_DIR/chatsft_checkpoints/$MODEL_TAG" ;;
  *) echo "ERROR: MODEL_SOURCE must be base or sft" >&2; exit 2 ;;
esac

if [[ ! -f "$JARVISNT_BASE_DIR/tokenizer/tokenizer.pkl" ]]; then
  echo "ERROR: tokenizer not found at $JARVISNT_BASE_DIR/tokenizer/tokenizer.pkl" >&2
  echo "Run runs/speedrun.sh first, or set JARVISNT_BASE_DIR to the trained cache." >&2
  exit 1
fi
if [[ ! -d "$CHECKPOINT_DIR" ]] || ! compgen -G "$CHECKPOINT_DIR/model_*.pt" > /dev/null; then
  echo "ERROR: no $MODEL_SOURCE checkpoint found at $CHECKPOINT_DIR" >&2
  echo "Run runs/speedrun.sh first, or set MODEL_SOURCE, MODEL_TAG, and MODEL_STEP." >&2
  exit 1
fi

command -v uv >/dev/null 2>&1 || {
  echo "ERROR: uv is required. Install it from https://docs.astral.sh/uv/" >&2
  exit 1
}
[[ -x .venv/bin/python ]] || uv venv
uv sync --extra gpu
source .venv/bin/activate

echo "Starting custom SFT"
echo "  source:       $MODEL_SOURCE"
echo "  model tag:    $MODEL_TAG"
echo "  base dir:     $JARVISNT_BASE_DIR"
echo "  steps:        $CUSTOM_SFT_STEPS"
echo "  identity:     x$IDENTITY_EPOCHS"
echo "  personality:  x$PERSONALITY_EPOCHS"
echo "  processes:    $NPROC_PER_NODE"

torchrun --standalone --nproc_per_node="$NPROC_PER_NODE" -m scripts.custom_sft -- \
  --source="$MODEL_SOURCE" \
  --model-tag="$MODEL_TAG" \
  "${MODEL_STEP_ARG[@]}" \
  --run="$WANDB_RUN" \
  --num-iterations="$CUSTOM_SFT_STEPS" \
  --device-batch-size="$DEVICE_BATCH_SIZE" \
  --identity-epochs="$IDENTITY_EPOCHS" \
  --personality-epochs="$PERSONALITY_EPOCHS"

echo
echo "Custom SFT complete. Checkpoint output:"
echo "  $JARVISNT_BASE_DIR/customsft_checkpoints/$MODEL_TAG"
