import type { HarvestResult, HarvestedRecord } from "../api/client";

interface HarvestResultsProps {
  results: HarvestResult;
  onSelectRecord: (record: HarvestedRecord) => void;
}

function recordTitle(m: Record<string, string[]>): string {
  return m.title?.[0] || "";
}

function recordCreator(m: Record<string, string[]>): string {
  const c = m.creator || m.creators || m.creatorName || [];
  return c.filter(Boolean).join(", ");
}

export default function HarvestResults({
  results,
  onSelectRecord,
}: HarvestResultsProps) {
  if (results.records.length === 0) {
    return (
      <div className="mt-4">
        <p className="text-sm text-slate-400 text-center py-4">
          No records found for these parameters
        </p>
      </div>
    );
  }

  return (
    <div className="mt-4">
      <p className="text-xs text-slate-500 mb-2 font-medium">
        {results.total} record{results.total !== 1 ? "s" : ""}
      </p>
      <div className="max-h-96 overflow-y-auto divide-y divide-slate-100 border border-slate-200 rounded-lg">
        {results.records.map((record) => {
          const title = recordTitle(record.metadata);
          const creator = recordCreator(record.metadata);
          return (
            <div
              key={record.identifier}
              className="flex items-center justify-between p-3 hover:bg-slate-50 transition-colors"
            >
              <div className="min-w-0 flex-1 pr-2">
                <p className="text-sm font-semibold text-slate-800 truncate">
                  {title || record.identifier}
                </p>
                {creator && (
                  <p className="text-xs text-slate-500 truncate mt-0.5">
                    {creator}
                  </p>
                )}
                <div className="flex items-center gap-2 mt-1 flex-wrap">
                  <span className="text-xs text-slate-400">
                    {record.datestamp}
                  </span>
                  {record.set_spec.map((s) => (
                    <span
                      key={s}
                      className="text-xs bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded"
                    >
                      {s}
                    </span>
                  ))}
                </div>
              </div>
              <button
                onClick={() => onSelectRecord(record)}
                className="ml-3 shrink-0 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 px-3 py-1.5 rounded-lg transition-colors"
              >
                Select
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
