import { SimplifyResponse } from "../lib/api";

type ResultPanelProps = {
  result: SimplifyResponse | null;
};

export function ResultPanel({ result }: ResultPanelProps) {
  if (!result) {
    return (
      <section className="card">
        <h2 className="section-title">Simplified Output</h2>
        <p>No output yet. Submit a report to generate a patient-friendly explanation.</p>
      </section>
    );
  }

  return (
    <section className="card">
      <h2 className="section-title">Simplified Output</h2>
      <span className="badge">Confidence: {Math.round(result.confidence_score * 100)}%</span>
      <span className="badge" style={{ marginLeft: 8 }}>
        Readability Grade: {result.readability_grade_level}
      </span>

      <p style={{ marginTop: 12 }}>{result.simplified_report}</p>

      <h3 className="section-title" style={{ marginTop: 18 }}>
        Key Points
      </h3>
      <ul>
        {result.summary_bullet_points.map((point) => (
          <li key={point}>{point}</li>
        ))}
      </ul>

      <h3 className="section-title" style={{ marginTop: 18 }}>
        Term Definitions
      </h3>
      <ul>
        {Object.entries(result.defined_terms).map(([term, definition]) => (
          <li key={term}>
            <strong>{term}:</strong> {definition}
          </li>
        ))}
      </ul>

      <div className="disclaimer">{result.disclaimer}</div>

      {result.warnings.length > 0 ? (
        <div className="error" style={{ marginTop: 12 }}>
          <strong>Quality Warnings:</strong>
          <ul>
            {result.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}
