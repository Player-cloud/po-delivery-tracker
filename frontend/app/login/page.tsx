"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { login } from "@/lib/api";
import { saveToken } from "@/lib/auth";
import { btnPrimary, card } from "@/lib/ui";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      saveToken(await login(email, password));
      router.push("/dashboard");
    } catch {
      setError("Login failed — check your email and password.");
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-[80vh] items-center justify-center p-4">
      <form
        onSubmit={handleSubmit}
        className={`${card} animate-rise flex w-full max-w-sm flex-col gap-4 p-8`}
      >
        <div className="flex items-center gap-2.5">
          <span className="h-6 w-6 rounded-lg bg-accent" aria-hidden />
          <span className="font-display text-lg font-semibold">PO Tracker</span>
        </div>
        <h1 className="text-sm text-muted">Sign in to continue</h1>

        <label className="flex flex-col gap-1 text-sm">
          <span className="text-muted">Email</span>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="rounded-[var(--radius-control)] border border-line px-3 py-2 focus:border-accent focus:outline-none"
            required
            autoFocus
          />
        </label>

        <label className="flex flex-col gap-1 text-sm">
          <span className="text-muted">Password</span>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="rounded-[var(--radius-control)] border border-line px-3 py-2 focus:border-accent focus:outline-none"
            required
          />
        </label>

        {error && <p className="text-sm text-overdue-on">{error}</p>}

        <button type="submit" disabled={submitting} className={`${btnPrimary} mt-1`}>
          {submitting ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </div>
  );
}
