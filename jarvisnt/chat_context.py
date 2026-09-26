"""Small helpers for keeping inference context bounded by chat messages."""


MAX_HISTORY_MESSAGES = 3


def assemble_chat_messages(history, current_user_message, system_prompt=None):
    """Keep the newest chat history messages and append the current user turn."""
    messages = []
    if system_prompt is not None:
        messages.append({"role": "system", "content": system_prompt})
    messages.extend(history[-MAX_HISTORY_MESSAGES:])
    messages.append({"role": "user", "content": current_user_message})
    return messages


def trim_tokenized_chat_history(tokens, user_start, user_end, assistant_start,
                                assistant_end, keep_messages=MAX_HISTORY_MESSAGES):
    """Keep a token prompt's prefix and newest complete chat messages.

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
    return prefix + [token for message in messages[-keep_messages:] for token in message]
