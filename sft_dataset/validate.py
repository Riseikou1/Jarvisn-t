import json
import re
import sys
from pathlib import Path


REQUIRED_FIELDS = {"id", "messages"}
SUSPICIOUS_STANDALONE = re.compile(
    r"^(again|wrong|what now|why|how|really\??|same|me too|paper|rock|"
    r"another one|I regret it|I already did|it went badly|it went great|"
    r"they said yes)$",
    re.IGNORECASE,
)


def validate_messages(messages, path, line_no):
    prefix = f"{path}:{line_no}"
    assert isinstance(messages, list) and messages, f"{prefix} messages must be a non-empty list"
    assert len(messages) >= 2, f"{prefix} expected at least user + assistant"
    assert len(messages) % 2 == 0, f"{prefix} conversation must end with an assistant response"
    for i, message in enumerate(messages):
        assert isinstance(message, dict), f"{prefix} each message must be an object"
        expected_role = "user" if i % 2 == 0 else "assistant"
        assert message.get("role") == expected_role, (
            f"{prefix} expected role {expected_role!r}, got {message.get('role')!r}"
        )
        content = message.get("content")
        assert isinstance(content, str) and content.strip(), f"{prefix} empty message content"


def validate(path):
    ids = set()
    records = set()
    warnings = []
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
            fingerprint = json.dumps(obj["messages"], sort_keys=True, ensure_ascii=False)
            assert fingerprint not in records, f"duplicate conversation record: {obj['id']}"
            records.add(fingerprint)
            first_user = obj["messages"][0]["content"].strip()
            if len(obj["messages"]) == 2 and SUSPICIOUS_STANDALONE.fullmatch(first_user):
                warnings.append(f"{path}:{line_no} suspicious standalone prompt: {first_user!r}")
            count += 1
    for warning in warnings:
        print("warning:", warning, file=sys.stderr)
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
