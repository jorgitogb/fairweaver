import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { UploadCloud, FileJson } from "lucide-react";

const ACCEPTED: Record<string, string[]> = {
  "application/json": [".json"],
  "application/xml": [".xml"],
  "text/xml": [".xml"],
  "text/csv": [".csv"],
};

const FORMAT_LABELS: Record<string, string> = {
  ".json": "Schema.org / ARC RO-Crate / ISA-JSON",
  ".xml": "DataCite XML / OAI-PMH DC",
  ".csv": "Darwin Core CSV",
};

interface Props {
  onFileAccepted: (file: File) => void;
  disabled?: boolean;
  compact?: boolean;
}

export default function UploadZone({
  onFileAccepted,
  disabled = false,
  compact = false,
}: Props) {
  const onDrop = useCallback(
    (accepted: File[]) => {
      if (accepted.length > 0) onFileAccepted(accepted[0]);
    },
    [onFileAccepted],
  );

  const { getRootProps, getInputProps, isDragActive, isDragReject } =
    useDropzone({
      onDrop,
      accept: ACCEPTED,
      maxFiles: 1,
      maxSize: 500 * 1024 * 1024,
      disabled,
    });

  return (
    <div
      {...getRootProps()}
      className={`
        border-2 border-dashed rounded-xl text-center cursor-pointer transition-all
        ${compact ? "p-3" : "p-4 sm:p-5 md:p-7"}
        ${isDragActive ? "border-emerald-400 bg-emerald-50" : "border-slate-300 hover:border-emerald-400 hover:bg-slate-50"}
        ${isDragReject ? "border-red-400 bg-red-50" : ""}
        ${disabled ? "opacity-50 cursor-not-allowed" : ""}
      `}
    >
      <input {...getInputProps()} />
      <UploadCloud
        className={`mx-auto ${compact ? "w-4 h-4 mb-0.5" : "w-8 h-8 mb-2"} ${isDragActive ? "text-emerald-500" : "text-slate-400"}`}
      />
      {isDragActive ? (
        <p className="text-emerald-600 font-medium text-sm">Drop it here…</p>
      ) : compact ? (
        <p className="text-slate-500 text-xs">
          Drag or click to replace file
        </p>
      ) : (
        <>
          <p className="text-slate-600 font-medium mb-1">
            Drag & drop a metadata file, or click to browse
          </p>
          <p className="text-slate-400 text-sm">Schema.org, ARC RO-Crate, ISA-JSON, DataCite, OAI-PMH, Darwin Core · Max 500 MB</p>
        </>
      )}
      {!compact && (
        <div className="mt-4 flex flex-wrap justify-center gap-2">
          {Object.entries(FORMAT_LABELS).map(([ext, label]) => (
            <span
              key={ext}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs bg-slate-100 text-slate-500"
            >
              <FileJson className="w-3 h-3" />
              {label}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
