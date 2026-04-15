"use client";

import { FormEvent, useState } from "react";

import { requestImageTextExtraction, requestSimplification, SimplifyResponse } from "../lib/api";

type ReportFormProps = {
  onResult: (result: SimplifyResponse) => void;
};

const sampleReport =
  "EXAM: CHEST X-RAY AP PORTABLE\nINDICATION: Shortness of breath\nFINDINGS: Cardiomediastinal silhouette is mildly enlarged. Mild bibasilar linear and patchy opacities, favored subsegmental atelectatic change. Small left pleural effusion. No pneumothorax.\nIMPRESSION: 1. Mild bibasilar atelectatic change. 2. Small left pleural effusion. 3. No pneumothorax.";

const secondSampleReport =
  "EXAM: CHEST X-RAY 2 VIEWS\nINDICATION: Fever and cough\nFINDINGS: Patchy right lower lobe airspace opacity may represent early infiltrate. Trace bilateral pleural effusions. Heart size upper limits of normal.\nIMPRESSION: Right basilar opacity, correlate clinically for early pneumonia. Trace pleural effusions.";

export function ReportForm({ onResult }: ReportFormProps) {
  const [reportText, setReportText] = useState(sampleReport);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [errorText, setErrorText] = useState<string | null>(null);
  const [extractStatus, setExtractStatus] = useState<string | null>(null);

  const handleImageUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    setErrorText(null);
    setExtractStatus("Extracting text from image...");
    setIsExtracting(true);

    try {
      const result = await requestImageTextExtraction(file);
      const extractedText = result.extracted_text.trim();

      if (!extractedText || extractedText.split(/\s+/).length < 15) {
        throw new Error(
          "Could not detect enough readable text. Retake the photo with better lighting and keep the page flat."
        );
      }

      setReportText(extractedText);
      setExtractStatus("Text extracted successfully. Review it before submitting.");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Image extraction failed.";
      setErrorText(message);
      setExtractStatus(null);
    } finally {
      setIsExtracting(false);
      event.target.value = "";
    }
  };

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

        <label className="label" htmlFor="reportImage" style={{ marginTop: 8 }}>
          Or upload report image (PNG/JPG) for text extraction
        </label>
        <input
          id="reportImage"
          className="file-input-hidden"
          type="file"
          accept="image/png,image/jpeg,image/jpg,image/webp"
          capture="environment"
          onChange={handleImageUpload}
          disabled={isExtracting || isSubmitting}
        />

        <label className="upload-button" htmlFor="reportImage">
          {isExtracting ? "Extracting from image..." : "Upload or Take Photo"}
        </label>

        {extractStatus ? <div className="disclaimer">{extractStatus}</div> : null}

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
            disabled={isSubmitting || isExtracting}
          >
            Load Sample 1
          </button>

          <button
            className="btn-secondary"
            type="button"
            onClick={() => setReportText(secondSampleReport)}
            disabled={isSubmitting || isExtracting}
          >
            Load Sample 2
          </button>
        </div>

        {errorText ? <div className="error">{errorText}</div> : null}
      </form>
    </section>
  );
}
