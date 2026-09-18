"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { resetPassword } from "@/lib/api";
import { btnPrimary, card } from "@/lib/ui";

const MIN_LENGTH = 10; // keep in step with the API's password_min_length

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<p className="mx-auto max-w-sm p-6 text-muted">Loading…</p>}>
      <ResetPassword />
    </Suspense>
  );
}

function ResetPassword() {
  const token = useSearchParams().get("token");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (password.length < MIN_LENGTH) {
      setError(`Password must be at least ${MIN_LENGTH} characters.`);
      return;
    }
    if (password !== confirm) {
      setError("The two passwords don't match.");
      return;
    }
    setSubmitting(true);
    try {
      await resetPassword(token ?? "", password);
      setDone(true);
    } catch (err) {
      setError(
        err instanceof TypeError
          ? "Can't reach the server — check your connection and try again."
          : err instanceof Error
            ? err.message
            : "Something went wrong — try again.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-[80vh] items-center justify-center p-4">
      <div className={`${card} animate-rise flex w-full max-w-sm flex-col gap-4 p-8`}>
        <div className="flex items-center gap-2.5">
          <span className="h-6 w-6 rounded-lg bg-accent" aria-hidden />
          <span className="font-display text-lg font-semibold">PO Tracker</span>
        </div>

        {done ? (
          <>
            <h1 className="text-sm text-muted">Password updated</h1>
            <p className="text-sm" role="status">
              You can now sign in with your new password.
            </p>
            <Link href="/login" className={btnPrimary}>
              Go to sign in
            </Link>
          </>
        ) : !token ? (
          <>
            <h1 className="text-sm text-muted">Reset link missing</h1>
            <p className="text-sm text-overdue-on">
              This page needs the link from your reset email. Request a new one below.
            </p>
            <Link href="/forgot-password" className={btnPrimary}>
              Request a reset link
            </Link>
          </>
        ) : (
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <h1 className="text-sm text-muted">Choose a new password</h1>

            <label className="flex flex-col gap-1 text-sm">
              <span className="text-muted">New password</span>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="rounded-[var(--radius-control)] border border-line px-3 py-2 focus:border-accent focus:outline-none"
                required
                autoFocus
                autoComplete="new-password"
                minLength={MIN_LENGTH}
              />
              <span className="text-xs text-faint">At least {MIN_LENGTH} characters.</span>
            </label>

            <label className="flex flex-col gap-1 text-sm">
              <span className="text-muted">Confirm new password</span>
              <input
                type="password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                className="rounded-[var(--radius-control)] border border-line px-3 py-2 focus:border-accent focus:outline-none"
                required
                autoComplete="new-password"
              />
            </label>

            {error && (
              <p className="text-sm text-overdue-on" role="alert">
                {error}{" "}
                {/invalid or has expired/.test(error) && (
                  <Link href="/forgot-password" className="underline">
                    Request a new link
                  </Link>
                )}
              </p>
            )}

            <button type="submit" disabled={submitting} className={btnPrimary}>
              {submitting ? "Saving…" : "Set new password"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
