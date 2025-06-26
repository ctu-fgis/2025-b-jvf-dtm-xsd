#!/usr/bin/env python3
"""
pokus.py

A console tool that:
1. Unpacks the ZIP into a temp folder, finds the “main” XSD, and checks imported vs. actual .xsd files.
2. Prints warnings for any Missing or Unreferenced schemas.
3. Extracts summary <element> references into a CSV.
4. Builds a detailed CSV based on a JSON config.
"""

# Imports
import zipfile
import pandas as pd
import json
from pathlib import Path
from lxml import etree
import tempfile
import argparse
import sys

# Function to normalize paths
def normalize_path(p: str) -> str:
    """
    Remove leading '../' segments and 'xsd/' prefix from a POSIX-style path.
    """
    while p.startswith("../"):
        p = p[3:]
    if p.startswith("xsd/"):
        p = p[4:]
    return p

def test_imported_xsd(zip_path: Path):
    """
    Unpack the ZIP, locate main XSD (input_data.xsd or index_data.xsd),
    perform the notebook‐style import-vs-disk check, and print warnings.
    """
    with tempfile.TemporaryDirectory() as tmpdir_str:
        output_path = Path(tmpdir_str)
        # 1) Extract ZIP
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(output_path)

        # 2) Locate main XSD
        candidates = list(output_path.rglob("input_data.xsd")) + \
                     list(output_path.rglob("index_data.xsd"))
        if not candidates:
            raise FileNotFoundError("Neither 'input_data.xsd' nor 'index_data.xsd' found.")
        xsd_path = candidates[0]
        print(f"Found main XSD: {xsd_path.relative_to(output_path)}", file=sys.stderr)

        # 3) Parse imports/includes
        tree = etree.parse(str(xsd_path))
        ns = {"xs": "http://www.w3.org/2001/XMLSchema"}
        raw_imports = {
            el.get("schemaLocation")
            for tag in ("import", "include")
            for el in tree.getroot().findall(f".//xs:{tag}", namespaces=ns)
            if el.get("schemaLocation")
        }

        # 4) Normalize and collect sets
        imported = { normalize_path(Path(loc).as_posix()) for loc in raw_imports }
        all_files = {
            normalize_path(p.relative_to(output_path).as_posix())
            for p in output_path.rglob("*.xsd")
        }

        # 5) Compare and warn
        for path in sorted(imported.union(all_files)):
            if   path in imported and path in all_files:
                status = "OK"
            elif path in imported:
                status = "Missing"
            else:
                status = "Unreferenced"

            if status != "OK":
                print(f"Warning: {path} → {status}", file=sys.stderr)


# ... your existing extract_and_process and create_detailed_csv definitions here ...


# CLI entrypoint
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract <element> refs + test imported XSD schemas."
    )
    parser.add_argument("--input",    type=Path, required=True,
                        help="Path to ZIP archive.")
    parser.add_argument("--summary",  type=Path, required=True,
                        help="Path to summary CSV.")
    parser.add_argument("--detailed", type=Path, required=True,
                        help="Path to detailed CSV.")
    parser.add_argument("--config",   type=Path, required=True,
                        help="JSON config file.")
    args = parser.parse_args()

    # just a single call instead of inline block
    test_imported_xsd(args.input)

    # then the CSV routines
    extract_and_process(args.input,   args.summary)
    create_detailed_csv(args.input,   args.detailed,  args.config)
