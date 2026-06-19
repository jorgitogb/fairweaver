import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import HarvestZone from "../../src/components/HarvestZone";
import type { HarvestConvertRequest } from "../../src/api/client";

const { mockListSets } = vi.hoisted(() => ({
  mockListSets: vi.fn(),
}));

vi.mock("../../src/api/client", async () => {
  const actual = await vi.importActual("../../src/api/client");
  return { ...actual, listSets: mockListSets };
});

const fakeSets = [
  { spec: "public", name: "Public datasets" },
  { spec: "restricted", name: "Restricted datasets" },
  { spec: "doc-type:ResearchData", name: "research data" },
];

describe("HarvestZone", () => {
  it("renders URL input, prefix dropdown, and harvest button", () => {
    render(
      <HarvestZone
        onHarvest={() => {}}
        isHarvesting={false}
        harvestError={null}
      />
    );
    expect(screen.getByPlaceholderText(/pangaea/i)).toBeInTheDocument();
    expect(screen.getByText(/harvest/i)).toBeInTheDocument();
  });

  it("disables harvest button when URL is empty", () => {
    render(
      <HarvestZone
        onHarvest={() => {}}
        isHarvesting={false}
        harvestError={null}
      />
    );
    const btn = screen.getByRole("button", { name: /harvest/i });
    expect(btn).toBeDisabled();
  });

  it("enables harvest button when URL is filled", async () => {
    const user = userEvent.setup();
    render(
      <HarvestZone
        onHarvest={() => {}}
        isHarvesting={false}
        harvestError={null}
      />
    );
    const input = screen.getByPlaceholderText(/pangaea/i);
    await user.type(input, "https://example.org/oai");
    const btn = screen.getByRole("button", { name: /harvest/i });
    expect(btn).not.toBeDisabled();
  });

  it("calls onHarvest with correct params on submit", async () => {
    const user = userEvent.setup();
    const onHarvest = vi.fn<HarvestConvertRequest>();
    render(
      <HarvestZone
        onHarvest={onHarvest}
        isHarvesting={false}
        harvestError={null}
      />
    );
    await user.type(screen.getByPlaceholderText(/pangaea/i), "https://example.org/oai");
    await user.click(screen.getByRole("button", { name: /harvest/i }));
    expect(onHarvest).toHaveBeenCalledWith({
      base_url: "https://example.org/oai",
      metadata_prefix: "oai_dc",
      pivot_id: "fairagro_searchhub",
    });
  });

  it("shows spinner while harvesting", () => {
    render(
      <HarvestZone
        onHarvest={() => {}}
        isHarvesting={true}
        harvestError={null}
      />
    );
    expect(screen.getByText(/harvesting/i)).toBeInTheDocument();
  });

  it("shows error message when harvestError is set", () => {
    render(
      <HarvestZone
        onHarvest={() => {}}
        isHarvesting={false}
        harvestError="Connection refused"
      />
    );
    expect(screen.getByText(/connection refused/i)).toBeInTheDocument();
  });
});

