import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-3 p-8 text-center">
      <p className="text-3xl font-bold">404</p>
      <p className="text-zinc-600">This page could not be found.</p>
      <Link href="/po-lines" className="text-blue-600 hover:underline">
        Go to PO Lines
      </Link>
    </div>
  );
}
