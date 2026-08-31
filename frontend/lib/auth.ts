// Auth token store. The token lives in localStorage; components subscribe via
// `useAuth()` (lib/useAuth.ts) so login/logout is reflected everywhere at once,
// including across browser tabs.

const TOKEN_KEY = "access_token";

const subscribers = new Set<() => void>();

function notify() {
  subscribers.forEach((cb) => cb());
}

/** For useSyncExternalStore. Also wires cross-tab `storage` events. */
export function subscribe(cb: () => void): () => void {
  subscribers.add(cb);
  const onStorage = (e: StorageEvent) => {
    if (e.key === TOKEN_KEY) cb();
  };
  window.addEventListener("storage", onStorage);
  return () => {
    subscribers.delete(cb);
    window.removeEventListener("storage", onStorage);
  };
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

/** Server snapshot for useSyncExternalStore — no localStorage during SSR. */
export function getServerToken(): null {
  return null;
}

export function saveToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
  notify();
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
  notify();
}

export function getUserRole(): string | null {
  const token = getToken();
  if (!token) return null;
  try {
    const payload = token.split(".")[1];
    const decoded = JSON.parse(atob(payload));
    return decoded.role ?? null;
  } catch {
    return null;
  }
}
