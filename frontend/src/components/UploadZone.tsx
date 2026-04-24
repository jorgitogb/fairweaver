import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { UploadCloud, FileJson } from "lucide-react";

const ACCEPTED: Record<string, string[]> = {
  "application/json": [".json"],
  "application/xml": [".xml"],
  "text/xml": [".xml"],
  "text/csv": [".csv"],
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [
    ".xlsx",
  ],
};

const FORMAT_LABELS: Record<string, string> = {
  ".json": "ISA-JSON / RO-Crate",
  ".xml": "DataCite XML",
  ".csv": "Darwin Core CSV",
  ".xlsx": "MIAPPE XLSX",
};

interface Props {
  onFileAccepted: (file: File) => void;
  disabled?: boolean;
}

export default function UploadZone({
  onFileAccepted,
  disabled = false,
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
      maxSize: 10 * 1024 * 1024,
      disabled,
    });

  return (
    <div
      {...getRootProps()}
      className={`
        border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all
        ${isDragActive ? "border-emerald-400 bg-emerald-50" : "border-slate-300 hover:border-emerald-400 hover:bg-slate-50"}
        ${isDragReject ? "border-red-400 bg-red-50" : ""}
        ${disabled ? "opacity-50 cursor-not-allowed" : ""}
      `}
    >
      <input {...getInputProps()} />
      <UploadCloud
        className={`mx-auto mb-3 w-10 h-10 ${isDragActive ? "text-emerald-500" : "text-slate-400"}`}
      />
      {isDragActive ? (
        <p className="text-emerald-600 font-medium">Drop it here…</p>
      ) : (
        <>
          <p className="text-slate-600 font-medium mb-1">
            Drag & drop a metadata file, or click to browse
          </p>
          <p className="text-slate-400 text-sm">Max 10 MB</p>
        </>
      )}
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
    </div>
  );
}
