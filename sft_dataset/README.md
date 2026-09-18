# Jarvisn't SFT data

This directory contains two different kinds of local data. They are intentionally kept separate because throwing every synthetic example into one training mixture is how a clean experiment becomes soup.

## Default Jarvisn't-specific SFT data

These files are wired into `scripts/chat_sft.py`:

- `identity.jsonl` — **96 curated conversations** about Jarvisn't's name, creator, provenance, project scope, capabilities, limitations, and relationship to nanochat.
- `personality.jsonl` — **147 curated conversations** that demonstrate the desired response style: direct, technical, concise, mildly witty, willing to correct the user, and willing to admit uncertainty.

The default SFT recipe oversamples them using:

```text
identity:    x8
personality: x4
```

The factors are configurable:

```bash
python -m scripts.chat_sft --identity-epochs 8 --personality-epochs 4
```

Do not run that command without a compatible pretrained checkpoint. It performs real SFT.

## Bootstrap / experimental corpus

The older files remain available:

- `train.jsonl` — 1,188 examples
- `valid.jsonl` — 66 examples
- `test.jsonl` — 66 examples

They contain math, logic, Python, CS, AI/ML, formatting, reliability, and safety examples.

They are **not included in the default Jarvisn't SFT mixture**.

Why? The current training recipe already has large general datasets:

- SmolTalk for conversation
- MMLU for broad knowledge / multiple choice
- GSM8K for math and tool-style reasoning

The bootstrap corpus is useful for loader tests, experiments, and targeted ablations, but its heavily templated arithmetic examples do not deserve automatic training weight merely because they exist.

## Record format

Local records use JSONL, one JSON object per line:

```json
{
  "id": "jarvisnt-id-001",
  "messages": [
    {"role": "user", "content": "Who are you?"},
    {"role": "assistant", "content": "I'm Jarvisn't, a small language model project created by Temuujin."}
  ],
  "category": "identity",
  "difficulty": "easy",
  "tags": ["identity", "name"],
  "source": "jarvisnt_curated",
  "license": "CC0-1.0"
}
```

An optional system message is allowed before the user/assistant turns.

## Validate locally

From the repository root:

```bash
python sft_dataset/validate.py \
  sft_dataset/identity.jsonl \
  sft_dataset/personality.jsonl
```

To validate all local files:

```bash
cd sft_dataset
python validate.py
```

## Identity principles

Identity examples teach stable project facts without inventing run-specific metadata:

- name: Jarvisn't
- creator/maintainer: Temuujin
- technical foundation: Andrej Karpathy's nanochat
- project goal: an end-to-end small language-model project rather than a commercial API wrapper

Exact parameter count, GPU hardware, benchmark scores, and checkpoint details are deliberately **not hard-coded**, because those can change between runs.

## Personality principles

Personality is taught through the answers themselves, not through repetitive declarations such as "I am sarcastic."

The intended behavior is:

- technically competent
- direct and compact by default
- willing to challenge incorrect assumptions
- mildly humorous when it does not get in the way
- explicit about uncertainty
- never pretending to have executed code or verified facts when it has not

## License

The original/curated dataset content in this directory is released as CC0-1.0.
