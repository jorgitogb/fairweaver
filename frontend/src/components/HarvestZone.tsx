import { useState, useCallback, useRef, useEffect, useMemo } from "react";
import { Loader2, Globe, Search, X } from "lucide-react";
import type { HarvestConvertRequest, SetInfo, PivotProfile } from "../api/client";
import { listSets, fetchPivots } from "../api/client";

interface HarvestZoneProps {
  onHarvest: (req: HarvestConvertRequest) => void;
  isHarvesting: boolean;
  harvestError: string | null;
}

export default function HarvestZone({
  onHarvest,
  isHarvesting,
  harvestError,
}: HarvestZoneProps) {
  const [url, setUrl] = useState("");
  const [prefix, setPrefix] = useState<"oai_dc" | "oai_datacite">("oai_dc");
  const [setSpec, setSetSpec] = useState("");
  const [fromDate, setFromDate] = useState("");
  const [untilDate, setUntilDate] = useState("");
  const [pivotId, setPivotId] = useState<string>("fairagro_searchhub");
  const [pivots, setPivots] = useState<PivotProfile[]>([]);
  const [loadingPivots, setLoadingPivots] = useState<boolean>(true);
  const [pivotsError, setPivotsError] = useState<string | null>(null);

  const [availableSets, setAvailableSets] = useState<SetInfo[] | null>(null);
  const [fetchingSets, setFetchingSets] = useState(false);
  const [setsError, setSetsError] = useState<string | null>(null);
  const [setFilter, setSetFilter] = useState("");

  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const loadPivots = async () => {
      try {
        setLoadingPivots(true);
        const { pivots } = await fetchPivots();
        setPivots(pivots);
      } catch (e) {
        console.error("Failed to load pivots:", e);
        setPivotsError(e instanceof Error ? e.message : "Failed to load pivots");
      } finally {
        setLoadingPivots(false);
      }
    };
    loadPivots();
  }, []);

  useEffect(() => {
    if (!availableSets) return;
    const handleClick = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setAvailableSets(null);
        setSetFilter("");
        setSetsError(null);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [availableSets]);

  const closeDropdown = () => {
    setAvailableSets(null);
    setSetFilter("");
    setSetsError(null);
  };

  const filteredSets = useMemo(() => {
    if (!availableSets) return [];
    if (!setFilter.trim()) return availableSets;
    const q = setFilter.toLowerCase();
    return availableSets.filter(
      (s) => s.spec.toLowerCase().includes(q) || s.name.toLowerCase().includes(q)
    );
  }, [availableSets, setFilter]);

  const handleBrowseSets = useCallback(async () => {
    if (!url.trim()) return;
    setFetchingSets(true);
    setSetsError(null);
    setSetFilter("");
    try {
      const result = await listSets(url.trim());
      setAvailableSets(result.sets);
    } catch (e) {
      setSetsError(e instanceof Error ? e.message : "Failed to fetch sets");
      setAvailableSets(null);
    } finally {
      setFetchingSets(false);
    }
  }, [url]);

  const handleSelectSet = (spec: string) => {
    setSetSpec(spec);
    setAvailableSets(null);
    setSetFilter("");
    setSetsError(null);
  };

  const handleSubmit = () => {
    const req: HarvestConvertRequest = {
      base_url: url.trim(),
      metadata_prefix: prefix,
      pivot_id: pivotId,
    };
    if (setSpec) req.set = setSpec;
    if (fromDate) req.from_date = fromDate;
    if (untilDate) req.until_date = untilDate;
    onHarvest(req);
  };

  const canHarvest = url.trim().length > 0 && !isHarvesting;

  return (
    <div className="space-y-4">
      {/* URL input */}
      <div>
        <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">
          OAI-PMH endpoint URL
        </label>
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://ws.pangaea.de/oai/provider"
          className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-emerald-400"
        />
      </div>

       {/* Metadata prefix */}
        <div>
          <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">
            Metadata format
          </label>
          <select
            value={prefix}
            onChange={(e) => setPrefix(e.target.value as "oai_dc" | "oai_datacite")}
            className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-emerald-400"
          >
            <option value="oai_dc">Dublin Core (oai_dc)</option>
            <option value="oai_datacite">DataCite (oai_datacite)</option>
          </select>
        </div>

        {/* Target Pivot */}
        <div>
          <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">
            Target Pivot
          </label>
          {loadingPivots ? (
            <div className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-slate-400" />
              <span className="text-slate-400">Loading pivots...</span>
            </div>
          ) : pivotsError ? (
            <div className="w-full border border-red-300 rounded-lg px-3 py-2 text-sm text-red-600">
              {pivotsError}
            </div>
          ) : (
            <select
              value={pivotId}
              onChange={(e) => setPivotId(e.target.value)}
              className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-emerald-400"
            >
              {pivots.map((pivot) => (
                <option key={pivot.id} value={pivot.id}>
                  {pivot.label}
                </option>
              ))}
            </select>
          )}
        </div>

      {/* Optional fields */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="relative">
          <div className="flex items-center justify-between mb-1">
            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Set
            </label>
              <button
                type="button"
                onClick={handleBrowseSets}
                disabled={!url.trim() || fetchingSets}
                className="text-xs text-emerald-600 hover:text-emerald-700 disabled:text-slate-300 font-medium flex items-center gap-0.5"
              >
              {fetchingSets ? (
                <Loader2 className="w-3 h-3 animate-spin" />
              ) : (
                <Search className="w-3 h-3" />
              )}
              Browse
            </button>
          </div>
          <input
            type="text"
            value={setSpec}
            onChange={(e) => setSetSpec(e.target.value)}
            placeholder="citable"
            className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-emerald-400"
          />
          {availableSets && (
            <div
              ref={dropdownRef}
              className="absolute z-10 mt-1 w-full bg-white border border-slate-200 rounded-lg shadow-lg"
            >
              <div className="flex items-center gap-1 border-b border-slate-100 px-2 py-1.5">
                <Search className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                <input
                  type="text"
                  value={setFilter}
                  onChange={(e) => setSetFilter(e.target.value)}
                  placeholder="Filter sets..."
                  className="w-full text-sm outline-none text-slate-600 placeholder:text-slate-400"
                />
                <button
                  type="button"
                  onClick={closeDropdown}
                  className="text-slate-400 hover:text-slate-600"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
              <div className="max-h-44 overflow-y-auto">
                {filteredSets.length > 0 ? (
                  filteredSets.map((s) => (
                    <button
                      key={s.spec}
                      type="button"
                      onClick={() => handleSelectSet(s.spec)}
                      className="w-full text-left px-3 py-2 text-sm hover:bg-emerald-50 border-b border-slate-100 last:border-b-0"
                    >
                      <span className="font-medium text-slate-700">{s.spec}</span>
                      {s.name && (
                        <span className="text-slate-400 ml-2">{s.name}</span>
                      )}
                    </button>
                  ))
                ) : (
                  <p className="text-xs text-slate-400 text-center py-3">
                    {setFilter.trim() ? "No matching sets" : "No sets available"}
                  </p>
                )}
              </div>
            </div>
          )}
          {setsError && (
            <p className="text-xs text-red-500 mt-1">{setsError}</p>
          )}
        </div>
        <div>
          <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
            From
          </label>
          <input
            type="date"
            value={fromDate}
            onChange={(e) => setFromDate(e.target.value)}
            className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-emerald-400"
          />
        </div>
        <div>
          <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
            Until
          </label>
          <input
            type="date"
            value={untilDate}
            onChange={(e) => setUntilDate(e.target.value)}
            className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-emerald-400"
          />
        </div>
      </div>

      {/* Harvest button */}
      <button
        onClick={handleSubmit}
        disabled={!canHarvest}
        className="w-full flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-60 text-white font-semibold py-3 rounded-xl transition-colors"
      >
        {isHarvesting ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Harvesting…
          </>
        ) : (
          <>
            <Globe className="w-4 h-4" />
            Harvest
          </>
        )}
      </button>

      {/* Error message */}
      {harvestError && (
        <p className="text-red-500 text-sm flex items-center gap-1">
          <span>⚠</span> {harvestError}
        </p>
      )}
    </div>
  );
}
