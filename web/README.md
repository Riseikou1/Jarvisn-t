# Jarvisn't web

The public project site for Jarvisn't. It documents the model architecture, training plan, current status, creator, and upstream credits. There is intentionally no chat interface until a real trained checkpoint and inference endpoint exist.

## Run locally

```bash
npm install
npm run dev
```

Open `http://localhost:3000`.

## Enable the chat

The website includes `/chat` and a Vercel-compatible `/api/chat` proxy. The
proxy keeps the inference service URL and optional API key server-side:

```bash
JARVISNT_INFERENCE_URL=https://your-inference-host.example.com
JARVISNT_INFERENCE_API_KEY=replace-me
```

The inference host must run the PyTorch model. From the repository root, after
pretraining and either SFT recipe has produced a checkpoint:

```bash
# custom_sft.py output
JARVISNT_BASE_DIR=/models/jarvisnt \
JARVISNT_INFERENCE_API_KEY=replace-me \
  .venv/bin/python -m scripts.serve_chat --source custom --model-tag d12

# chat_sft.py output instead
JARVISNT_BASE_DIR=/models/jarvisnt \
JARVISNT_INFERENCE_API_KEY=replace-me \
  .venv/bin/python -m scripts.serve_chat --source sft --model-tag d12
```

The model host needs the matching `tokenizer/` directory, the selected
checkpoint directory, and a compatible Python/PyTorch environment. Vercel
hosts the UI and proxy; it is not the model runtime.

The chat proxy limits requests to 10 per IP per minute by default and stops
waiting for the inference host after 55 seconds. Configure
`JARVISNT_RATE_LIMIT` and `JARVISNT_INFERENCE_TIMEOUT_MS` in Vercel if needed.
The built-in limiter is a lightweight per-serverless-instance safeguard; for
larger public traffic, add a shared Redis or edge/WAF rate limiter.

## Editable project information

Update `content/site.ts` for the creator bio, project status, GitHub URL, public email, model facts, and training stages. Missing contact values stay hidden or clearly marked as unconfigured; the site does not invent them.

Set `NEXT_PUBLIC_SITE_URL` in production so canonical social-image URLs use the deployed host. During local development the incoming request host is used automatically.
