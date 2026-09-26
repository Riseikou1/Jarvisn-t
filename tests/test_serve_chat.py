import pytest

from scripts.serve_chat import InferenceService


class FakeTokenizer:
    def get_bos_token_id(self):
        return 99

    def encode_special(self, token):
        assert token == "<|assistant_end|>"
        return 98

    def render_for_completion(self, conversation):
        self.last_conversation = conversation
        return [1, 2]

    def decode(self, tokens):
        return "hello<|assistant_end|>" if tokens else ""


class FakeEngine:
    def generate_batch(self, prompt_tokens, **kwargs):
        assert prompt_tokens == [1, 2]
        return [[1, 2, 7, 98, 99]], [[]]


def test_reply_uses_history_and_strips_terminal_token():
    tokenizer = FakeTokenizer()
    service = InferenceService(FakeEngine(), tokenizer, max_new_tokens=64)
    reply = service.reply(
        "What did I say?",
        history=[
            {"role": "user", "content": "Remember 42."},
            {"role": "assistant", "content": "I will remember 42."},
        ],
        max_tokens=16,
    )

    assert reply == "hello"
    assert tokenizer.last_conversation["messages"][-2:] == [
        {"role": "user", "content": "What did I say?"},
        {"role": "assistant", "content": ""},
    ]


def test_reply_keeps_only_latest_three_history_messages_and_current_message():
    tokenizer = FakeTokenizer()
    service = InferenceService(FakeEngine(), tokenizer, max_new_tokens=64)
    history = [
        {"role": "user", "content": "old question"},
        {"role": "assistant", "content": "old answer"},
        {"role": "user", "content": "recent question 1"},
        {"role": "assistant", "content": "recent answer 1"},
        {"role": "user", "content": "recent question 2"},
        {"role": "assistant", "content": "recent answer 2"},
    ]
    service.reply(
        "current question", history=history, max_tokens=16
    )

    messages = tokenizer.last_conversation["messages"]
    assert messages == [
        {"role": "assistant", "content": "recent answer 1"},
        {"role": "user", "content": "recent question 2"},
        {"role": "assistant", "content": "recent answer 2"},
        {"role": "user", "content": "current question"},
        {"role": "assistant", "content": ""},
    ]


def test_reply_keeps_system_prompt_separate_from_history_window():
    tokenizer = FakeTokenizer()
    service = InferenceService(FakeEngine(), tokenizer, max_new_tokens=64)
    service.reply(
        "current", history=[
            {"role": "system", "content": "Keep this prompt."},
            {"role": "user", "content": "one"},
            {"role": "assistant", "content": "two"},
        ], max_tokens=16,
    )
    assert tokenizer.last_conversation["messages"][0] == {
        "role": "system", "content": "Keep this prompt."
    }
    assert tokenizer.last_conversation["messages"][-2] == {
        "role": "user", "content": "current"
    }


@pytest.mark.parametrize("message,history", [
    ("", None),
    ("hello", [{"role": "assistant", "content": "out of order"}]),
])
def test_reply_rejects_invalid_request(message, history):
    service = InferenceService(FakeEngine(), FakeTokenizer())
    with pytest.raises(ValueError):
        service.reply(message, history=history)
