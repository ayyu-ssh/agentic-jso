import { NextResponse } from "next/server";
import { getBackendUrl } from "@/lib/backend";

const SEARCH_TIMEOUT_MS = 75_000;

export async function POST(request: Request): Promise<NextResponse> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), SEARCH_TIMEOUT_MS);

  try {
    const incomingFormData = await request.formData();
    const response = await fetch(`${getBackendUrl()}/search`, {
      method: "POST",
      body: incomingFormData,
      signal: controller.signal,
    });

    const text = await response.text();
    return new NextResponse(text, {
      status: response.status,
      headers: {
        "content-type": response.headers.get("content-type") || "application/json",
      },
    });
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") {
      return NextResponse.json(
        { detail: "Search timed out. Please try again." },
        { status: 504 },
      );
    }

    return NextResponse.json(
      { detail: "Proxy error while contacting backend." },
      { status: 502 },
    );
  } finally {
    clearTimeout(timer);
  }
}
