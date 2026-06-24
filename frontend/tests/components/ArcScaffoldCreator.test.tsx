import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import ArcScaffoldCreator from "../../src/components/ArcScaffoldCreator";

function wrapper({ children }: { children: React.ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe("ArcScaffoldCreator", () => {
  beforeEach(() => {
    global.URL.createObjectURL = vi.fn(() => "blob:mock");
    global.URL.revokeObjectURL = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders download button", () => {
    render(<ArcScaffoldCreator rocrateFile={new File(["{}"], "ro-crate.json")} />, { wrapper });
    expect(screen.getByText(/Download ARC Scaffold/i)).toBeInTheDocument();
  });

  it("downloads the scaffold on success", async () => {
    const blob = new Blob(["PK"], { type: "application/zip" });
    global.fetch = vi.fn(() =>
      Promise.resolve(new Response(blob, { status: 200, headers: { "content-type": "application/zip" } }))
    ) as unknown as typeof fetch;

    render(<ArcScaffoldCreator rocrateFile={new File(["{}"], "ro-crate.json")} />, { wrapper });

    fireEvent.click(screen.getByText(/Download ARC Scaffold/i));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith("/arc/scaffold", expect.any(Object));
    });

    await waitFor(() => {
      expect(global.URL.createObjectURL).toHaveBeenCalledWith(blob);
    });
  });

  it("shows error message when download fails", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve(new Response(JSON.stringify({ detail: "Bad request" }), { status: 400 }))
    ) as unknown as typeof fetch;

    render(<ArcScaffoldCreator rocrateFile={new File(["{}"], "ro-crate.json")} />, { wrapper });

    fireEvent.click(screen.getByText(/Download ARC Scaffold/i));

    await waitFor(() => {
      expect(screen.getByText("Bad request")).toBeInTheDocument();
    });
  });
});
