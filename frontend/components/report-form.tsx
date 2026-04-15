"use client";

import { FormEvent, useState } from "react";

import { requestSimplification, SimplifyResponse } from "../lib/api";

type ReportFormProps = {
  onResult: (result: SimplifyResponse) => void;
};

const sampleReport =
  "FINDINGS: Mild bibasilar atelectatic changes. No focal consolidation. Small left pleural effusion. Cardiomediastinal silhouette is mildly enlarged.";

export function ReportForm({ onResult }: ReportFormProps) {
  const [reportText, setReportText] = useState(sampleReport);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorText, setErrorText] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrorText(null);
    setIsSubmitting(true);

    try {
      const result = await requestSimplification(reportText);
      onResult(result);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unexpected error.";
      setErrorText(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="card">
      <h2 className="section-title">Report Input</h2>
      <form onSubmit={handleSubmit}>
        <label className="label" htmlFor="reportText">
          Paste de-identified radiology report
        </label>
        <textarea
          id="reportText"
          value={reportText}
          onChange={(event) => setReportText(event.target.value)}
        />

        <div className="toolbar">
          <button className="btn-primary" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Simplifying..." : "Simplify Report"}
          </button>
          <button
            className="btn-secondary"
            type="button"
            onClick={() => setReportText(sampleReport)}
            disabled={isSubmitting}
          >
            Load Sample
          </button>
        </div>

        {errorText ? <div className="error">{errorText}</div> : null}
      </form>
    </section>
  );
}
