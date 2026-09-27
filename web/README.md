# Jarvisn't web

The public project site for Jarvisn't, including the chat interface.

## Run locally

```bash
npm install
npm run dev
```

Open `http://localhost:3000`.

## Connect chat to RunPod

The Next.js `/api/chat` route calls the RunPod Serverless `/runsync` endpoint.
It keeps the RunPod API key on the server and adapts RunPod's response for the
chat UI. Configure these variables in the web app's local `web/.env.local`
file for development, and in the Vercel project's Environment Variables for
deployment:

```dotenv
JARVISNT_INFERENCE_URL=https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync
JARVISNT_INFERENCE_API_KEY=your_runpod_api_key
```

Use the RunPod endpoint ID in the URL and the RunPod API key as the secret.
Do not prefix either variable with `NEXT_PUBLIC_`: that would expose it to
browser code. After adding or changing variables, restart the local Next.js
server or redeploy the Vercel project.

Each inference request contains the previous three complete user/assistant
exchanges and the current user message. The browser can keep showing older
messages, but they are not sent to the model. The API route enforces the same
limit. Generation defaults to 256 new tokens (maximum 512); the route also
limits requests to 10 per IP per minute by default and times out after 55
seconds. Configure `JARVISNT_RATE_LIMIT` and
`JARVISNT_INFERENCE_TIMEOUT_MS` in Vercel if needed. The built-in rate
limiter is per serverless instance; for larger public traffic, use a shared
rate limiter or an edge/WAF rule.

Set `NEXT_PUBLIC_SITE_URL` in production so canonical social-image URLs use
the deployed host. During local development the incoming request host is used
automatically.

## Editable project information

Update `content/site.ts` for the creator bio, project status, GitHub URL,
public email, model facts, and training stages. Missing contact values stay
hidden or clearly marked as unconfigured; the site does not invent them.
