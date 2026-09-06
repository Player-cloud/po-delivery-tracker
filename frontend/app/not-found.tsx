import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-3 p-8 text-center">
      <p className="font-display text-3xl font-bold">404</p>
      <p className="text-muted">This page could not be found.</p>
      <Link href="/po-lines" className="text-accent hover:underline">
        Go to PO Lines
      </Link>
    </div>
  );
}
