"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";

type POLine = {
  id: number;
  po_number: string;
  po_line: number;
  promised_delivery: string;
  days_remaining: number;
  status: string;
  delivered: boolean;
};

export default function POLinesPage() {
  const [lines, setLines] = useState<POLine[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    apiFetch("/po-lines")
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load PO lines");
        return res.json();
      })
      .then((data) => setLines(data))
      .catch(() => setError("Could not load PO lines"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="p-8">Loading...</p>;
  if (error) return <p className="p-8 text-red-600">{error}</p>;

  return (
    <div className="p-8">
      <div className="mb-4 flex justify-between">
        <h1 className="text-xl font-semibold">PO Lines</h1>
        <Link
          href="/po-lines/new"
          className="rounded bg-black px-4 py-2 text-white hover:bg-zinc-800"
        >
          New PO Line
        </Link>
      </div>
      <table className="w-full border-collapse text-left">
        <thead>
          <tr className="border-b">
            <th className="py-2">PO Number</th>
            <th>Line</th>
            <th>Promised Delivery</th>
            <th>Days Remaining</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {lines.map((line) => (
            <tr key={line.id} className="border-b">
              <td className="py-2">{line.po_number}</td>
              <td>{line.po_line}</td>
              <td>{line.promised_delivery}</td>
              <td>{line.days_remaining}</td>
              <td>{line.status}</td>
              <td>
                <Link href={`/po-lines/${line.id}/edit`} className="text-blue-600 hover:underline">
                  Edit
                </Link>
                {" · "}
                <Link
                  href={`/po-lines/${line.id}/request-deletion`}
                  className="text-red-600 hover:underline"
                >
                  Request Deletion
                </Link>
            </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}