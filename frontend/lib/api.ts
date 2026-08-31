import { clearToken, getToken } from "@/lib/auth";

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
    // Session expired mid-use — bounce to login. (A 401 on the login call
    // itself has no token and is handled by the caller.)
    clearToken();
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
  if (!res.ok) throw new Error("Login failed — check your email and password");
  const data = await res.json();
  return data.access_token as string;
}
