"""
Local JSONL conversation datasets for Jarvisn't-specific SFT data.

Each non-empty line is a JSON object with a `messages` field. Metadata fields
such as `id`, `category`, `tags`, and `license` are preserved in the file
but are not required by the training loader.
"""

import json
from pathlib import Path

from tasks.common import Task


class LocalJSONL(Task):
    """Load a small repository-local JSONL conversation dataset."""

    def __init__(self, path, **kwargs):
        super().__init__(**kwargs)
        candidate = Path(path)
        if not candidate.is_absolute():
            repo_root = Path(__file__).resolve().parents[1]
            candidate = repo_root / candidate
        self.path = candidate.resolve()
        if not self.path.is_file():
            raise FileNotFoundError(f"Local SFT dataset not found: {self.path}")

        self.rows = []
        seen_ids = set()
        with self.path.open("r", encoding="utf-8") as f:
            for line_no, raw_line in enumerate(f, 1):
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{self.path}:{line_no}: invalid JSON") from exc

                record_id = row.get("id")
                if record_id is not None:
                    if record_id in seen_ids:
                        raise ValueError(f"{self.path}:{line_no}: duplicate id {record_id!r}")
                    seen_ids.add(record_id)

                messages = row.get("messages")
                self._validate_messages(messages, line_no)
                self.rows.append({"messages": messages})

        if not self.rows:
            raise ValueError(f"Local SFT dataset is empty: {self.path}")

    def _validate_messages(self, messages, line_no):
        prefix = f"{self.path}:{line_no}"
        if not isinstance(messages, list) or len(messages) < 2:
            raise ValueError(f"{prefix}: messages must contain at least user + assistant")

        start = 0
        if messages[0].get("role") == "system":
            if not isinstance(messages[0].get("content"), str) or not messages[0]["content"].strip():
                raise ValueError(f"{prefix}: system content must be a non-empty string")
            start = 1

        conversational = messages[start:]
        if len(conversational) < 2 or len(conversational) % 2 != 0:
            raise ValueError(f"{prefix}: messages after optional system must be user/assistant pairs")

        for i, message in enumerate(conversational):
            if not isinstance(message, dict):
                raise ValueError(f"{prefix}: each message must be an object")
            expected = "user" if i % 2 == 0 else "assistant"
            if message.get("role") != expected:
                raise ValueError(f"{prefix}: expected role {expected!r}, got {message.get('role')!r}")
            content = message.get("content")
            if not isinstance(content, str) or not content.strip():
                raise ValueError(f"{prefix}: message content must be a non-empty string")

    def num_examples(self):
        return len(self.rows)

    def get_example(self, index):
        return self.rows[index]
