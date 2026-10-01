"""RunPod Serverless worker for custom SFT checkpoint d24 at step 100."""

import os
import threading
from pathlib import Path

from huggingface_hub import snapshot_download
from jarvisnt.checkpoint_manager import load_model
from jarvisnt.common import autodetect_device_type, compute_init, get_base_dir
from jarvisnt.engine import Engine
from scripts.serve_chat import InferenceService


MODEL_SOURCE = os.environ.get("JARVISNT_MODEL_SOURCE", "sft")
MODEL_TAG = os.environ.get("JARVISNT_MODEL_TAG", "d24")
MODEL_STEP = int(os.environ.get("JARVISNT_MODEL_STEP", "467"))
HF_REPO_ID = os.environ.get(
    "JARVISNT_HF_REPO_ID",
    "Riseikou1/jarvisnt-chat-sft",
)

CHECKPOINT_DIRS = {
    "base": "base_checkpoints",
    "sft": "chatsft_checkpoints",
    "custom": "customsft_checkpoints",
    "rl": "chatrl_checkpoints",
}

CHECKPOINT_DIR = CHECKPOINT_DIRS[MODEL_SOURCE]

SERVICE = None
STARTUP_ERROR = None
INFERENCE_LOCK = threading.Lock()


class HFTokenMissingError(Exception):
    """Raised when a worker has no Hugging Face read token configured."""


def _error(code, message):
    return {"error": {"code": code, "message": message}}


def _validate_messages(messages):
    if not isinstance(messages, list) or not messages:
        raise ValueError("input.messages must be a non-empty array")
    if len(messages) > 32:
        raise ValueError("input.messages may contain at most 32 messages")

    validated = []
    for index, message in enumerate(messages):
        if not isinstance(message, dict):
            raise ValueError(f"input.messages[{index}] must be an object")
        role, content = message.get("role"), message.get("content")
        if not isinstance(role, str):
            raise ValueError(f"input.messages[{index}].role must be a string")
        if role not in {"system", "user", "assistant"}:
            raise ValueError(f"input.messages[{index}].role must be system, user, or assistant")
        if role == "system" and index != 0:
            raise ValueError("system prompt is allowed only as the first message")
        if not isinstance(content, str) or not content.strip():
            raise ValueError(f"input.messages[{index}].content must be a non-empty string")
        if len(content) > 16_000:
            raise ValueError(f"input.messages[{index}].content is too long (maximum 16000 characters)")
        validated.append({"role": role, "content": content})

    chat_messages = validated[1:] if validated[0]["role"] == "system" else validated
    if not chat_messages or chat_messages[-1]["role"] != "user":
        raise ValueError("input.messages must end with the current user message")
    if any(
        message["role"] != ("user" if index % 2 == 0 else "assistant")
        for index, message in enumerate(chat_messages)
    ):
        raise ValueError("chat messages must alternate user and assistant, starting with user")
    return validated


def download_model_artifacts(token=None, base_dir=None, download_fn=None):
    """Download the private model repo into the exact tree expected by load_model."""
    token = token if token is not None else os.environ.get("HF_TOKEN")
    if not token:
        raise HFTokenMissingError("HF_TOKEN is required to download the private model repository.")
    base_dir = Path(base_dir or get_base_dir())
    download_fn = download_fn or snapshot_download
    download_fn(repo_id=HF_REPO_ID, token=token, local_dir=str(base_dir))

    expected_files = [
        base_dir / CHECKPOINT_DIR / MODEL_TAG / f"model_{MODEL_STEP:06d}.pt",
        base_dir / CHECKPOINT_DIR / MODEL_TAG / f"meta_{MODEL_STEP:06d}.json",
        base_dir / "tokenizer" / "tokenizer.pkl",
    ]
    missing = [str(path.relative_to(base_dir)) for path in expected_files if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "Hugging Face repository is missing files required by load_model: "
            + ", ".join(missing)
        )
    return base_dir


