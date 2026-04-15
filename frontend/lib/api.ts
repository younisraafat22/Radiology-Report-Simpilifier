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
