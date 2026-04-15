"use client";

import { useState } from "react";

import { ReportForm } from "../components/report-form";
import { ResultPanel } from "../components/result-panel";
import { SimplifyResponse } from "../lib/api";

export default function HomePage() {
  const [result, setResult] = useState<SimplifyResponse | null>(null);

  return (
    <main>
      <section className="hero">
        <h1>Radiology Report Simplifier</h1>
        <p>
          Transform technical radiology language into patient-friendly explanations while preserving
          clinical meaning.
        </p>
        <div className="disclaimer" style={{ marginTop: 12 }}>
          Educational use only. This tool does not provide diagnosis or treatment decisions.
        </div>
      </section>

      <section className="grid">
        <ReportForm onResult={setResult} />
        <ResultPanel result={result} />
      </section>
    </main>
  );
}
