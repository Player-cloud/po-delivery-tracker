"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import RequireAdmin from "@/components/RequireAdmin";
import { useAuth } from "@/lib/useAuth";

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

  if (!loaded && !error) return <p className="p-8">Loading...</p>;

  return (
    <div className="p-8">
      <h1 className="mb-6 text-xl font-semibold">Users</h1>

      <form
        onSubmit={handleCreate}
        className="mb-8 flex flex-wrap items-end gap-3 rounded border bg-white p-4"
      >
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className="rounded border px-3 py-2 text-sm"
        />
        <input
          type="password"
          placeholder="Temp password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          className="rounded border px-3 py-2 text-sm"
        />
        <select
          value={role}
          onChange={(e) => setRole(e.target.value)}
          className="rounded border px-3 py-2 text-sm"
        >
          {ROLES.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
        <button
          type="submit"
          disabled={creating}
          className="rounded bg-black px-4 py-2 text-sm text-white hover:bg-zinc-800 disabled:opacity-50"
        >
          {creating ? "Adding..." : "Add user"}
        </button>
      </form>

      {error && <p className="mb-3 text-sm text-red-600">{error}</p>}

      <table className="w-full border-collapse text-left text-sm">
        <thead>
          <tr className="border-b text-xs uppercase text-zinc-400">
            <th className="py-2 font-medium">Email</th>
            <th className="font-medium">Role</th>
            <th className="font-medium">Active</th>
            <th className="font-medium">Created</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {users.map((u) => {
            const isSelf = myId === u.id;
            return (
              <tr key={u.id} className="border-b">
                <td className="py-2">
                  {u.email}
                  {isSelf && <span className="ml-2 text-xs text-zinc-400">(you)</span>}
                </td>
                <td>
                  <select
                    value={u.role}
                    disabled={isSelf}
                    onChange={(e) => patch(u.id, { role: e.target.value })}
                    className="rounded border px-2 py-1 text-sm disabled:opacity-50"
                  >
                    {ROLES.map((r) => (
                      <option key={r} value={r}>
                        {r}
                      </option>
                    ))}
                  </select>
                </td>
                <td>
                  <button
                    disabled={isSelf}
                    onClick={() => patch(u.id, { active: !u.active })}
                    className={`rounded px-2 py-0.5 text-xs ring-1 ring-inset disabled:opacity-50 ${
                      u.active
                        ? "bg-green-50 text-green-700 ring-green-600/20"
                        : "bg-zinc-100 text-zinc-500 ring-zinc-400/30"
                    }`}
                  >
                    {u.active ? "active" : "inactive"}
                  </button>
                </td>
                <td className="tabular-nums text-zinc-500">{u.created_at.slice(0, 10)}</td>
                <td>
                  <button
                    onClick={() => resetPassword(u)}
                    className="text-xs text-blue-600 hover:underline"
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
  );
}

function tryDecodeId(token: string): number | null {
  try {
    return Number(JSON.parse(atob(token.split(".")[1])).sub) || null;
  } catch {
    return null;
  }
}
