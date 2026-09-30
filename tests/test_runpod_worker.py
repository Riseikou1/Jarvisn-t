import pytest

from runpod_worker import handler as worker
from scripts.serve_chat import InferenceService


class FakeTokenizer:
    def get_bos_token_id(self):
        return 99

    def encode_special(self, token):
        assert token == "<|assistant_end|>"
        return 98

    def render_for_completion(self, conversation):
        self.conversation = conversation
        return [1, 2]

    def decode(self, tokens):
        return "reply<|assistant_end|>" if tokens else ""


class FakeEngine:
    def generate_batch(self, prompt_tokens, **kwargs):
        return [[*prompt_tokens, 7, 98]], [[]]


@pytest.fixture
def fake_service(monkeypatch):
    tokenizer = FakeTokenizer()
    service = InferenceService(FakeEngine(), tokenizer, max_new_tokens=512)
    monkeypatch.setattr(worker, "SERVICE", service)
    monkeypatch.setattr(worker, "STARTUP_ERROR", None)
    return tokenizer


def test_worker_preserves_system_and_newest_three_complete_exchanges(fake_service):
    output = worker.handler({"input": {"messages": [
        {"role": "system", "content": "Keep this system prompt."},
        {"role": "user", "content": "exchange 1 question"},
        {"role": "assistant", "content": "exchange 1 answer"},
        {"role": "user", "content": "exchange 2 question"},
        {"role": "assistant", "content": "exchange 2 answer"},
        {"role": "user", "content": "exchange 3 question"},
        {"role": "assistant", "content": "exchange 3 answer"},
        {"role": "user", "content": "exchange 4 question"},
        {"role": "assistant", "content": "exchange 4 answer"},
        {"role": "user", "content": "current question"},
    ]}})

    assert output == {"response": "reply"}
    assert fake_service.conversation["messages"] == [
        {"role": "system", "content": "Keep this system prompt."},
        {"role": "user", "content": "exchange 2 question"},
        {"role": "assistant", "content": "exchange 2 answer"},
        {"role": "user", "content": "exchange 3 question"},
        {"role": "assistant", "content": "exchange 3 answer"},
        {"role": "user", "content": "exchange 4 question"},
        {"role": "assistant", "content": "exchange 4 answer"},
        {"role": "user", "content": "current question"},
        {"role": "assistant", "content": ""},
    ]


@pytest.mark.parametrize("job", [
    None,
    {},
    {"input": {"messages": []}},
    {"input": {"messages": [{"role": "assistant", "content": "no user turn"}]}},
    {"input": {"messages": [{"role": [], "content": "bad role"}]}},
])
def test_worker_rejects_invalid_input(job, fake_service):
    response = worker.handler(job)
    assert response["error"]["code"] == "invalid_input"


def test_worker_keeps_32_message_input_validation(fake_service):
    messages = []
    for index in range(16):
        messages.extend([
            {"role": "user", "content": f"question {index}"},
            {"role": "assistant", "content": f"answer {index}"},
        ])
    messages.append({"role": "user", "content": "current question"})
    response = worker.handler({"input": {"messages": messages}})
    assert response["error"] == {
        "code": "invalid_input",
        "message": "input.messages may contain at most 32 messages",
    }


def test_worker_reports_missing_artifacts(monkeypatch):
    monkeypatch.setattr(worker, "SERVICE", None)
    monkeypatch.setattr(worker, "STARTUP_ERROR", (
        "missing_artifacts", "Mount model artifacts."
    ))
    response = worker.handler({"input": {"messages": [
        {"role": "user", "content": "hello"}
    ]}})
    assert response["error"]["code"] == "missing_artifacts"


def test_initialization_classifies_missing_artifact_paths(monkeypatch):
    monkeypatch.setenv("JARVISNT_DEVICE_TYPE", "cpu")
    monkeypatch.setattr(worker, "download_model_artifacts", lambda: None)
    monkeypatch.setattr(worker, "compute_init", lambda _device: (False, 0, 0, 1, "cpu"))
    def missing_checkpoint(*_args, **_kwargs):
        raise FileNotFoundError
    monkeypatch.setattr(worker, "load_model", missing_checkpoint)
    monkeypatch.setattr(worker, "SERVICE", None)

    worker.initialize_worker()

    assert worker.STARTUP_ERROR[0] == "missing_artifacts"


def test_private_repo_download_uses_loader_layout_and_hf_token(tmp_path):
    seen = {}

    def fake_download(**kwargs):
        seen.update(kwargs)
        (tmp_path / "chatsft_checkpoints/d24").mkdir(parents=True)
        (tmp_path / "chatsft_checkpoints/d24/model_000467.pt").touch()
        (tmp_path / "chatsft_checkpoints/d24/meta_000467.json").touch()
        (tmp_path / "tokenizer").mkdir()
        (tmp_path / "tokenizer/tokenizer.pkl").touch()

    result = worker.download_model_artifacts(
        token="test-token", base_dir=tmp_path, download_fn=fake_download
    )

    assert result == tmp_path
    assert seen == {
        "repo_id": "Riseikou1/jarvisnt-chat-sft",
        "token": "test-token",
        "local_dir": str(tmp_path),
    }


def test_private_repo_download_requires_hf_token(monkeypatch, tmp_path):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    with pytest.raises(worker.HFTokenMissingError):
        worker.download_model_artifacts(base_dir=tmp_path, download_fn=lambda **_kwargs: None)


def test_worker_reports_generation_failure(monkeypatch):
    class BrokenService:
        def reply(self, *args, **kwargs):
            raise RuntimeError("private detail")

    monkeypatch.setattr(worker, "SERVICE", BrokenService())
    monkeypatch.setattr(worker, "STARTUP_ERROR", None)
    response = worker.handler({"input": {"messages": [
        {"role": "user", "content": "hello"}
    ]}})
    assert response == {"error": {
        "code": "generation_failed",
        "message": "Text generation failed. Check worker logs for details.",
    }}
    assert "private detail" not in str(response)
