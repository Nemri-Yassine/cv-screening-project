import { cvUrl } from "../api";
import type { Source } from "../types";

interface Props {
  source: Source;
  onClose: () => void;
}

export default function CandidatePanel({ source, onClose }: Props) {
  const url = cvUrl(source.file_name);

  return (
    <aside className="panel">
      <div className="panel-header">
        <div>
          <span className="category">{source.category}</span>
          <h3>{source.job_title || "Unknown title"}</h3>
          <span className="file">{source.file_name}</span>
        </div>
        <button className="ghost icon" onClick={onClose} aria-label="Close">
          ×
        </button>
      </div>

      <dl className="facts">
        <div>
          <dt>Experience</dt>
          <dd>{source.years_experience} years</dd>
        </div>
        <div>
          <dt>Education</dt>
          <dd>{source.education_level}</dd>
        </div>
      </dl>

      <p className="summary">{source.summary}</p>

      <div className="skills">
        {source.skills.map((skill) => (
          <span key={skill}>{skill}</span>
        ))}
      </div>

      <div className="pdf-header">
        <h4>Original CV</h4>
        <a href={url} target="_blank" rel="noreferrer">
          Open in a new tab
        </a>
      </div>
      <iframe className="pdf" src={url} title={`CV ${source.file_name}`} />
    </aside>
  );
}
