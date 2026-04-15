export type SimplifyResponse = {
  simplified_report: string;
  summary_bullet_points: string[];
  defined_terms: Record<string, string>;
  confidence_score: number;
  readability_grade_level: number;
  warnings: string[];
  model_source: string;
  disclaimer: string;
};

export type ExtractTextResponse = {
  extracted_text: string;
  model_source: string;
};

export async function requestSimplification(reportText: string): Promise<SimplifyResponse> {
  let response: Response;
  try {
    response = await fetch("/api/simplify", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ report_text: reportText }),
    });
  } catch {
    throw new Error("Failed to fetch local API route /api/simplify.");
  }

  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: "Request failed." }));
    throw new Error(payload.detail || "Request failed.");
  }

  return (await response.json()) as SimplifyResponse;
}

export async function requestImageTextExtraction(file: File): Promise<ExtractTextResponse> {
  const formData = new FormData();
  formData.append("file", file);

  let response: Response;
  try {
    response = await fetch("/api/extract-text", {
      method: "POST",
      body: formData,
    });
  } catch {
    throw new Error("Failed to fetch local API route /api/extract-text.");
  }

  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: "Image extraction failed." }));
    throw new Error(payload.detail || "Image extraction failed.");
  }

  return (await response.json()) as ExtractTextResponse;
}
