"use client";

import { FormEvent, useState } from "react";
import Tesseract from "tesseract.js";

import { requestSimplification, SimplifyResponse } from "../lib/api";

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
  const [ocrStatus, setOcrStatus] = useState<string | null>(null);

  const handleImageUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    setErrorText(null);
    setOcrStatus("Extracting text from image...");
    setIsExtracting(true);

    try {
      const preprocessedImage = await preprocessImageForOcr(file);
      const result = await Tesseract.recognize(preprocessedImage, "eng", {
        // These parameters work better for report-style scanned pages.
        tessedit_pageseg_mode: "6",
        preserve_interword_spaces: "1",
      } as unknown as Record<string, string>);

      const extractedText = cleanExtractedText(result.data.text);

      if (!extractedText || extractedText.split(/\s+/).length < 15) {
        throw new Error(
          "OCR could not detect enough readable text. Retake the photo with better lighting and keep the page flat."
        );
      }

      setReportText(extractedText);
      setOcrStatus("Text extracted successfully. Review it before submitting.");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Image OCR failed.";
      setErrorText(message);
      setOcrStatus(null);
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
          Or upload report image (PNG/JPG) for OCR text extraction
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

        {ocrStatus ? <div className="disclaimer">{ocrStatus}</div> : null}

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

async function preprocessImageForOcr(file: File): Promise<string> {
  const originalDataUrl = await readFileAsDataUrl(file);
  const image = await loadImage(originalDataUrl);

  const canvas = document.createElement("canvas");
  const context = canvas.getContext("2d");

  if (!context) {
    return originalDataUrl;
  }

  // Upscale for small fonts to improve OCR quality.
  const scale = 2;
  canvas.width = Math.max(1, Math.floor(image.width * scale));
  canvas.height = Math.max(1, Math.floor(image.height * scale));

  context.drawImage(image, 0, 0, canvas.width, canvas.height);

  const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
  const pixels = imageData.data;

  for (let i = 0; i < pixels.length; i += 4) {
    const r = pixels[i];
    const g = pixels[i + 1];
    const b = pixels[i + 2];

    // Grayscale + moderate contrast stretch.
    let gray = 0.299 * r + 0.587 * g + 0.114 * b;
    gray = (gray - 128) * 1.35 + 128;

    // Mild thresholding to reduce noisy backgrounds.
    const normalized = gray > 165 ? 255 : gray < 85 ? 0 : gray;

    pixels[i] = normalized;
    pixels[i + 1] = normalized;
    pixels[i + 2] = normalized;
  }

  context.putImageData(imageData, 0, 0);

  return canvas.toDataURL("image/png");
}

function cleanExtractedText(rawText: string): string {
  const lines = rawText
    .replace(/\r/g, "")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  const cleaned = lines.filter((line) => {
    const lettersOnly = line.replace(/[^A-Za-z]/g, "");
    return lettersOnly.length >= 3;
  });

  return cleaned.join("\n").trim();
}

function readFileAsDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(new Error("Failed to read image file."));
    reader.readAsDataURL(file);
  });
}

function loadImage(dataUrl: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error("Failed to load image for OCR."));
    image.src = dataUrl;
  });
}
