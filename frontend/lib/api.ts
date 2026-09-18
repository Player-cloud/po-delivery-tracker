import { clearToken, getToken } from "@/lib/auth";
import { extractErrorMessage } from "@/lib/errors";

// Backend origin — set NEXT_PUBLIC_API_BASE_URL (e.g. https://api.example.com) at
// build time for deployment (M6); defaults to the local dev backend.
const API_ORIGIN =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8000";
export const API_BASE = `${API_ORIGIN}/api/v1`;

export async function apiFetch(path: string, options: RequestInit = {}) {
  const token = getToken();
  // Let the browser set Content-Type (with the multipart boundary) for FormData.
  const isForm = options.body instanceof FormData;
  const headers = {
    ...(isForm ? {} : { "Content-Type": "application/json" }),
    ...(options.headers || {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (response.status === 401 && token) {
    // Session expired mid-use — hard-navigate to login so all client state is
    // dropped. (A 401 on the login call itself has no token; the caller handles
    // that.) Deliberate full reload, not a router push.
    clearToken();
    // eslint-disable-next-line @next/next/no-location-assign-relative-destination
    window.location.href = "/login";
    throw new Error("Not authenticated");
  }

  return response;
}

/** Exchange email + password for a token. Uses the OAuth2 form encoding FastAPI expects. */
export async function login(email: string, password: string): Promise<string> {
  const body = new URLSearchParams({ username: email, password });
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: body.toString(),
  });
  if (!res.ok) {
    if (res.status === 429) throw new Error("Too many attempts — wait a minute and try again.");
    if (res.status === 403) throw new Error("This account has been disabled.");
    if (res.status >= 500) throw new Error("The server had a problem — try again shortly.");
    throw new Error("Login failed — check your email and password.");
  }
  const data = await res.json();
  return data.access_token as string;
}

/** Ask for a password-reset email. The API answers the same way whether or not
 *  the address has an account, so this only throws for rate limits / outages. */
export async function requestPasswordReset(email: string): Promise<void> {
  const res = await fetch(`${API_BASE}/auth/forgot-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  if (res.status === 429) throw new Error("Too many requests — wait a while and try again.");
  if (!res.ok) throw new Error("Could not send the reset email — try again shortly.");
}

/** Set a new password using the token from the emailed link. */
export async function resetPassword(token: string, password: string): Promise<void> {
  const res = await fetch(`${API_BASE}/auth/reset-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, password }),
  });
  if (res.ok) return;
  if (res.status === 429) throw new Error("Too many attempts — wait a minute and try again.");
  const data = await res.json().catch(() => ({}));
  throw new Error(extractErrorMessage(data).replace(/^Value error, /, ""));
}
