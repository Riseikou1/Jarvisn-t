import json
import sys
from pathlib import Path


REQUIRED_FIELDS = {"id", "messages", "category", "difficulty", "source", "license"}


def validate_messages(messages, path, line_no):
    prefix = f"{path}:{line_no}"
    assert isinstance(messages, list), f"{prefix} messages must be a list"
    assert len(messages) >= 2, f"{prefix} expected at least user + assistant"

    start = 0
    if messages[0].get("role") == "system":
        start = 1
        content = messages[0].get("content")
        assert isinstance(content, str) and content.strip(), f"{prefix} empty system content"

    rest = messages[start:]
    assert len(rest) >= 2 and len(rest) % 2 == 0, (
        f"{prefix} messages after optional system must be user/assistant pairs"
    )
    for i, message in enumerate(rest):
        expected_role = "user" if i % 2 == 0 else "assistant"
        assert message.get("role") == expected_role, (
            f"{prefix} expected role {expected_role!r}, got {message.get('role')!r}"
        )
        content = message.get("content")
        assert isinstance(content, str) and content.strip(), f"{prefix} empty message content"


def validate(path):
    ids = set()
    count = 0
    with open(path, encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            obj = json.loads(line)
            missing = REQUIRED_FIELDS - obj.keys()
            assert not missing, f"{path}:{line_no} missing {missing}"
            assert obj["id"] not in ids, f"duplicate id: {obj['id']}"
            ids.add(obj["id"])
            validate_messages(obj["messages"], path, line_no)
            count += 1
    return count


if __name__ == "__main__":
    paths = [Path(p) for p in sys.argv[1:]] or [
        Path("train.jsonl"),
        Path("valid.jsonl"),
        Path("test.jsonl"),
        Path("identity.jsonl"),
        Path("personality.jsonl"),
    ]
    total = 0
    for p in paths:
        c = validate(p)
        print(f"{p}: {c} valid examples")
        total += c
    print("total:", total)
