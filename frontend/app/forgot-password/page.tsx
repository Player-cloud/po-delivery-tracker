"use client";

import { useState } from "react";
import Link from "next/link";
import { requestPasswordReset } from "@/lib/api";
import { btnPrimary, card } from "@/lib/ui";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [sent, setSent] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await requestPasswordReset(email.trim());
      setSent(true);
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

        {sent ? (
          <>
            <h1 className="text-sm text-muted">Check your email</h1>
            <p className="text-sm" role="status">
              If <span className="font-medium">{email.trim()}</span> belongs to an account, we&apos;ve
              sent a link to reset the password. It works once and expires in 30 minutes.
            </p>
            <p className="text-[12.5px] text-muted">
              Nothing after a few minutes? Check spam, or ask your administrator to reset it for
              you.
            </p>
            <Link href="/login" className="text-center text-[12.5px] text-accent hover:underline">
              Back to sign in
            </Link>
          </>
        ) : (
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <h1 className="text-sm text-muted">
              Enter your email and we&apos;ll send you a link to choose a new password.
            </h1>

            <label className="flex flex-col gap-1 text-sm">
              <span className="text-muted">Email</span>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="rounded-[var(--radius-control)] border border-line px-3 py-2 focus:border-accent focus:outline-none"
                required
                autoFocus
                autoComplete="email"
              />
            </label>

            {error && <p className="text-sm text-overdue-on">{error}</p>}

            <button type="submit" disabled={submitting} className={btnPrimary}>
              {submitting ? "Sending…" : "Send reset link"}
            </button>

            <Link href="/login" className="text-center text-[12.5px] text-muted hover:text-accent">
              Back to sign in
            </Link>
          </form>
        )}
      </div>
    </div>
  );
}
