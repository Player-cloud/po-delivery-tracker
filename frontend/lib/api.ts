import { getToken, clearToken } from "@/lib/auth";

const API_BASE = "http://localhost:8000/api/v1";

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

  if (response.status === 401) {
    clearToken();
    window.location.href = "/login";
    throw new Error("Not authenticated");
  }

  return response;
}