import json

import pytest

from tasks.local_jsonl import LocalJSONL


def write_jsonl(path, rows):
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def test_local_jsonl_loads_conversations(tmp_path):
    path = tmp_path / "tiny.jsonl"
    write_jsonl(path, [
        {
            "id": "a",
            "messages": [
                {"role": "user", "content": "Who are you?"},
                {"role": "assistant", "content": "I'm Jarvisn't."},
            ],
        },
        {
            "id": "b",
            "messages": [
                {"role": "system", "content": "Be concise."},
                {"role": "user", "content": "2+2?"},
                {"role": "assistant", "content": "4"},
            ],
        },
    ])
    task = LocalJSONL(path)
    assert len(task) == 2
    assert task[0]["messages"][1]["content"] == "I'm Jarvisn't."
    assert task[1]["messages"][0]["role"] == "system"


def test_local_jsonl_rejects_bad_role_order(tmp_path):
    path = tmp_path / "bad.jsonl"
    write_jsonl(path, [{
        "messages": [
            {"role": "assistant", "content": "wrong first role"},
            {"role": "user", "content": "wrong second role"},
        ]
    }])
    with pytest.raises(ValueError, match="expected role"):
        LocalJSONL(path)


def test_local_jsonl_rejects_duplicate_ids(tmp_path):
    path = tmp_path / "dupe.jsonl"
    row = {
        "id": "same",
        "messages": [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"},
        ],
    }
    write_jsonl(path, [row, row])
    with pytest.raises(ValueError, match="duplicate id"):
        LocalJSONL(path)
