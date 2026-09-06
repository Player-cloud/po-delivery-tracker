"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import RequireAdmin from "@/components/RequireAdmin";
import { useAuth } from "@/lib/useAuth";
import { btnPrimary, card, h1, input, page } from "@/lib/ui";

type User = {
  id: number;
  email: string;
  role: string;
  active: boolean;
  created_at: string;
};

const ROLES = ["administrator", "manager", "staff", "viewer"];

export default function UsersPage() {
  return (
    <RequireAdmin>
      <Users />
    </RequireAdmin>
  );
}

function Users() {
  const { token } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState("");

  // new-user form
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("staff");
  const [creating, setCreating] = useState(false);

  const myId = token ? tryDecodeId(token) : null;

  async function reload() {
    try {
      const res = await apiFetch("/users");
      if (res.ok) setUsers(await res.json());
      else setError("Could not load users");
    } catch {
      setError("Could not load users");
    }
  }

  useEffect(() => {
    let ignore = false;
    (async () => {
      try {
        const res = await apiFetch("/users");
        if (!res.ok) throw new Error();
        const data = await res.json();
        if (!ignore) setUsers(data);
      } catch {
        if (!ignore) setError("Could not load users");
      } finally {
        if (!ignore) setLoaded(true);
      }
    })();
    return () => {
      ignore = true;
    };
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setCreating(true);
    setError("");
    const res = await apiFetch("/users", {
      method: "POST",
      body: JSON.stringify({ email, password, role }),
    });
    setCreating(false);
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      setError(typeof data.detail === "string" ? data.detail : "Could not create user");
      return;
    }
    setEmail("");
    setPassword("");
    setRole("staff");
    void reload();
  }

  async function patch(id: number, body: Record<string, unknown>) {
    setError("");
    const res = await apiFetch(`/users/${id}`, { method: "PUT", body: JSON.stringify(body) });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      setError(typeof data.detail === "string" ? data.detail : "Update failed");
      return;
    }
    void reload();
  }

  function resetPassword(u: User) {
    const pw = window.prompt(`New password for ${u.email}:`);
    if (pw) void patch(u.id, { password: pw });
  }

  if (!loaded && !error) return <p className={`${page} text-muted`}>Loading…</p>;

  return (
    <div className={`${page} flex flex-col gap-5`}>
      <h1 className={h1}>Users</h1>

      <form
        onSubmit={handleCreate}
        className={`${card} flex flex-wrap items-end gap-3 p-4`}
      >
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className={input}
          aria-label="New user email"
        />
        <input
          type="password"
          placeholder="Temp password (10+ chars)"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          className={input}
          aria-label="Temporary password"
        />
        <select
          value={role}
          onChange={(e) => setRole(e.target.value)}
          className={input}
          aria-label="Role"
        >
          {ROLES.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
        <button type="submit" disabled={creating} className={btnPrimary}>
          {creating ? "Adding…" : "Add user"}
        </button>
      </form>

      {error && <p className="text-sm text-overdue-on">{error}</p>}

      <div className={`${card} overflow-hidden`}>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[560px] text-left text-[12.5px]">
            <thead>
              <tr className="border-b border-line text-[10.5px] uppercase tracking-[0.04em] text-faint">
                <th className="px-5 py-3 font-medium">Email</th>
                <th className="px-5 py-3 font-medium">Role</th>
                <th className="px-5 py-3 font-medium">Active</th>
                <th className="px-5 py-3 font-medium">Created</th>
                <th className="px-5 py-3" />
              </tr>
            </thead>
            <tbody>
              {users.map((u) => {
                const isSelf = myId === u.id;
                return (
                  <tr key={u.id} className="border-t border-line/70">
                    <td className="px-5 py-3">
                      {u.email}
                      {isSelf && <span className="ml-2 text-xs text-faint">(you)</span>}
                    </td>
                    <td className="px-5 py-3">
                      <select
                        value={u.role}
                        disabled={isSelf}
                        onChange={(e) => patch(u.id, { role: e.target.value })}
                        className="rounded-md border border-line px-2 py-1 text-[12.5px] disabled:opacity-50"
                        aria-label={`Role for ${u.email}`}
                      >
                        {ROLES.map((r) => (
                          <option key={r} value={r}>
                            {r}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="px-5 py-3">
                      <button
                        disabled={isSelf}
                        onClick={() => patch(u.id, { active: !u.active })}
                        className={`rounded-full px-2.5 py-0.5 text-xs font-medium disabled:opacity-50 ${
                          u.active ? "bg-ontrack-tint text-ontrack-on" : "bg-done-tint text-done-on"
                        }`}
                      >
                        {u.active ? "active" : "inactive"}
                      </button>
                    </td>
                    <td className="px-5 py-3 font-mono text-muted">{u.created_at.slice(0, 10)}</td>
                    <td className="px-5 py-3">
                      <button
                        onClick={() => resetPassword(u)}
                        className="text-xs text-accent hover:underline"
                      >
                        Reset password
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function tryDecodeId(token: string): number | null {
  try {
    return Number(JSON.parse(atob(token.split(".")[1])).sub) || null;
  } catch {
    return null;
  }
}
