import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import HarvestResults from "../../src/components/HarvestResults";

const dcResults = {
  records: [
    {
      identifier: "oai:test:1",
      datestamp: "2023-01-01",
      set_spec: ["public"],
      metadata: {
        title: ["Test Dataset"],
        creator: ["Author One"],
        date: ["2023"],
      },
      metadata_format: "oai_dc",
    },
    {
      identifier: "oai:test:2",
      datestamp: "2023-06-15",
      set_spec: ["restricted"],
      metadata: {
        title: ["Second Dataset"],
        creator: ["Author Two"],
        date: ["2023"],
      },
      metadata_format: "oai_dc",
    },
  ],
  total: 2,
  metadata_format: "oai_dc",
};

describe("HarvestResults", () => {
  it("renders record count badge", () => {
    render(
      <HarvestResults results={dcResults} onSelectRecord={() => {}} />
    );
    expect(screen.getByText(/2 records/i)).toBeInTheDocument();
  });

  it("renders record titles and creators", () => {
    render(
      <HarvestResults results={dcResults} onSelectRecord={() => {}} />
    );
    expect(screen.getByText("Test Dataset")).toBeInTheDocument();
    expect(screen.getByText("Second Dataset")).toBeInTheDocument();
    expect(screen.getByText("Author One")).toBeInTheDocument();
    expect(screen.getByText("Author Two")).toBeInTheDocument();
  });

  it("falls back to identifier when metadata has no title", () => {
    const noTitleResults = {
      records: [
        {
          identifier: "oai:no-title:1",
          datestamp: "2024-01-01",
          set_spec: [],
          metadata: { creator: ["Someone"] },
          metadata_format: "oai_dc",
        },
      ],
      total: 1,
      metadata_format: "oai_dc",
    };
    render(
      <HarvestResults results={noTitleResults} onSelectRecord={() => {}} />
    );
    expect(screen.getByText("oai:no-title:1")).toBeInTheDocument();
  });

  it("works with DataCite-style metadata", () => {
    const dataciteResult = {
      records: [
        {
          identifier: "oai:datacite:1",
          datestamp: "2023-01-01",
          set_spec: ["public"],
          metadata: {
            title: ["DataCite Dataset"],
            creatorName: ["Researcher One", "Researcher Two"],
            publisher: ["Test Publisher"],
            publicationYear: ["2023"],
          },
          metadata_format: "oai_datacite",
        },
      ],
      total: 1,
      metadata_format: "oai_datacite",
    };
    render(
      <HarvestResults results={dataciteResult} onSelectRecord={() => {}} />
    );
    expect(screen.getByText("DataCite Dataset")).toBeInTheDocument();
    expect(screen.getByText("Researcher One, Researcher Two")).toBeInTheDocument();
  });

  it("calls onSelectRecord when Select clicked", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    render(
      <HarvestResults results={dcResults} onSelectRecord={onSelect} />
    );
    const buttons = screen.getAllByRole("button", { name: /select/i });
    await user.click(buttons[0]);
    expect(onSelect).toHaveBeenCalledWith(dcResults.records[0]);
  });

  it("handles empty records array", () => {
    render(
      <HarvestResults
        results={{ records: [], total: 0, metadata_format: "oai_dc" }}
        onSelectRecord={() => {}}
      />
    );
    expect(screen.getByText(/no records found/i)).toBeInTheDocument();
  });
});