def initialize_worker():
    """Download and load the configured checkpoint once for this worker."""
    global SERVICE, STARTUP_ERROR
    device_setting = os.environ.get("JARVISNT_DEVICE_TYPE", "auto").lower()
    if device_setting == "auto":
        device_type = autodetect_device_type()
    elif device_setting in {"cpu", "cuda", "mps"}:
        device_type = device_setting
    else:
        STARTUP_ERROR = ("worker_configuration_error", "JARVISNT_DEVICE_TYPE must be auto, cpu, cuda, or mps")
        return

    try:
        download_model_artifacts()
    except HFTokenMissingError as exc:
        STARTUP_ERROR = ("hf_token_required", str(exc))
        return
    except FileNotFoundError as exc:
        STARTUP_ERROR = ("missing_artifacts", str(exc))
        return
    except Exception:
        STARTUP_ERROR = (
            "artifact_download_failed",
            "Could not download the private Hugging Face model repository. Verify HF_TOKEN and repository access.",
        )
        print("Jarvisn't artifact download failed; check HF_TOKEN and repository access.")
        return

    try:
        _ddp, _rank, _local_rank, _world_size, device = compute_init(device_type)
        model, tokenizer, _meta = load_model(
            MODEL_SOURCE, device, phase="eval", model_tag=MODEL_TAG, step=MODEL_STEP
        )
        max_tokens = int(os.environ.get("JARVISNT_MAX_NEW_TOKENS", "512"))
        if max_tokens < 1:
            raise ValueError("JARVISNT_MAX_NEW_TOKENS must be positive")
        SERVICE = InferenceService(Engine(model, tokenizer), tokenizer, max_tokens)
        STARTUP_ERROR = None
        print(f"Loaded sft checkpoint {MODEL_TAG} step {MODEL_STEP} on {device_type}")
    except FileNotFoundError:
        STARTUP_ERROR = (
            "missing_artifacts",
            "Model artifacts are missing. Check JARVISNT_BASE_DIR and confirm the checkpoint and tokenizer are mounted.",
        )
    except Exception:
        # Keep details in server logs only; never echo environment values or
        # request data back to callers.
        STARTUP_ERROR = ("worker_initialization_failed", "The model worker could not initialize.")
        print("Jarvisn't worker initialization failed; verify model artifacts and device configuration.")


def handler(job):
    """RunPod job handler: input.messages contains ordered chat messages."""
    if not isinstance(job, dict):
        return _error("invalid_input", "job must be a JSON object")
    payload = job.get("input")
    if not isinstance(payload, dict):
        return _error("invalid_input", "job.input must be a JSON object")
    try:
        messages = _validate_messages(payload.get("messages"))
        temperature = payload.get("temperature", 0.6)
        top_k = payload.get("top_k", 50)
        max_tokens = payload.get("max_tokens", 256)
        if isinstance(temperature, bool) or not isinstance(temperature, (int, float)):
            raise ValueError("input.temperature must be a number")
        if isinstance(top_k, bool) or not isinstance(top_k, int):
            raise ValueError("input.top_k must be an integer")
        if isinstance(max_tokens, bool) or not isinstance(max_tokens, int):
            raise ValueError("input.max_tokens must be an integer")
    except (ValueError, TypeError) as exc:
        return _error("invalid_input", str(exc))

    return {"response": "ok"}  # need to delete this shit.

    if SERVICE is None:
        if STARTUP_ERROR:
            return _error(*STARTUP_ERROR)
        return _error("worker_not_initialized", "The model worker is not initialized.")

    system_message = messages[:1] if messages[0]["role"] == "system" else []
    chat_messages = messages[len(system_message):]
    current_message = chat_messages[-1]["content"]
    history = system_message + chat_messages[:-1]
    try:
        # Reuse one loaded Engine safely across concurrent worker jobs.
        with INFERENCE_LOCK:
            response = SERVICE.reply(
                current_message,
                history=history,
                temperature=temperature,
                top_k=top_k,
                max_tokens=max_tokens,
            )
        return {"response": response.replace("<|assistant_end|>", "").strip()}
    except ValueError as exc:
        return _error("invalid_input", str(exc))
    except Exception:
        return _error("generation_failed", "Text generation failed. Check worker logs for details.")


def main():
    initialize_worker()
    import runpod

    runpod.serverless.start({"handler": handler})


if __name__ == "__main__":
    main()
