import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const maxDuration = 60;

const DEFAULT_TIMEOUT_MS = 55_000;
const DEFAULT_RATE_LIMIT = 10;
const RATE_WINDOW_MS = 60_000;
const MAX_BODY_BYTES = 64 * 1024;
const MAX_MESSAGES = 32;
const MAX_MESSAGE_CHARS = 16_000;
const MAX_CONTEXT_TURNS = 3;

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

function validateAndLimitMessages(value: unknown) {
  if (!Array.isArray(value) || value.length === 0 || value.length > MAX_MESSAGES) {
    throw new Error("messages must contain between 1 and " + MAX_MESSAGES + " items.");
  }

  const messages: { role: "system" | "user" | "assistant"; content: string }[] = [];
  for (const [index, item] of value.entries()) {
    if (!item || typeof item !== "object") throw new Error("messages[" + index + "] must be an object.");
    const message = item as { role?: unknown; content?: unknown };
    if (message.role !== "system" && message.role !== "user" && message.role !== "assistant") {
      throw new Error("messages[" + index + "].role is invalid.");
    }
    if (typeof message.content !== "string" || !message.content.trim()) {
      throw new Error("messages[" + index + "].content must be a non-empty string.");
    }
    if (message.content.length > MAX_MESSAGE_CHARS) {
      throw new Error("messages[" + index + "].content is too long.");
    }
    if (message.role === "system" && index !== 0) {
      throw new Error("A system message is allowed only at the start.");
    }
    messages.push({ role: message.role, content: message.content });
  }

  const system = messages[0]?.role === "system" ? [messages[0]] : [];
  const chat = messages.slice(system.length);
  if (!chat.length || chat[chat.length - 1].role !== "user") {
    throw new Error("messages must end with the current user message.");
  }
  if (chat.some((message, index) => message.role !== (index % 2 === 0 ? "user" : "assistant"))) {
    throw new Error("Chat messages must alternate user and assistant, starting with user.");
  }

  // Keep the system prompt, the previous three user/assistant pairs, and the
  // current user message. The UI can still display the complete local chat.
  const contextMessages = chat.slice(-(MAX_CONTEXT_TURNS * 2 + 1));
  return [...system, ...contextMessages];
}

export async function POST(request: NextRequest) {
  const limited = rateLimit(request);
  if (limited) return limited;

  const inferenceUrl = process.env.JARVISNT_INFERENCE_URL;
  const apiKey = process.env.JARVISNT_INFERENCE_API_KEY;
  if (!inferenceUrl || !apiKey) {
    return NextResponse.json(
      { error: "RunPod chat is not configured. Set the server-side inference URL and API key." },
      { status: 503 },
    );
  }

  let messages: ReturnType<typeof validateAndLimitMessages>;
  let body: Record<string, unknown>;
  try {
    const rawBody = await request.text();
    if (new TextEncoder().encode(rawBody).byteLength > MAX_BODY_BYTES) {
      return NextResponse.json({ error: "The request is too large." }, { status: 413 });
    }
    body = JSON.parse(rawBody) as Record<string, unknown>;
    messages = validateAndLimitMessages(body?.messages);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Invalid request." },
      { status: 400 },
    );
  }

  const temperature = typeof body.temperature === "number" ? body.temperature : 0.6;
  const top_k = Number.isInteger(body.top_k) ? body.top_k as number : 50;
  const max_tokens = Number.isInteger(body.max_tokens) ? body.max_tokens as number : 256;
  if (!Number.isFinite(temperature) || temperature < 0 || temperature > 2
      || top_k < 1 || top_k > 256 || max_tokens < 1 || max_tokens > 512) {
    return NextResponse.json({ error: "Generation settings are outside the allowed range." }, { status: 400 });
  }

  const controller = new AbortController();
  const timeout = setTimeout(
    () => controller.abort(),
    numberEnv("JARVISNT_INFERENCE_TIMEOUT_MS", DEFAULT_TIMEOUT_MS),
  );

  try {
    const upstream = await fetch(inferenceUrl, {
      method: "POST",
      headers: {
        Authorization: "Bearer " + apiKey,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        input: { messages, temperature, top_k, max_tokens },
      }),
      signal: controller.signal,
      cache: "no-store",
    });

    const result = await upstream.json().catch(() => null) as {
      status?: unknown;
      output?: { response?: unknown; error?: { message?: unknown } };
    } | null;

    if (!upstream.ok) {
      return NextResponse.json({ error: "RunPod could not process this message." }, { status: 502 });
    }
    if (result?.status !== "COMPLETED" || typeof result.output?.response !== "string") {
      return NextResponse.json({ error: "The model did not return a completed response." }, { status: 502 });
    }

    return NextResponse.json({
      message: { role: "assistant", content: result.output.response },
    });
  } catch (error) {
    const message = error instanceof Error && error.name === "AbortError"
      ? "The model took too long to respond."
      : "The RunPod inference service could not be reached.";
    return NextResponse.json({ error: message }, { status: 502 });
  } finally {
    clearTimeout(timeout);
  }
}
