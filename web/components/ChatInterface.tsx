"use client";

import { FormEvent, useEffect, useRef, useState } from "react";

type Message = { role: "user" | "assistant"; content: string };

const MAX_CONTEXT_MESSAGES = 7; // three complete exchanges plus the current user message

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, busy]);

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
        body: JSON.stringify({
          messages: nextMessages.slice(-MAX_CONTEXT_MESSAGES),
          temperature: 0.6,
          top_k: 50,
          max_tokens: 256,
        }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || "The model did not respond.");
      if (payload.message?.role !== "assistant" || typeof payload.message.content !== "string") {
        throw new Error("The model returned an invalid response.");
      }
      setMessages([...nextMessages, payload.message as Message]);
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
          <div ref={messagesEndRef} aria-hidden="true" />
        </div>
      )}
      <div className="inference-composer-wrap">
        <details className="inference-disclosure">
          <summary><span aria-hidden="true">ⓘ</span> About this chat</summary>
          <div className="inference-disclosure-content">
            <p>This project is designed to run on a tight budget. It uses a CPU rather than an always-on GPU cluster, so the service may take a while to start when it has been idle. If many people are chatting at once, you may also have to wait in a queue.</p>
            <p>The model is an experimental, small model built to beat GPT-2. It can make things up confidently, so please check important information. Thanks for your patience while this project grows.</p>
          </div>
        </details>
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
        <p className="inference-note">Experimental small model · Responses may be unreliable</p>
      </div>
    </section>
  );
}
