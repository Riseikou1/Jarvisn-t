"""Minimal HTTP inference service for a trained Jarvisn't chat checkpoint.

This process owns the PyTorch model. Deploy it on a machine with the model
checkpoint and tokenizer, then point the Vercel app's
JARVISNT_INFERENCE_URL at it.

Example:
    JARVISNT_BASE_DIR=/models/jarvisnt \
      python -m scripts.serve_chat --source custom --model-tag d12 --port 8000
"""

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import torch

from jarvisnt.checkpoint_manager import load_model
from jarvisnt.common import autodetect_device_type, compute_cleanup, compute_init
from jarvisnt.engine import Engine


parser = argparse.ArgumentParser(description="Serve a Jarvisn't chat checkpoint over HTTP")
parser.add_argument("--source", choices=["sft", "custom", "rl"], default="custom")
parser.add_argument("--model-tag", default=None)
parser.add_argument("--step", type=int, default=None)
parser.add_argument("--device-type", choices=["cuda", "cpu", "mps"], default="")
parser.add_argument("--host", default="0.0.0.0")
parser.add_argument("--port", type=int, default=8000)
parser.add_argument("--max-new-tokens", type=int, default=512)
parser.add_argument("--api-key", default=os.environ.get("JARVISNT_INFERENCE_API_KEY"))
args = parser.parse_args()

device_type = autodetect_device_type() if args.device_type == "" else args.device_type
_ddp, _rank, _local_rank, _world_size, device = compute_init(device_type)
model, tokenizer, _meta = load_model(
    args.source, device, phase="eval", model_tag=args.model_tag, step=args.step
)
engine = Engine(model, tokenizer)
bos = tokenizer.get_bos_token_id()
assistant_end = tokenizer.encode_special("<|assistant_end|>")


def generate_reply(messages, temperature, top_k, max_tokens):
    if not messages or messages[-1].get("role") != "user":
        raise ValueError("messages must end with a user message")
    if any(message.get("role") not in {"system", "user", "assistant"} for message in messages):
        raise ValueError("unsupported message role")

    conversation = {"messages": [
        {"role": message["role"], "content": message["content"]}
        for message in messages
    ]}
    # render_for_completion expects an assistant turn to remove, then primes
    # the model with <|assistant_start|> for the new response.
    conversation["messages"].append({"role": "assistant", "content": ""})
    prompt_tokens = tokenizer.render_for_completion(conversation)
    results, _masks = engine.generate_batch(
        prompt_tokens,
        num_samples=1,
        max_tokens=max(1, min(max_tokens, args.max_new_tokens)),
        temperature=max(0.01, temperature),
        top_k=None if top_k <= 0 else top_k,
    )
    generated = results[0][len(prompt_tokens):]
    if generated and generated[-1] == assistant_end:
        generated = generated[:-1]
    return tokenizer.decode(generated).strip()


class ChatHandler(BaseHTTPRequestHandler):
    def _send(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self._send(200, {"ok": True, "source": args.source})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/v1/chat":
            self._send(404, {"error": "not found"})
            return
        if args.api_key and self.headers.get("Authorization") != f"Bearer {args.api_key}":
            self._send(401, {"error": "unauthorized"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
            messages = payload.get("messages")
            if not isinstance(messages, list) or len(messages) > 32:
                raise ValueError("messages must be a list with at most 32 turns")
            reply = generate_reply(
                messages,
                float(payload.get("temperature", 0.6)),
                int(payload.get("top_k", 50)),
                int(payload.get("max_tokens", args.max_new_tokens)),
            )
            self._send(200, {"message": {"role": "assistant", "content": reply}})
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            self._send(400, {"error": str(exc)})
        except Exception as exc:
            self._send(500, {"error": f"inference failed: {exc}"})


server = ThreadingHTTPServer((args.host, args.port), ChatHandler)
print(f"Jarvisn't inference server listening on http://{args.host}:{args.port}")
try:
    server.serve_forever()
except KeyboardInterrupt:
    pass
finally:
    server.server_close()
    compute_cleanup()
