import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import ArcHierarchyTree from "../../src/components/ArcHierarchyTree";

const mockGraph = [
  {
    "@id": "./",
    "@type": "Dataset",
    additionalType: "Investigation",
    name: "Test Investigation",
    hasPart: [
      { "@id": "#Study_test" },
      { "@id": "#Assay_test" },
    ],
  },
  {
    "@id": "#Study_test",
    "@type": "Dataset",
    additionalType: "Study",
    name: "Test Study",
    about: [{ "@id": "#Process_test" }],
  },
  {
    "@id": "#Assay_test",
    "@type": "Dataset",
    additionalType: "Assay",
    name: "Test Assay",
    measurementMethod: { "@id": "https://example.org/DefinedTerm" },
  },
  {
    "@id": "#Process_test",
    "@type": "LabProcess",
    name: "Test Process",
    object: { "@id": "#Material_test" },
  },
  {
    "@id": "#Material_test",
    "@type": "Sample",
    additionalType: "Material",
    name: "Test Material",
    additionalProperty: [{ "@id": "#PropValue_test" }],
  },
  {
    "@id": "#PropValue_test",
    "@type": "PropertyValue",
    additionalType: "CharacteristicValue",
    name: "Organism",
    value: "Solanum tuberosum",
  },
  {
    "@id": "https://example.org/DefinedTerm",
    "@type": "DefinedTerm",
    name: "digital camera",
    termCode: "OBI:0001048",
  },
];

describe("ArcHierarchyTree", () => {
  it("renders root investigation", () => {
    render(<ArcHierarchyTree graph={mockGraph} />);
    expect(screen.getAllByText("Test Investigation").length).toBeGreaterThan(0);
  });

  it("renders Investigation → hasPart → Assay", () => {
    render(<ArcHierarchyTree graph={mockGraph} />);
    expect(screen.getAllByText("Test Assay").length).toBeGreaterThan(0);
  });

  it("renders Investigation → hasPart → Study", () => {
    render(<ArcHierarchyTree graph={mockGraph} />);
    expect(screen.getAllByText("Test Study").length).toBeGreaterThan(0);
  });

  it("renders Assay → measurementMethod → DefinedTerm", () => {
    render(<ArcHierarchyTree graph={mockGraph} />);
    expect(screen.getByText("digital camera")).toBeInTheDocument();
  });

  it("renders Study → about → LabProcess", () => {
    render(<ArcHierarchyTree graph={mockGraph} />);
    expect(screen.getByText("Test Process")).toBeInTheDocument();
  });

  it("renders LabProcess → object → Sample/Material", () => {
    render(<ArcHierarchyTree graph={mockGraph} />);
    fireEvent.click(screen.getByText("Test Process"));
    expect(screen.getByText("Test Material")).toBeInTheDocument();
  });

  it("renders Sample → additionalProperty → PropertyValue", () => {
    render(<ArcHierarchyTree graph={mockGraph} />);
    fireEvent.click(screen.getByText("Test Process"));
    fireEvent.click(screen.getByText("Test Material"));
    fireEvent.click(screen.getByText("Organism"));
    expect(screen.getByText("Solanum tuberosum")).toBeInTheDocument();
  });

  it("shows empty state for empty graph", () => {
    render(<ArcHierarchyTree graph={[]} />);
    expect(screen.getByText(/No entities/i)).toBeInTheDocument();
  });
});
