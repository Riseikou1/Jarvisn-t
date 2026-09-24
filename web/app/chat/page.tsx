"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";

type Message = { role: "user" | "assistant"; content: string };

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function send(event: FormEvent) {
    event.preventDefault();
    const content = input.trim();
    if (!content || busy) return;
    const nextMessages = [...messages, { role: "user" as const, content }];
    setMessages(nextMessages);
    setInput("");
    setError("");
    setBusy(true);
    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: nextMessages, temperature: 0.6, top_k: 50, max_tokens: 512 }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || "The model did not respond.");
      setMessages([...nextMessages, payload.message]);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The model did not respond.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main id="main-content" className="chat-page shell">
      <div className="chat-heading">
        <div>
          <p className="kicker"><span />Live model interface</p>
          <h1>Talk to Jarvis&apos;nt.</h1>
          <p>Responses come from the deployed Jarvis&apos;nt checkpoint, not a placeholder demo.</p>
        </div>
        <Link className="button secondary" href="/model">Model details</Link>
      </div>

      <section className="chat-panel" aria-label="Jarvisn't chat">
        <div className="chat-messages" aria-live="polite">
          {messages.length === 0 && <div className="chat-empty"><strong>Ready when you are.</strong><span>Ask about code, language models, or anything else.</span></div>}
          {messages.map((message, index) => <article className={`chat-message ${message.role}`} key={`${message.role}-${index}`}><span>{message.role === "user" ? "YOU" : "JARVIS'NT"}</span><p>{message.content}</p></article>)}
          {busy && <article className="chat-message assistant"><span>JARVIS&apos;NT</span><p className="typing">Thinking<span>.</span><span>.</span><span>.</span></p></article>}
        </div>
        {error && <p className="chat-error" role="alert">{error}</p>}
        <form className="chat-form" onSubmit={send}>
          <textarea value={input} onChange={(event) => setInput(event.target.value)} placeholder="Message Jarvisn't..." rows={2} disabled={busy} aria-label="Message" />
          <button className="button primary" type="submit" disabled={busy || !input.trim()}>{busy ? "Working" : "Send"}<span>↗</span></button>
        </form>
      </section>
    </main>
  );
}
