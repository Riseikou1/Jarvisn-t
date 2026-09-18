import json, sys
from pathlib import Path

def validate(path):
    ids = set()
    count = 0
    with open(path, encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            obj = json.loads(line)
            required = {"id","messages","category","difficulty","source","license"}
            missing = required - obj.keys()
            assert not missing, f"{path}:{line_no} missing {missing}"
            assert obj["id"] not in ids, f"duplicate id: {obj['id']}"
            ids.add(obj["id"])
            msgs = obj["messages"]
            assert len(msgs) == 3, f"{path}:{line_no} expected 3 messages"
            assert [m["role"] for m in msgs] == ["system","user","assistant"]
            assert all(isinstance(m["content"], str) and m["content"].strip() for m in msgs)
            count += 1
    return count

if __name__ == "__main__":
    paths = [Path(p) for p in sys.argv[1:]] or [Path("train.jsonl"), Path("valid.jsonl"), Path("test.jsonl")]
    total = 0
    for p in paths:
        c = validate(p)
        print(f"{p}: {c} valid examples")
        total += c
    print("total:", total)
