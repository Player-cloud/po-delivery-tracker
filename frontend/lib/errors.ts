// FastAPI returns two error shapes:
// - Pydantic 422:  { detail: [{ msg, loc, type }, ...] }
// - HTTPException:  { detail: "some string" }
export function extractErrorMessage(data: unknown, fallback = "Something went wrong"): string {
  if (typeof data === "object" && data !== null && "detail" in data) {
    const detail = (data as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join(", ") || fallback;
    }
  }
  return fallback;
}
