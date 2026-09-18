# Jarvisn't SFT v0.1

A bootstrap supervised fine-tuning dataset for an instruction-following assistant.

## What this is

- 1,320 original/synthetic chat examples
- JSONL, one example per line
- 90/5/5 train/validation/test split
- Categories include math, logic, Python, CS, AI/ML, strict formatting, reliability, and safety
- Each sample includes provenance metadata and a license field

## What this is NOT

This is **not** a foundation-model pretraining corpus. It is too small for training a GPT-style language model from scratch.
Use it for:
- supervised fine-tuning (SFT)
- pipeline testing
- tokenizer/data-loader testing
- early behavior shaping
- evaluating your training loop

## Record format

```json
{
  "id": "jv-00001",
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "category": "coding",
  "difficulty": "medium",
  "tags": ["python"],
  "source": "synthetic_original",
  "license": "CC0-1.0"
}
```

## Split sizes

- train: 1,188
- valid: 66
- test: 66

## Important quality note

This dataset is intentionally a **clean bootstrap set**, not a giant synthetic dump.
For a serious Jarvisn't model, the next useful version should add:
1. more linguistic diversity,
2. longer multi-turn conversations,
3. harder code and reasoning samples,
4. domain-specific AI/CS data,
5. verified public-domain / permissively licensed text for continued pretraining,
6. preference pairs for DPO or another preference-training stage.

Repeated templates are present on purpose to make the first version deterministic and verifiable.
Do not confuse example count with model quality. Humanity has already tried that strategy.

## License

Dataset content in this package is released as CC0-1.0.
