from jarvisnt.chat_context import trim_tokenized_chat_history


def test_cli_context_keeps_three_latest_complete_exchanges_and_prefix():
    bos = 0
    user_start, user_end = 10, 11
    assistant_start, assistant_end = 12, 13
    tokens = [
        bos,
        user_start, 20, user_end,
        assistant_start, 21, assistant_end,
        user_start, 22, user_end,
        assistant_start, 23, assistant_end,
        user_start, 24, user_end,
        assistant_start, 25, assistant_end,
        user_start, 26, user_end,
        assistant_start, 27, assistant_end,
    ]

    kept = trim_tokenized_chat_history(
        tokens, user_start, user_end, assistant_start, assistant_end,
        keep_exchanges=3,
    )

    assert kept == [
        bos,
        user_start, 22, user_end,
        assistant_start, 23, assistant_end,
        user_start, 24, user_end,
        assistant_start, 25, assistant_end,
        user_start, 26, user_end,
        assistant_start, 27, assistant_end,
    ]
