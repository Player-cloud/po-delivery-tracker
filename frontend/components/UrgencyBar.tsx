import { URGENCY, UrgencyKey } from "@/lib/urgency";

// Composition bar: how the open PO lines split across urgency buckets.
// One bar, four segments, 2px surface gaps, legend below with counts.
const ORDER: { key: Exclude<UrgencyKey, "delivered">; field: string }[] = [
  { key: "overdue", field: "overdue" },
  { key: "today", field: "due_today" },
  { key: "soon", field: "due_soon" },
  { key: "later", field: "later" },
];

export default function UrgencyBar({
  counts,
}: {
  counts: Record<string, number>;
}) {
  const total = ORDER.reduce((n, s) => n + (counts[s.field] ?? 0), 0);

  return (
    <div className="rounded border bg-white p-6 shadow">
      <p className="mb-3 text-sm font-medium text-zinc-600">
        Open lines by urgency
        <span className="ml-2 text-zinc-400">({total})</span>
      </p>

      {total === 0 ? (
        <p className="text-sm text-zinc-400">No open lines.</p>
      ) : (
        <div className="flex h-4 w-full gap-[2px] overflow-hidden rounded">
          {ORDER.map((s) => {
            const value = counts[s.field] ?? 0;
            if (value === 0) return null;
            return (
              <div
                key={s.key}
                className={`${URGENCY[s.key].bar} min-w-[3px]`}
                style={{ width: `${(value / total) * 100}%` }}
                title={`${URGENCY[s.key].label}: ${value}`}
              />
            );
          })}
        </div>
      )}

      <ul className="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-sm">
        {ORDER.map((s) => (
          <li key={s.key} className="flex items-center gap-2">
            <span className={`h-2.5 w-2.5 rounded-full ${URGENCY[s.key].dot}`} aria-hidden />
            <span className="text-zinc-600">{URGENCY[s.key].label}</span>
            <span className="font-semibold tabular-nums">{counts[s.field] ?? 0}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
