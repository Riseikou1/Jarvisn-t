# Jarvisn't web

The public project site for Jarvisn't. It documents the model architecture, training plan, current status, creator, and upstream credits. There is intentionally no chat interface until a real trained checkpoint and inference endpoint exist.

## Run locally

```bash
npm install
npm run dev
```

Open `http://localhost:3000`.

## Editable project information

Update `content/site.ts` for the creator bio, project status, GitHub URL, public email, model facts, and training stages. Missing contact values stay hidden or clearly marked as unconfigured; the site does not invent them.

Set `NEXT_PUBLIC_SITE_URL` in production so canonical social-image URLs use the deployed host. During local development the incoming request host is used automatically.
