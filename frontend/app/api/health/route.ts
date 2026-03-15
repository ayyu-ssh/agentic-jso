import { NextResponse } from "next/server";
import { getBackendUrl } from "@/lib/backend";

export async function GET(): Promise<NextResponse> {
  try {
    const response = await fetch(`${getBackendUrl()}/health`, {
      method: "GET",
      cache: "no-store",
    });

    if (!response.ok) {
      return NextResponse.json(
        { ok: false, detail: "Backend health check failed." },
        { status: 502 },
      );
    }

    const body = await response.json();
    return NextResponse.json({ ok: true, backend: body });
  } catch {
    return NextResponse.json(
      { ok: false, detail: "Backend is unreachable." },
      { status: 502 },
    );
  }
}
