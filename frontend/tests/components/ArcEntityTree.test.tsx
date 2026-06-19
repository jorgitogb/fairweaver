import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import ArcEntityTree from "../../src/components/ArcEntityTree";

const mockGraph = [
  {
    "@id": "ro-crate-metadata.json",
    "@type": "CreativeWork",
    conformsTo: "https://w3id.org/ro/crate/1.1",
    about: { "@id": "./" },
  },
  {
    "@id": "./",
    "@type": "Dataset",
    additionalType: "Investigation",
    name: "Wheat Drought Trial 2024",
    description: "Field trial under drought stress",
    identifier: "10.5447/test/001",
    license: "CC-BY-4.0",
    datePublished: "2024-09-15",
  },
  {
    "@id": "#Study_wheat",
    "@type": "Dataset",
    additionalType: "Study",
    name: "Wheat Field Trial",
    description: "Field study description",
    crop_species: "Triticum aestivum",
    crop_species_uri: "http://purl.obolibrary.org/obo/NCBITaxon_4565",
    crop_pest: "Zymoseptoria tritici",
    crop_pest_uri: "http://purl.obolibrary.org/obo/NCBITaxon_5284",
  },
  {
    "@id": "#Assay_wheat",
    "@type": "Dataset",
    additionalType: "Assay",
    name: "Wheat Multispectral imaging",
    measurementTechnique: "Multispectral imaging",
  },
  {
    "@id": "#Mühlhaus_Timo",
    "@type": "Person",
    name: "Timo Mühlhaus",
    email: "timo@rptu.de",
  },
  {
    "@id": "#Organization_RPTU",
    "@type": "Organization",
    name: "RPTU University of Kaiserslautern",
  },
  {
    "@id": "assays/wheat/sample1.tiff",
    "@type": "File",
    name: "Sample 1",
    encodingFormat: "image/tiff",
  },
];

describe("ArcEntityTree", () => {
  it("renders section headers for each entity type", () => {
    render(<ArcEntityTree graph={mockGraph} />);
    expect(screen.getAllByText(/Investigation/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/Study/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/Assay/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/Person/i).length).toBeGreaterThanOrEqual(1);
  });

  it("shows entity names", () => {
    render(<ArcEntityTree graph={mockGraph} />);
    expect(screen.getByText("Wheat Drought Trial 2024")).toBeInTheDocument();
    expect(screen.getByText("Wheat Field Trial")).toBeInTheDocument();
  });

  it("shows crop data when Study is expanded", () => {
    render(<ArcEntityTree graph={mockGraph} />);
    fireEvent.click(screen.getByText("Wheat Field Trial"));
    expect(screen.getByText("Triticum aestivum")).toBeInTheDocument();
  });

  it("shows pest data when Study is expanded", () => {
    render(<ArcEntityTree graph={mockGraph} />);
    fireEvent.click(screen.getByText("Wheat Field Trial"));
    expect(screen.getByText("Zymoseptoria tritici")).toBeInTheDocument();
  });

  it("shows sensor data when Assay is expanded", () => {
    render(<ArcEntityTree graph={mockGraph} />);
    fireEvent.click(screen.getByText("Wheat Multispectral imaging"));
    expect(screen.getByText("Multispectral imaging")).toBeInTheDocument();
  });

  it("renders person name", () => {
    render(<ArcEntityTree graph={mockGraph} />);
    expect(screen.getByText("Timo Mühlhaus")).toBeInTheDocument();
  });

  it("renders organization name", () => {
    render(<ArcEntityTree graph={mockGraph} />);
    expect(screen.getByText("RPTU University of Kaiserslautern")).toBeInTheDocument();
  });

  it("renders file entries", () => {
    render(<ArcEntityTree graph={mockGraph} />);
    expect(screen.getByText("Sample 1")).toBeInTheDocument();
  });

  it("expands entity details on click", () => {
    render(<ArcEntityTree graph={mockGraph} />);
    fireEvent.click(screen.getByText("Wheat Drought Trial 2024"));
    expect(screen.getByText(/10\.5447\/test\/001/)).toBeInTheDocument();
    expect(screen.getByText(/CC-BY-4.0/)).toBeInTheDocument();
  });

  it("collapses expanded entity on second click", () => {
    render(<ArcEntityTree graph={mockGraph} />);
    const node = screen.getByText("Wheat Drought Trial 2024");
    fireEvent.click(node);
    expect(screen.getByText(/10\.5447\/test\/001/)).toBeInTheDocument();
    fireEvent.click(node);
    expect(screen.queryByText(/10\.5447\/test\/001/)).not.toBeInTheDocument();
  });

  it("shows crop field key in details when Study is expanded", () => {
    render(<ArcEntityTree graph={mockGraph} />);
    fireEvent.click(screen.getByText("Wheat Field Trial"));
    expect(screen.getByText("crop_species")).toBeInTheDocument();
  });

  it("shows empty state for empty graph", () => {
    render(<ArcEntityTree graph={[]} />);
    expect(screen.getByText(/No entities/i)).toBeInTheDocument();
  });
});
