"""Local HTTP inference API for Jarvisn't chat checkpoints.

Run with ``python -m scripts.serve_chat \
    --source sft \
    --model-tag d24 \
    --step 467 \
    --device-type cpu``.
Set ``JARVISNT_INFERENCE_API_KEY`` to require
Bearer authentication; the key is read only from the server environment.
"""

import argparse
import json
import math
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from jarvisnt.checkpoint_manager import load_model
from jarvisnt.chat_context import assemble_chat_messages
from jarvisnt.common import autodetect_device_type, compute_cleanup, compute_init
from jarvisnt.engine import Engine


def parse_args():
    parser = argparse.ArgumentParser(description="Serve Jarvisn't chat inference over HTTP")
    parser.add_argument("--source", choices=["sft", "custom", "rl"], default="sft")
    parser.add_argument("--model-tag", default=None)
    parser.add_argument("--step", type=int, default=None)
    parser.add_argument("--device-type", choices=["cuda", "cpu", "mps"], default="")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--max-new-tokens", type=int, default=512)
    return parser.parse_args()


class InferenceService:
    def __init__(self, engine, tokenizer, max_new_tokens=512):
        self.engine = engine
        self.tokenizer = tokenizer
        self.max_new_tokens = max_new_tokens
        self.bos = tokenizer.get_bos_token_id()
        self.assistant_end = tokenizer.encode_special("<|assistant_end|>")

    def reply(self, message, history=None, temperature=0.6, top_k=50, max_tokens=256):
        if not isinstance(message, str) or not message.strip():
            raise ValueError("message must be a non-empty string")
        if len(message) > 16_000:
            raise ValueError("message is too long (maximum 16000 characters)")
        if history is None:
            history = []
        if not isinstance(history, list) or len(history) > 31:
            raise ValueError("history must be a list with at most 30 chat messages and an optional system message")

        chat_history = []
        system_prompt = None
        for index, item in enumerate(history):
            if not isinstance(item, dict):
                raise ValueError(f"history[{index}] must be an object")
            role, content = item.get("role"), item.get("content")
            if role == "system" and index == 0:
                if not isinstance(content, str) or not content.strip():
                    raise ValueError("history[0].content must be a non-empty system prompt")
                system_prompt = content
                continue
            if role not in {"user", "assistant"}:
                raise ValueError(f"history[{index}].role must be 'user' or 'assistant' (system is allowed only first)")
            if not isinstance(content, str) or not content.strip():
                raise ValueError(f"history[{index}].content must be a non-empty string")
            if len(content) > 16_000:
                raise ValueError(f"history[{index}].content is too long")
            chat_history.append({"role": role, "content": content})

        # Histories are complete user/assistant pairs; the new message is the
        # next user turn. This mirrors the CLI's accumulated conversation.
        if len(chat_history) % 2 or any(
            item["role"] != ("user" if i % 2 == 0 else "assistant")
            for i, item in enumerate(chat_history)
        ):
            raise ValueError("history must contain alternating user and assistant messages, starting with user")

        if isinstance(temperature, bool) or not isinstance(temperature, (int, float)) or not math.isfinite(temperature) or not 0 <= temperature <= 2:
            raise ValueError("temperature must be a number between 0 and 2")
        if isinstance(top_k, bool) or not isinstance(top_k, int) or not 0 <= top_k <= 4096:
            raise ValueError("top_k must be an integer between 0 and 4096")
        if isinstance(max_tokens, bool) or not isinstance(max_tokens, int) or not 1 <= max_tokens <= self.max_new_tokens:
            raise ValueError(f"max_tokens must be an integer between 1 and {self.max_new_tokens}")

        messages = assemble_chat_messages(chat_history, message, system_prompt)
        conversation = {"messages": messages + [{"role": "assistant", "content": ""}]}
        prompt_tokens = self.tokenizer.render_for_completion(conversation)
        results, _masks = self.engine.generate_batch(
            prompt_tokens,
            num_samples=1,
            max_tokens=max_tokens,
            temperature=max(0.01, temperature),
            top_k=None if top_k == 0 else top_k,
        )
        generated = results[0][len(prompt_tokens):]
        # Defense in depth in case a generator implementation returns the
        # completion marker; decode only user-facing response tokens.
        generated = [token for token in generated if token != self.assistant_end and token != self.bos]
        return self.tokenizer.decode(generated).replace("<|assistant_end|>", "").strip()


def make_handler(service, api_key=None):
    class ChatHandler(BaseHTTPRequestHandler):
        def _send(self, status, payload):
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/health":
                self._send(200, {"ok": True})
            else:
                self._send(404, {"error": "not found"})

        def do_POST(self):
            if self.path != "/v1/chat":
                self._send(404, {"error": "not found"})
                return
            if api_key and self.headers.get("Authorization") != f"Bearer {api_key}":
                self._send(401, {"error": "unauthorized"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > 64_000:
                    raise ValueError("request body must be between 1 and 64000 bytes")
                payload = json.loads(self.rfile.read(length))
                if not isinstance(payload, dict):
                    raise ValueError("JSON body must be an object")
                reply = service.reply(
                    message=payload.get("message"),
                    history=payload.get("history"),
                    temperature=payload.get("temperature", 0.6),
                    top_k=payload.get("top_k", 50),
                    max_tokens=payload.get("max_tokens", min(256, service.max_new_tokens)),
                )
                self._send(200, {"response": reply})
            except (ValueError, TypeError, json.JSONDecodeError) as exc:
                self._send(400, {"error": str(exc)})
            except Exception:
                # Keep internal checkpoint/runtime details out of API responses.
                self._send(500, {"error": "inference failed"})

        def log_message(self, _format, *_args):
            return

    return ChatHandler


def main():
    args = parse_args()
    if args.port < 1 or args.port > 65535 or args.max_new_tokens < 1:
        raise SystemExit("port and max-new-tokens must be positive valid values")
    device_type = autodetect_device_type() if args.device_type == "" else args.device_type
    _ddp, _rank, _local_rank, _world_size, device = compute_init(device_type)
    try:
        model, tokenizer, _meta = load_model(
            args.source, device, phase="eval", model_tag=args.model_tag, step=args.step
        )
        service = InferenceService(Engine(model, tokenizer), tokenizer, args.max_new_tokens)
        server = ThreadingHTTPServer(
            (args.host, args.port),
            make_handler(service, os.environ.get("JARVISNT_INFERENCE_API_KEY")),
        )
        print(f"Jarvisn't inference API listening on http://{args.host}:{args.port}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
    finally:
        compute_cleanup()


if __name__ == "__main__":
    main()
