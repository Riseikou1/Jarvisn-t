import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
// Leave a small margin below the platform function limit so the route can
// return a useful JSON response instead of being terminated abruptly.
export const maxDuration = 60;

const DEFAULT_TIMEOUT_MS = 55_000;
const DEFAULT_RATE_LIMIT = 10;
const RATE_WINDOW_MS = 60_000;
const MAX_BODY_BYTES = 64 * 1024;
const MAX_MESSAGES = 32;

type RateEntry = { count: number; windowStartedAt: number };
const rateEntries = new Map<string, RateEntry>();

function numberEnv(name: string, fallback: number) {
  const value = Number(process.env[name]);
  return Number.isFinite(value) && value > 0 ? value : fallback;
}

function clientKey(request: NextRequest) {
  return request.headers.get("x-forwarded-for")?.split(",")[0]?.trim()
    || request.headers.get("x-real-ip")
    || "unknown";
}

function rateLimit(request: NextRequest) {
  const now = Date.now();
  const key = clientKey(request);
  const existing = rateEntries.get(key);
  const limit = numberEnv("JARVISNT_RATE_LIMIT", DEFAULT_RATE_LIMIT);

  // Keep this best-effort in-memory table bounded on warm instances.
  if (rateEntries.size > 10_000) {
    for (const [entryKey, entry] of rateEntries) {
      if (now - entry.windowStartedAt >= RATE_WINDOW_MS) rateEntries.delete(entryKey);
    }
  }

  if (!existing || now - existing.windowStartedAt >= RATE_WINDOW_MS) {
    rateEntries.set(key, { count: 1, windowStartedAt: now });
    return null;
  }

  if (existing.count >= limit) {
    const retryAfter = Math.max(1, Math.ceil((RATE_WINDOW_MS - (now - existing.windowStartedAt)) / 1000));
    return NextResponse.json(
      { error: "Too many messages. Please wait a moment and try again." },
      { status: 429, headers: { "Retry-After": String(retryAfter) } },
    );
  }

  existing.count += 1;
  return null;
}

export async function POST(request: NextRequest) {
  const limited = rateLimit(request);
  if (limited) return limited;

  const inferenceUrl = process.env.JARVISNT_INFERENCE_URL;
  if (!inferenceUrl) {
    return NextResponse.json(
      { error: "Chat inference is not configured. Set JARVISNT_INFERENCE_URL." },
      { status: 503 },
    );
  }

  try {
    const rawBody = await request.text();
    if (new TextEncoder().encode(rawBody).byteLength > MAX_BODY_BYTES) {
      return NextResponse.json({ error: "The request is too large." }, { status: 413 });
    }

    let body: { messages?: unknown[]; [key: string]: unknown };
    try {
      body = JSON.parse(rawBody) as { messages?: unknown[]; [key: string]: unknown };
    } catch {
      return NextResponse.json({ error: "Request body must be valid JSON." }, { status: 400 });
    }

    if (!Array.isArray(body?.messages) || body.messages.length === 0 || body.messages.length > MAX_MESSAGES) {
      return NextResponse.json(
        { error: `messages must contain between 1 and ${MAX_MESSAGES} items.` },
        { status: 400 },
      );
    }

    const headers: HeadersInit = { "Content-Type": "application/json" };
    const apiKey = process.env.JARVISNT_INFERENCE_API_KEY;
    if (apiKey) headers.Authorization = `Bearer ${apiKey}`;

    const controller = new AbortController();
    const timeout = setTimeout(
      () => controller.abort(),
      numberEnv("JARVISNT_INFERENCE_TIMEOUT_MS", DEFAULT_TIMEOUT_MS),
    );
    try {
      const upstream = await fetch(`${inferenceUrl.replace(/\/$/, "")}/v1/chat`, {
        method: "POST",
        headers,
        body: JSON.stringify(body),
        signal: controller.signal,
        cache: "no-store",
      });
      const payload = await upstream.json().catch(() => ({ error: "Invalid inference response." }));
      return NextResponse.json(payload, { status: upstream.status });
    } finally {
      clearTimeout(timeout);
    }
  } catch (error) {
    const message = error instanceof Error && error.name === "AbortError"
      ? "The model took too long to respond."
      : "The inference service could not be reached.";
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
