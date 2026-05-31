import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ComparisonView from "../../src/components/ComparisonView";
import type { FieldRule, MissingField } from "../../src/api/client";

const fieldRules: FieldRule[] = [
  { source: "identifier", target: "identifier", required: true, confidence: 0.95, transform: null },
  { source: "title", target: "name", required: true, confidence: 0.95, transform: null },
  { source: null, target: "description", required: true, confidence: 0.0, transform: null },
  { source: null, target: "url", required: true, confidence: 0.0, transform: null },
  { source: null, target: "keywords", required: true, confidence: 0.0, transform: null },
  { source: null, target: "license", required: true, confidence: 0.0, transform: null },
  { source: "creator", target: "creator", required: false, confidence: 0.8, transform: null },
  { source: null, target: "datePublished", required: false, confidence: 0.0, transform: null },
  { source: null, target: "publisher", required: false, confidence: 0.0, transform: null },
  { source: null, target: "version", required: false, confidence: 0.0, transform: null },
];

const missingFields: MissingField[] = [
  { field: "description", level: "minimum", description: "Required" },
  { field: "url", level: "minimum", description: "Required" },
  { field: "keywords", level: "minimum", description: "Required" },
  { field: "license", level: "minimum", description: "Required" },
  { field: "datePublished", level: "recommended", description: "Recommended" },
  { field: "publisher", level: "recommended", description: "Recommended" },
  { field: "version", level: "recommended", description: "Recommended" },
];

const defaultProps = {
  fieldRules,
  missingFields,
  output: { "@context": "https://schema.org", "@type": "Dataset", identifier: "test:1", name: "Test", creator: "Author" },
  confidence: 0.3,
};

describe("ComparisonView", () => {
  it("renders header with coverage badge", () => {
    render(<ComparisonView {...defaultProps} />);
    expect(screen.getByText(/30% coverage/i)).toBeInTheDocument();
  });

  it("shows source fields on the left", () => {
    render(<ComparisonView {...defaultProps} />);
    expect(screen.getByText("Input Fields")).toBeInTheDocument();
    const titleMatches = screen.getAllByText("title");
    expect(titleMatches.length).toBeGreaterThanOrEqual(1);
    const creatorMatches = screen.getAllByText("creator");
    expect(creatorMatches.length).toBeGreaterThanOrEqual(1);
    const idMatches = screen.getAllByText("identifier");
    expect(idMatches.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("3 source fields mapped")).toBeInTheDocument();
  });

  it("shows mapped pivot fields on the right", () => {
    render(<ComparisonView {...defaultProps} />);
    expect(screen.getByText("name")).toBeInTheDocument();
    expect(screen.getByText("Pivot Fields (3/10)")).toBeInTheDocument();
    const idMatches = screen.getAllByText("identifier");
    expect(idMatches.length).toBe(3);
  });

  it("shows missing required fields with MISSING label", () => {
    render(<ComparisonView {...defaultProps} />);
    const matches = screen.getAllByText("MISSING");
    expect(matches.length).toBe(4);
  });

  it("shows missing recommended count badge", () => {
    render(<ComparisonView {...defaultProps} />);
    expect(screen.getByText(/RECOMMENDED — 3 missing/i)).toBeInTheDocument();
  });

  it("reveals missing recommended fields on toggle", async () => {
    const user = userEvent.setup();
    render(<ComparisonView {...defaultProps} />);
    const toggleBtn = screen.getByText(/RECOMMENDED — 3 missing/i);
    await user.click(toggleBtn);
    const matches = screen.getAllByText(/^missing$/);
    expect(matches.length).toBe(3);
  });

  it("toggles to JSON-LD Output tab", async () => {
    const user = userEvent.setup();
    render(<ComparisonView {...defaultProps} />);
    await user.click(screen.getByText("JSON-LD Output"));
    expect(screen.getByText(/"@context"/i)).toBeInTheDocument();
  });

  it("handles empty field rules", () => {
    render(
      <ComparisonView
        fieldRules={[]}
        missingFields={[]}
        output={{}}
        confidence={1}
      />
    );
    expect(screen.getByText(/No source fields mapped/i)).toBeInTheDocument();
    expect(screen.getByText(/No pivot fields defined/i)).toBeInTheDocument();
  });

  it("shows Download button and mapping source badge", () => {
    render(
      <ComparisonView
        {...defaultProps}
        mappingSource="cached"
      />
    );
    expect(screen.getByText("cached")).toBeInTheDocument();
    expect(screen.getByText(/download/i)).toBeInTheDocument();
  });

  it("shows 100% coverage when all fields present", () => {
    const fullRules: FieldRule[] = [
      { source: "id", target: "identifier", required: true, confidence: 0.95, transform: null },
    ];
    render(
      <ComparisonView
        fieldRules={fullRules}
        missingFields={[]}
        output={{ "@type": "Dataset", identifier: "test" }}
        confidence={1}
      />
    );
    expect(screen.getByText(/100% coverage/i)).toBeInTheDocument();
    expect(screen.queryByText(/MISSING/i)).not.toBeInTheDocument();
  });
});
