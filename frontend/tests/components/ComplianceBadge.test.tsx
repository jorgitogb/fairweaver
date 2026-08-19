import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import ComplianceBadge from "../../src/components/ComplianceBadge";
import { type ComplianceResult } from "../../src/api/client";

const fullResult: ComplianceResult = {
  level: "full",
  overall_score: 82.5,
  source_format: "schema_org",
  breakdown: {
    required: { present: ["name"], missing: [], score: 100 },
    recommended: { present: [], missing: ["keywords"], score: 50 },
    full: { present: [], missing: ["sensorType"], score: 0 },
  },
};

describe("ComplianceBadge", () => {
  it("renders compliance level and score when result is present", () => {
    render(<ComplianceBadge result={fullResult} />);

    expect(screen.getByText("Full")).toBeInTheDocument();
    expect(screen.getByText("82.5%")).toBeInTheDocument();
  });

  it("renders loading state when loading is true", () => {
    render(<ComplianceBadge loading />);

    expect(screen.getByText("Analyzing…")).toBeInTheDocument();
  });

  it("renders nothing when there is no result and no error", () => {
    const { container } = render(<ComplianceBadge />);

    expect(container).toBeEmptyDOMElement();
  });

  it("renders the error message when an error is provided", () => {
    render(
      <ComplianceBadge
        error="The file contains a JSON array instead of a single object."
      />
    );

    expect(
      screen.getByText("The file contains a JSON array instead of a single object.")
    ).toBeInTheDocument();
  });

  it("prefers showing the error over an empty state when both are present", () => {
    render(<ComplianceBadge error="Something went wrong" />);

    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
  });
});
