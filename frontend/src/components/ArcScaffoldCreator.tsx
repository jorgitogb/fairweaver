import { useMutation } from "@tanstack/react-query";
import { Download, Loader2, AlertTriangle, FolderArchive } from "lucide-react";
import { createArcScaffold } from "../api/client";

export interface ArcScaffoldCreatorProps {
  rocrateFile: File;
  arcName?: string;
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function sanitizeFilename(name: string): string {
  return name.replace(/[^a-zA-Z0-9_-]/g, "_").replace(/_+/g, "_") || "arc";
}

export default function ArcScaffoldCreator({ rocrateFile, arcName }: ArcScaffoldCreatorProps) {
  const mutation = useMutation({
    mutationFn: () => createArcScaffold(rocrateFile),
    onSuccess: (blob) => {
      const baseName = sanitizeFilename(arcName || rocrateFile.name.replace(/\.json$/i, ""));
      downloadBlob(blob, `${baseName}_scaffold.zip`);
    },
  });

  return (
    <div className="rounded-xl border border-emerald-200/60 bg-white/80 backdrop-blur-sm p-5">
      <div className="flex items-start gap-3">
        <div className="mt-0.5 rounded-lg bg-emerald-100 p-2 text-emerald-700">
          <FolderArchive className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-slate-800">Create ARC Scaffold</h3>
          <p className="text-xs text-slate-500 mt-1">
            Generate a full ARC directory structure (studies/, assays/, XLSX files) from this
            RO-Crate metadata.
          </p>

          <button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
            className="mt-4 inline-flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-60 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
          >
            {mutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Generating scaffold…
              </>
            ) : (
              <>
                <Download className="w-4 h-4" />
                Download ARC Scaffold (.zip)
              </>
            )}
          </button>

          {mutation.isError && (
            <p className="mt-3 text-xs text-red-600 flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
              {(mutation.error as Error).message}
            </p>
          )}

          {mutation.isSuccess && !mutation.isPending && (
            <p className="mt-3 text-xs text-emerald-700 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              Scaffold download started.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