describe("HarvestZone Browse Sets", () => {
  beforeEach(() => {
    mockListSets.mockReset();
  });

  it("renders Browse button", () => {
    render(
      <HarvestZone
        onHarvest={() => {}}
        isHarvesting={false}
        harvestError={null}
        results={null}
        onSelectRecord={() => {}}
      />
    );
    expect(screen.getByText("Browse")).toBeInTheDocument();
  });

  it("disables Browse button when URL is empty", () => {
    render(
      <HarvestZone
        onHarvest={() => {}}
        isHarvesting={false}
        harvestError={null}
        results={null}
        onSelectRecord={() => {}}
      />
    );
    const btn = screen.getByText("Browse").closest("button");
    expect(btn).toBeDisabled();
  });

  it("enables Browse button when URL is filled", async () => {
    const user = userEvent.setup();
    render(
      <HarvestZone
        onHarvest={() => {}}
        isHarvesting={false}
        harvestError={null}
        results={null}
        onSelectRecord={() => {}}
      />
    );
    const input = screen.getByPlaceholderText(/pangaea/i);
    await user.type(input, "https://example.org/oai");
    const btn = screen.getByText("Browse").closest("button");
    expect(btn).not.toBeDisabled();
  });

  it("shows sets dropdown after clicking Browse", async () => {
    mockListSets.mockResolvedValue({ sets: fakeSets });
    const user = userEvent.setup();
    render(
      <HarvestZone
        onHarvest={() => {}}
        isHarvesting={false}
        harvestError={null}
        results={null}
        onSelectRecord={() => {}}
      />
    );
    await user.type(screen.getByPlaceholderText(/pangaea/i), "https://example.org/oai");
    await user.click(screen.getByText("Browse"));
    await waitFor(() => {
      expect(screen.getByText("research data")).toBeInTheDocument();
    });
    expect(screen.getByText("public")).toBeInTheDocument();
    expect(screen.getByText("restricted")).toBeInTheDocument();
  });

  it("fills setSpec when a set is selected", async () => {
    mockListSets.mockResolvedValue({ sets: fakeSets });
    const user = userEvent.setup();
    render(
      <HarvestZone
        onHarvest={() => {}}
        isHarvesting={false}
        harvestError={null}
        results={null}
        onSelectRecord={() => {}}
      />
    );
    await user.type(screen.getByPlaceholderText(/pangaea/i), "https://example.org/oai");
    await user.click(screen.getByText("Browse"));
    await waitFor(() => {
      expect(screen.getByText("research data")).toBeInTheDocument();
    });
    await user.click(screen.getByText("research data"));
    const setInput = screen.getByPlaceholderText("citable");
    expect(setInput).toHaveValue("doc-type:ResearchData");
  });

  it("shows error message on fetch failure", async () => {
    mockListSets.mockRejectedValue(new Error("Network error"));
    const user = userEvent.setup();
    render(
      <HarvestZone
        onHarvest={() => {}}
        isHarvesting={false}
        harvestError={null}
        results={null}
        onSelectRecord={() => {}}
      />
    );
    await user.type(screen.getByPlaceholderText(/pangaea/i), "https://example.org/oai");
    await user.click(screen.getByText("Browse"));
    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });
  });

  it("shows no-sets message when repository returns empty sets", async () => {
    mockListSets.mockResolvedValue({ sets: [] });
    const user = userEvent.setup();
    render(
      <HarvestZone
        onHarvest={() => {}}
        isHarvesting={false}
        harvestError={null}
        results={null}
        onSelectRecord={() => {}}
      />
    );
    await user.type(screen.getByPlaceholderText(/pangaea/i), "https://example.org/oai");
    await user.click(screen.getByText("Browse"));
    await waitFor(() => {
      expect(screen.getByText(/No sets available/i)).toBeInTheDocument();
    });
  });

  it("shows filter input inside dropdown", async () => {
    mockListSets.mockResolvedValue({ sets: fakeSets });
    const user = userEvent.setup();
    render(
      <HarvestZone
        onHarvest={() => {}}
        isHarvesting={false}
        harvestError={null}
        results={null}
        onSelectRecord={() => {}}
      />
    );
    await user.type(screen.getByPlaceholderText(/pangaea/i), "https://example.org/oai");
    await user.click(screen.getByText("Browse"));
    await waitFor(() => {
      expect(screen.getByPlaceholderText("Filter sets...")).toBeInTheDocument();
    });
  });

  it("filters sets by spec when typing in filter input", async () => {
    mockListSets.mockResolvedValue({ sets: fakeSets });
    const user = userEvent.setup();
    render(
      <HarvestZone
        onHarvest={() => {}}
        isHarvesting={false}
        harvestError={null}
        results={null}
        onSelectRecord={() => {}}
      />
    );
    await user.type(screen.getByPlaceholderText(/pangaea/i), "https://example.org/oai");
    await user.click(screen.getByText("Browse"));
    await waitFor(() => {
      expect(screen.getByPlaceholderText("Filter sets...")).toBeInTheDocument();
    });
    const filterInput = screen.getByPlaceholderText("Filter sets...");
    await user.type(filterInput, "doc");
    expect(screen.getByText(/doc-type:ResearchData/i)).toBeInTheDocument();
    expect(screen.queryByText(/^public$/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/^restricted$/i)).not.toBeInTheDocument();
  });

  it("filters sets by name when typing in filter input", async () => {
    mockListSets.mockResolvedValue({ sets: fakeSets });
    const user = userEvent.setup();
    render(
      <HarvestZone
        onHarvest={() => {}}
        isHarvesting={false}
        harvestError={null}
        results={null}
        onSelectRecord={() => {}}
      />
    );
    await user.type(screen.getByPlaceholderText(/pangaea/i), "https://example.org/oai");
    await user.click(screen.getByText("Browse"));
    await waitFor(() => {
      expect(screen.getByPlaceholderText("Filter sets...")).toBeInTheDocument();
    });
    const filterInput = screen.getByPlaceholderText("Filter sets...");
    await user.type(filterInput, "research");
    expect(screen.getByText("research data")).toBeInTheDocument();
    expect(screen.queryByText(/^public$/i)).not.toBeInTheDocument();
  });

  it("shows 'No matching sets' when filter yields empty", async () => {
    mockListSets.mockResolvedValue({ sets: fakeSets });
    const user = userEvent.setup();
    render(
      <HarvestZone
        onHarvest={() => {}}
        isHarvesting={false}
        harvestError={null}
        results={null}
        onSelectRecord={() => {}}
      />
    );
    await user.type(screen.getByPlaceholderText(/pangaea/i), "https://example.org/oai");
    await user.click(screen.getByText("Browse"));
    await waitFor(() => {
      expect(screen.getByPlaceholderText("Filter sets...")).toBeInTheDocument();
    });
    const filterInput = screen.getByPlaceholderText("Filter sets...");
    await user.type(filterInput, "zzzznotexist");
    expect(screen.getByText("No matching sets")).toBeInTheDocument();
  });

  it("closes dropdown when close button clicked", async () => {
    mockListSets.mockResolvedValue({ sets: fakeSets });
    const user = userEvent.setup();
    render(
      <HarvestZone
        onHarvest={() => {}}
        isHarvesting={false}
        harvestError={null}
        results={null}
        onSelectRecord={() => {}}
      />
    );
    await user.type(screen.getByPlaceholderText(/pangaea/i), "https://example.org/oai");
    await user.click(screen.getByText("Browse"));
    await waitFor(() => {
      expect(screen.getByPlaceholderText("Filter sets...")).toBeInTheDocument();
    });
    const closeBtn = document.querySelector('button svg.lucide-x')?.closest('button');
    expect(closeBtn).toBeTruthy();
    if (closeBtn) await user.click(closeBtn);
    await waitFor(() => {
      expect(screen.queryByPlaceholderText("Filter sets...")).not.toBeInTheDocument();
    });
  });
});
