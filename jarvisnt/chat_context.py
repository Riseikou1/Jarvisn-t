"""Small helpers for keeping inference context bounded by chat messages."""


MAX_HISTORY_EXCHANGES = 3


def assemble_chat_messages(history, current_user_message, system_prompt=None):
    """Keep the newest complete user/assistant exchanges and current user turn."""
    messages = []
    if system_prompt is not None:
        messages.append({"role": "system", "content": system_prompt})
    messages.extend(history[-2 * MAX_HISTORY_EXCHANGES:])
    messages.append({"role": "user", "content": current_user_message})
    return messages


def trim_tokenized_chat_history(tokens, user_start, user_end, assistant_start,
                                assistant_end, keep_exchanges=MAX_HISTORY_EXCHANGES):
    """Keep a token prompt's prefix and newest complete user/assistant pairs.

    The CLI calls this before adding the current user message. The prefix (BOS
    and any future system prompt tokens) is intact.
    """
    markers = {user_start: user_end, assistant_start: assistant_end}
    first_message = next(
        (i for i, token in enumerate(tokens) if token in markers), len(tokens)
    )
    prefix = tokens[:first_message]
    messages = []
    i = first_message
    while i < len(tokens):
        start = tokens[i]
        if start not in markers:
            i += 1
            continue
        end = markers[start]
        try:
            end_index = tokens.index(end, i + 1)
        except ValueError:
            # Preserve an incomplete trailing message rather than discarding
            # user input if generation was interrupted.
            messages.append(tokens[i:])
            break
        messages.append(tokens[i:end_index + 1])
        i = end_index + 1
    complete_pairs = []
    for index in range(0, len(messages) - 1, 2):
        if (messages[index][0] == user_start
                and messages[index + 1][0] == assistant_start):
            complete_pairs.append(messages[index:index + 2])
    kept = complete_pairs[-keep_exchanges:]
    return prefix + [token for pair in kept for message in pair for token in message]
