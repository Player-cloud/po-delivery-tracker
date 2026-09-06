import { URGENCY, UrgencyKey } from "@/lib/urgency";
import { card } from "@/lib/ui";

// Composition bar: how the open PO lines split across urgency buckets.
// One bar, four segments, 2px surface gaps, legend below with counts.
const ORDER: { key: Exclude<UrgencyKey, "delivered">; field: string }[] = [
  { key: "overdue", field: "overdue" },
  { key: "today", field: "due_today" },
  { key: "soon", field: "due_soon" },
  { key: "later", field: "later" },
];

export default function UrgencyBar({ counts }: { counts: Record<string, number> }) {
  const total = ORDER.reduce((n, s) => n + (counts[s.field] ?? 0), 0);

  return (
    <div className={`${card} p-4 sm:p-[18px]`}>
      <p className="mb-3 text-xs text-muted">
        Open lines by urgency <span className="text-faint">({total})</span>
      </p>

      {total === 0 ? (
        <p className="text-sm text-faint">No open lines.</p>
      ) : (
        <div className="flex h-[15px] w-full gap-[3px] overflow-hidden rounded-[7px]">
          {ORDER.map((s) => {
            const value = counts[s.field] ?? 0;
            if (value === 0) return null;
            return (
              <div
                key={s.key}
                className={`${URGENCY[s.key].bar} animate-grow-x min-w-[3px]`}
                style={{ width: `${(value / total) * 100}%` }}
                title={`${URGENCY[s.key].label}: ${value}`}
              />
            );
          })}
        </div>
      )}

      <ul className="mt-3.5 flex flex-wrap gap-x-5 gap-y-2 text-xs">
        {ORDER.map((s) => (
          <li key={s.key} className="flex items-center gap-2">
            <span className={`h-2.5 w-2.5 rounded-full ${URGENCY[s.key].dot}`} aria-hidden />
            <span className="text-muted">{URGENCY[s.key].label}</span>
            <span className="font-semibold tabular-nums">{counts[s.field] ?? 0}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
