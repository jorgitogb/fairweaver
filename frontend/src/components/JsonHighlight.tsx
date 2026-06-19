import { Fragment } from "react";

function indent(n: number): string {
  return "  ".repeat(n);
}

export default function JsonHighlight({ data, depth = 0 }: { data: unknown; depth?: number }) {
  if (data === null || data === undefined) {
    return <span className="text-slate-500">null</span>;
  }
  if (typeof data === "boolean") {
    return <span className="text-purple-300">{String(data)}</span>;
  }
  if (typeof data === "number") {
    return <span className="text-amber-300">{String(data)}</span>;
  }
  if (typeof data === "string") {
    return <span className="text-emerald-300">"{data}"</span>;
  }
  if (Array.isArray(data)) {
    if (data.length === 0) return <span className="text-slate-400">[]</span>;
    return (
      <>
        <span className="text-slate-400">[{"\n"}</span>
        {data.map((item, i) => (
          <Fragment key={i}>
            {indent(depth + 1)}
            <JsonHighlight data={item} depth={depth + 1} />
            {i < data.length - 1 && <span className="text-slate-400">,</span>}
            {"\n"}
          </Fragment>
        ))}
        {indent(depth)}
        <span className="text-slate-400">]</span>
      </>
    );
  }
  if (typeof data === "object") {
    const entries = Object.entries(data as Record<string, unknown>);
    if (entries.length === 0) return <span className="text-slate-400">{`{}`}</span>;
    return (
      <>
        <span className="text-slate-400">{`{`}</span>
        {"\n"}
        {entries.map(([key, val], i) => (
          <Fragment key={key}>
            {indent(depth + 1)}
            <span className="text-sky-300">"{key}"</span>
            <span className="text-slate-400">: </span>
            <JsonHighlight data={val} depth={depth + 1} />
            {i < entries.length - 1 && <span className="text-slate-400">,</span>}
            {"\n"}
          </Fragment>
        ))}
        {indent(depth)}
        <span className="text-slate-400">{`}`}</span>
      </>
    );
  }
  return <span>{String(data)}</span>;
}
