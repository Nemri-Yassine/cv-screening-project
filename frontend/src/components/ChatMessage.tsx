import { useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { citationIndex } from "../citations";
import type { Message, Source } from "../types";
import SourceCard from "./SourceCard";

const CITATION = /\[([\w-]+\.pdf)\](?!\()/g;
const CITATION_PREFIX = "#cv:";

interface Props {
  message: Message;
  selected?: string;
  onSelect: (source: Source) => void;
  onCitation: (fileName: string) => void;
}

// [10554236.pdf] -> markdown link; chip label shows [1], [2], ...
function linkCitations(text: string) {
  return text.replace(CITATION, (_, fileName) => {
    const index = citationIndex(text, fileName);
    const label = index != null ? `[${index}]` : `[${fileName}]`;
    return `[${label}](${CITATION_PREFIX}${fileName})`;
  });
}

function formatArgs(args: Record<string, unknown>) {
  return Object.entries(args)
    .map(([key, value]) => `${key}=${JSON.stringify(value)}`)
    .join(", ");
}

export default function ChatMessage({ message, selected, onSelect, onCitation }: Props) {
  useEffect(() => {
    if (!selected) return;
    document.getElementById(`source-${selected}`)?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [selected]);

  if (message.role === "user") {
    return (
      <div className="message user">
        <div className="bubble">{message.content}</div>
      </div>
    );
  }

  if (message.error) {
    return (
      <div className="message assistant">
        <div className="bubble error">
          <strong>Something went wrong.</strong> {message.content}
        </div>
      </div>
    );
  }

  const sources = message.sources ?? [];
  const toolCalls = message.toolCalls ?? [];
  const citedCount = sources.filter((source) => source.cited).length;

  return (
    <div className="message assistant">
      <div className="bubble">
        {toolCalls.length > 0 && (
          <details className="trace">
            <summary>
              Used {toolCalls.length} tool call{toolCalls.length > 1 ? "s" : ""}
            </summary>
            <ol>
              {toolCalls.map((call, index) => (
                <li key={index}>
                  <code>
                    {call.name}({formatArgs(call.args)})
                  </code>
                </li>
              ))}
            </ol>
          </details>
        )}

        {message.filters && (
          <div className="filters">
            <span>query: {message.filters.search_query}</span>
            {message.filters.category && <span>category: {message.filters.category}</span>}
            {message.filters.min_years > 0 && <span>min years: {message.filters.min_years}</span>}
          </div>
        )}

        <div className="markdown">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              a: ({ href, children }) => {
                if (href?.startsWith(CITATION_PREFIX)) {
                  const fileName = href.slice(CITATION_PREFIX.length);
                  const active = fileName === selected;
                  return (
                    <button
                      className={`citation ${active ? "active" : ""}`}
                      onClick={() => onCitation(fileName)}
                      title={`Open source ${fileName}`}
                    >
                      {children}
                    </button>
                  );
                }
                return (
                  <a href={href} target="_blank" rel="noreferrer">
                    {children}
                  </a>
                );
              },
            }}
          >
            {linkCitations(message.content)}
          </ReactMarkdown>
        </div>
      </div>

      {sources.length > 0 && (
        <div className="sources">
          <h4>
            Sources ({sources.length})
            {citedCount > 0 && (
              <span className="sources-hint">
                {" "}
                · {citedCount} cited in the answer — click a chip or a card to open the PDF
              </span>
            )}
          </h4>
          <div className="source-grid">
            {sources.map((source) => (
              <SourceCard
                key={source.file_name}
                source={source}
                active={source.file_name === selected}
                onClick={() => onSelect(source)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
