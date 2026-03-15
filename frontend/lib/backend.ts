export function getBackendUrl(): string {
  return process.env.NEXT_PUBLIC_BACKEND_URL?.trim() || "http://127.0.0.1:8000";
}
