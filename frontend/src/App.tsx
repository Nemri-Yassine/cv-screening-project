import { useEffect, useRef, useState } from "react";
import { getCandidate, getHealth, sendChat } from "./api";
import ChatMessage from "./components/ChatMessage";
import CandidatePanel from "./components/CandidatePanel";
import type { Health, Message, Mode, Source } from "./types";

const EXAMPLES = [
  "Find me IT profiles with Python and at least 3 years of experience",
  "I need an accountant who knows QuickBooks",
  "Compare the top 2 chefs on menu planning and food safety",
  "Do we have a nurse with a master degree?",
];

const MODES: { value: Mode; label: string; hint: string }[] = [
  { value: "agent", label: "Agent", hint: "The LLM calls tools (search, read CV, compare) and keeps the conversation" },
  { value: "rag", label: "RAG pipeline", hint: "Fixed LangGraph: extract filters, retrieve, grade, generate" },
];

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [mode, setMode] = useState<Mode>("agent");
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<Source | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getHealth().then(setHealth).catch((error) => setHealthError(error.message));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function ask(question: string) {
    question = question.trim();
    if (!question || loading) return;

    const userMessage: Message = { id: crypto.randomUUID(), role: "user", content: question };
    const previous = messages;
    setMessages([...previous, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const response = await sendChat(question, mode, previous);
      const firstCited = response.sources.find((source) => source.cited) ?? response.sources[0] ?? null;
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: response.answer,
          sources: response.sources,
          toolCalls: response.tool_calls,
          filters: response.filters,
          mode: response.mode,
        },
      ]);
      // open the first cited CV so answer ↔ source ↔ PDF is obvious in the demo
      if (firstCited) setSelected(firstCited);
    } catch (error) {
      setMessages((current) => [
        ...current,
        { id: crypto.randomUUID(), role: "assistant", content: (error as Error).message, error: true },
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function openCitation(fileName: string, sources: Source[]) {
    const known = sources.find((source) => source.file_name === fileName);
    if (known) {
      setSelected(known);
      return;
    }
    try {
      setSelected(await getCandidate(fileName));
    } catch {
      setSelected(null);
    }
  }

  function onKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      ask(input);
    }
  }

  return (
    <div className={`app ${selected ? "with-panel" : ""}`}>
      <header className="header">
        <div className="brand">
          <span className="logo">CV</span>
          <div>
            <h1>CV Screening Assistant</h1>
            <p>Ask in natural language, get candidates with their CV as source</p>
          </div>
        </div>

        <div className="header-actions">
          <div className="mode-switch" role="radiogroup" aria-label="Assistant mode">
            {MODES.map((option) => (
              <button
                key={option.value}
                role="radio"
                aria-checked={mode === option.value}
                className={mode === option.value ? "active" : ""}
                title={option.hint}
                onClick={() => setMode(option.value)}
              >
                {option.label}
              </button>
            ))}
          </div>
          <button className="ghost" onClick={() => setMessages([])} disabled={!messages.length || loading}>
            New chat
          </button>
          <span className={`status ${health ? "ok" : healthError ? "down" : ""}`} title={healthError ?? ""}>
            {health ? `${health.cv_count} CVs indexed` : healthError ? "Backend offline" : "Connecting..."}
          </span>
        </div>
      </header>

      <main className="chat">
        {messages.length === 0 ? (
          <div className="empty">
            <h2>Who are you looking for?</h2>
            <p>{MODES.find((option) => option.value === mode)?.hint}</p>
            <div className="examples">
              {EXAMPLES.map((example) => (
                <button key={example} onClick={() => ask(example)}>
                  {example}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="messages">
            {messages.map((message) => (
              <ChatMessage
                key={message.id}
                message={message}
                selected={selected?.file_name}
                onSelect={setSelected}
                onCitation={(fileName) => openCitation(fileName, message.sources ?? [])}
              />
            ))}
            {loading && (
              <div className="message assistant">
                <div className="bubble thinking">
                  <span />
                  <span />
                  <span />
                  {mode === "agent" ? "The agent is calling tools..." : "Searching the CVs..."}
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}

        <form
          className="composer"
          onSubmit={(event) => {
            event.preventDefault();
            ask(input);
          }}
        >
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={onKeyDown}
            placeholder="e.g. find a designer who can do UI/UX with 5+ years of experience"
            rows={1}
          />
          <button type="submit" disabled={!input.trim() || loading}>
            Send
          </button>
        </form>
      </main>

      {selected && <CandidatePanel source={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}
