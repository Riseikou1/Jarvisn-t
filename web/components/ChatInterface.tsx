"use client";

import { FormEvent, useState } from "react";

type Message = { role: "user" | "assistant"; content: string };

export function ChatInterface() {
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
    <section className={`inference-chat${messages.length ? " has-messages" : ""}`} aria-label="Jarvisn't chat">
      {messages.length === 0 ? (
        <div className="inference-welcome"><h1>What can I help with?</h1></div>
      ) : (
        <div className="inference-messages" aria-live="polite">
          {messages.map((message, index) => (
            <article className={`inference-message ${message.role}`} key={`${message.role}-${index}`}>
              {message.role === "user" ? <p>{message.content}</p> : <div><span className="assistant-mark">J</span><p>{message.content}</p></div>}
            </article>
          ))}
          {busy && <article className="inference-message assistant"><div><span className="assistant-mark">J</span><p className="typing">Thinking…</p></div></article>}
        </div>
      )}
      <div className="inference-composer-wrap">
        {error && <p className="inference-error" role="alert">{error}</p>}
        <form className="inference-composer" onSubmit={send}>
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); event.currentTarget.form?.requestSubmit(); } }}
            placeholder="Ask anything"
            rows={1}
            disabled={busy}
            aria-label="Message Jarvisn't"
          />
          <button type="submit" disabled={busy || !input.trim()} aria-label="Send message">↑</button>
        </form>
        <p className="inference-note">Jarvis&apos;nt is still in development. Responses may be unreliable.</p>
      </div>
    </section>
  );
}
