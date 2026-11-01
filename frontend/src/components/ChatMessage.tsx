import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
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

// [10554236.pdf] in the answer becomes a link that react-markdown renders as a citation chip
function linkCitations(text: string) {
  return text.replace(CITATION, (_, fileName) => `[${fileName}](${CITATION_PREFIX}${fileName})`);
}

function formatArgs(args: Record<string, unknown>) {
  return Object.entries(args)
    .map(([key, value]) => `${key}=${JSON.stringify(value)}`)
    .join(", ");
}

export default function ChatMessage({ message, selected, onSelect, onCitation }: Props) {
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
                  return (
                    <button className="citation" onClick={() => onCitation(fileName)} title="Open this CV">
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
          <h4>Sources ({sources.length})</h4>
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
