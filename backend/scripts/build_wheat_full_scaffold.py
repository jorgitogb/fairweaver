"""Build a full ARC scaffold (with git init) from the wheat sample RO-Crate.

An ARC is a git repository, so the scaffold is initialised as one.
"""

import json
import os
import struct
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

sys.path.insert(0, str(REPO_ROOT / "backend"))

from arc_scaffold_builder import build_scaffold_from_rocrate
from arctrl import XlsxController

INPUT = REPO_ROOT / "sample-data" / "demo" / "arc-ro-crate-wheat-full.json"

with open(INPUT) as f:
    rocrate = json.load(f)

graph = rocrate["@graph"]
investigation = next(e for e in graph if e.get("additionalType") == "Investigation")

folder_name = investigation["name"]
OUTPUT = REPO_ROOT / "sample-data" / "demo" / folder_name

print(f"Building ARC scaffold: {folder_name}")
print(f"Output: {OUTPUT}")

OUTPUT.mkdir(parents=True, exist_ok=True)
build_scaffold_from_rocrate(rocrate, OUTPUT)

# Print tree
print(f"\nFiles ({sum(1 for _ in OUTPUT.rglob('*'))} total):")
for path in sorted(OUTPUT.rglob("*")):
    suffix = " (dir)" if path.is_dir() else ""
    print(f"  {path.relative_to(OUTPUT)}{suffix}")

# Read back XLSX for verification
inv = XlsxController.Investigation().from_xlsx_file(str(OUTPUT / "isa.investigation.xlsx"))
print(f"\nIdentifier: {inv.Identifier}  |  Title: {inv.Title}")
print(f"Contacts: {len(inv.Contacts)}")
for c in inv.Contacts:
    print(f"  - {c.FirstName} {c.LastName} <{c.EMail}> ORCID:{c.ORCID}")

# Add sample TIFF data files from the RO-Crate references
dataset_dir = OUTPUT / "assays" / "Assay_wheat" / "dataset"


def make_minimal_tiff():
    entries = {
        256: (3, 1, 1),
        257: (3, 1, 1),
        258: (3, 1, 8),
        259: (3, 1, 1),
        278: (3, 1, 1),
        279: (4, 1, 1),
        339: (3, 1, 1),
    }
    pixel = b"\x00"
    body = b""
    for tag, (typ, count, val) in sorted(entries.items()):
        body += struct.pack("<HHHI", tag, typ, count, val)
    ifd = struct.pack("<H", len(entries)) + body
    strip_off = 8 + len(ifd) + 4
    entries[273] = (4, 1, strip_off)
    body = b""
    for tag, (typ, count, val) in sorted(entries.items()):
        body += struct.pack("<HHHI", tag, typ, count, val)
    ifd = struct.pack("<H", len(entries)) + body + struct.pack("<I", 0)
    return b"II" + struct.pack("<H", 42) + struct.pack("<I", 8) + ifd + pixel


print("\nAdding sample TIFF data files...")
for i in range(1, 4):
    path = dataset_dir / f"sample{i}.tiff"
    path.write_bytes(make_minimal_tiff())
    print(f"  Created {path.name} ({path.stat().st_size} bytes)")

# Initialise as a git repository with proper ARC conventions
print("\nInitialising git repository...")
subprocess.run(["git", "init", "-b", "main"], cwd=OUTPUT, check=True, capture_output=True)
subprocess.run(
    ["git", "config", "user.name", "FAIRweaver"], cwd=OUTPUT, check=True, capture_output=True
)
subprocess.run(
    ["git", "config", "user.email", "dev@fairweaver.local"],
    cwd=OUTPUT,
    check=True,
    capture_output=True,
)
subprocess.run(["git", "add", "."], cwd=OUTPUT, check=True, capture_output=True)
subprocess.run(
    ["git", "commit", "-m", "Initial ARC scaffold"],
    cwd=OUTPUT,
    check=True,
    capture_output=True,
)
print("Done.")
