import { NextRequest, NextResponse } from "next/server";

const REQUEST_TIMEOUT_MS = 90000;

export async function POST(request: NextRequest) {
  const backendBaseUrl =
    process.env.BACKEND_API_BASE_URL ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    "http://localhost:8000";

  let incomingFormData: FormData;
  try {
    incomingFormData = await request.formData();
  } catch {
    return NextResponse.json({ detail: "Invalid multipart payload." }, { status: 400 });
  }

  const file = incomingFormData.get("file");
  if (!(file instanceof File)) {
    return NextResponse.json({ detail: "Missing file field." }, { status: 400 });
  }

  const backendFormData = new FormData();
  backendFormData.append("file", file, file.name);

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(`${backendBaseUrl}/api/v1/extract-text`, {
      method: "POST",
      body: backendFormData,
      signal: controller.signal,
    });

    const text = await response.text();
    const contentType = response.headers.get("content-type") || "application/json";

    return new NextResponse(text, {
      status: response.status,
      headers: {
        "Content-Type": contentType,
      },
    });
  } catch {
    return NextResponse.json(
      {
        detail:
          "Backend extraction request failed from Vercel API route. Check BACKEND_API_BASE_URL and backend availability.",
      },
      { status: 502 }
    );
  } finally {
    clearTimeout(timeout);
  }
}
