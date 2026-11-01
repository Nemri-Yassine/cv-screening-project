import type { Source } from "../types";

interface Props {
  source: Source;
  active: boolean;
  onClick: () => void;
}

export default function SourceCard({ source, active, onClick }: Props) {
  return (
    <button className={`source-card ${active ? "active" : ""} ${source.cited ? "cited" : ""}`} onClick={onClick}>
      <div className="source-top">
        <span className="category">{source.category}</span>
        {source.cited && <span className="cited-badge">cited</span>}
      </div>
      <strong>{source.job_title || "Unknown title"}</strong>
      <span className="meta">
        {source.years_experience} yrs · {source.education_level}
      </span>
      <span className="file">{source.file_name}</span>
    </button>
  );
}
