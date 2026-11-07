import type { Source } from "../types";

interface Props {
  source: Source;
  active: boolean;
  onClick: () => void;
}

export default function SourceCard({ source, active, onClick }: Props) {
  const index = source.citation_index;

  return (
    <button
      id={`source-${source.file_name}`}
      className={`source-card ${active ? "active" : ""} ${source.cited ? "cited" : ""}`}
      onClick={onClick}
      title={source.cited ? "Cited in the answer — click to open the CV" : "Retrieved but not cited — click to open"}
    >
      <div className="source-top">
        <span className="category">{source.category}</span>
        {source.cited && index != null ? (
          <span className="cited-badge">cited [{index}]</span>
        ) : (
          <span className="retrieved-badge">retrieved</span>
        )}
      </div>
      <strong>
        {index != null && <span className="cite-num">{index}. </span>}
        {source.job_title || "Unknown title"}
      </strong>
      <span className="meta">
        {source.years_experience} yrs · {source.education_level}
      </span>
      <span className="file">{source.file_name}</span>
    </button>
  );
}
