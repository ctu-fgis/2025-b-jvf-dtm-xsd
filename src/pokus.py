#!/usr/bin/env python3
"""
pokus.py

A console tool that:
1. Auto-detects the “main” XSD in the archive, checks imported vs. actual XSD files, and prints warnings.
2. Extracts summary <element> references into a CSV.
3. Builds a detailed CSV based on a JSON config.
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

def normalize_path(p: str) -> str:
    """
    Remove leading '../' segments and 'xsd/' prefix from a POSIX-style path.
    """
    while p.startswith("../"):
        p = p[3:]
    if p.startswith("xsd/"):
        p = p[4:]
    return p

def check_imports(main_xsd: Path, xsd_root: Path):
    """
    Parse main_xsd for <xs:import> and <xs:include>, normalize them,
    scan xsd_root for all .xsd, normalize those, and return list of (path, status).
    """
    tree = etree.parse(str(main_xsd))
    ns = {"xs": "http://www.w3.org/2001/XMLSchema"}
    raw_imports = {
        el.get("schemaLocation")
        for tag in ("import", "include")
        for el in tree.getroot().findall(f".//xs:{tag}", namespaces=ns)
        if el.get("schemaLocation")
    }
    imported = { normalize_path(Path(loc).as_posix()) for loc in raw_imports }
    all_files = {
        normalize_path(p.relative_to(xsd_root).as_posix())
        for p in xsd_root.rglob("*.xsd")
    }

    results = []
    for path in sorted(imported.union(all_files)):
        in_imp  = path in imported
        on_disk = path in all_files
        status = (
            "OK"            if in_imp and on_disk else
            "Missing"       if in_imp and not on_disk else
            "Unreferenced"
        )
        results.append((path, status))
    return results

def find_main_xsd(xsd_root: Path) -> Path:
    """
    Pick the file under xsd_root not imported by any other.
    If none or multiple, warn and pick the first.
    """
    ns = {"xs": "http://www.w3.org/2001/XMLSchema"}
    all_paths = []
    imported_all = set()

    for p in xsd_root.rglob("*.xsd"):
        rel = normalize_path(p.relative_to(xsd_root).as_posix())
        all_paths.append((rel, p))
        try:
            tree = etree.parse(str(p))
            for tag in ("import", "include"):
                for el in tree.getroot().findall(f".//xs:{tag}", namespaces=ns):
                    loc = el.get("schemaLocation")
                    if loc:
                        imported_all.add(normalize_path(Path(loc).as_posix()))
        except Exception as e:
            print(f"Warning: failed to parse {p.name}: {e}", file=sys.stderr)

    file_set = {rel for rel, _ in all_paths}
    candidates = sorted(file_set - imported_all)

    if len(candidates) == 1:
        chosen = candidates[0]
    elif len(candidates) > 1:
        chosen = candidates[0]
        print(f"Warning: multiple main candidates {candidates}, using {chosen}", file=sys.stderr)
    else:
        chosen = sorted(file_set)[0]
        print(f"Warning: no unreferenced XSD, defaulting to {chosen}", file=sys.stderr)

    return xsd_root / chosen

# Function to load and parse all .xsd files in a directory
def load_xsd_files(directory: Path):
    xsd_files = []
    for path in directory.rglob("*.xsd"):
        try:
            tree = etree.parse(str(path))
            xsd_files.append((path.name, tree.getroot()))
        except etree.XMLSyntaxError as e:
            print(f"[XMLSyntaxError] Skipping {path.name}: {e}")
        except Exception as e:
            print(f"[Error] Could not process {path.name}: {e}")
            raise
    return xsd_files

# Main function to handle ZIP -> parse -> CSV
def extract_and_process(zip_path: Path, output_csv: Path):
    records = []
    seen_global = set()

    with tempfile.TemporaryDirectory() as tmpdir_str:
        tmpdir = Path(tmpdir_str)
        # Extract ZIP archive
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmpdir)

        xsd_objects_path = tmpdir / "xsd" / "objekty"

        for file_path in xsd_objects_path.glob("*.xsd"):
            try:
                tree = etree.parse(str(file_path))
                root = tree.getroot()

                complex_types = root.xpath(".//*[local-name()='complexType']")

                for complex_type in complex_types:
                    atr_normal = []
                    atr_ki = []
                    gml_refs = []
                    gml_min_flags = []
                    atr_ki_with_0 = False

                    for element in complex_type.xpath(".//*[local-name()='element']"):
                        ref = element.get("ref")
                        min_occurs = element.get("minOccurs")

                        if not ref:
                            continue

                        key = (file_path.name, ref)
                        if key in seen_global:
                            continue
                        seen_global.add(key)

                        if ref.startswith("atr:"):
                            entry = {
                                "filename": file_path.name,
                                "nazev": ref,
                                "minOccurs": min_occurs
                            }
                            if ref.endswith("KI"):
                                atr_ki.append(entry)
                                if min_occurs == "0":
                                    atr_ki_with_0 = True
                            else:
                                atr_normal.append(entry)

                        elif ref.startswith("gml:"):
                            gml_refs.append(ref)
                            gml_min_flags.append(min_occurs)

                    records.extend(atr_normal)

                    if gml_refs:
                        min_occurs_final = "0" if "0" in gml_min_flags or atr_ki_with_0 else None
                        records.append({
                            "filename": file_path.name,
                            "nazev": str(gml_refs),
                            "minOccurs": min_occurs_final
                        })

                    records.extend(atr_ki)

            except etree.XMLSyntaxError as e:
                print(f"[XMLSyntaxError] {file_path.name}: {e}")
            except Exception as e:
                print(f"[Error] Failed to process {file_path.name}: {e}")
                raise

    df = pd.DataFrame(records)
    df.to_csv(output_csv, index=False, encoding="utf-8")
    print(f"Saved {len(df)} rows to {output_csv}")

def create_detailed_csv(zip_path: Path, output_detailed_csv: Path, input_config: Path):
    # Load JSON config
    with open(input_config, "r", encoding="utf-8") as f:
        config = json.load(f)

    with tempfile.TemporaryDirectory() as tmpdir_str:
        tmpdir = Path(tmpdir_str)
        # Extract ZIP archive
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmpdir)

        xsd_objects_path = tmpdir / "xsd" / "objekty"
        records = []
        output_fields = config["output_fields"]
        element_rules = config["element_types"]

        for file_path in xsd_objects_path.glob("*.xsd"):
            try:
                tree = etree.parse(str(file_path))
                root = tree.getroot()
                namespace = root.attrib.get("targetNamespace", "")

                data = {key: "" for key in output_fields}
                data["filename"] = file_path.name
                data["namespace"] = namespace
                data["zaznamy"] = []
                data["OblastObjektuKI"] = 0

                # Get top-level element
                top_level_elems = root.xpath(
                    f"./*[local-name()='element' and starts-with(@type, '{namespace}:')]"
                )
                if top_level_elems:
                    main_elem = top_level_elems[0]
                    data["name"] = main_elem.get("name", "")
                    data["type"] = main_elem.get("type", "")

                # Iterate through all complex types
                complex_types = root.xpath(".//*[local-name()='complexType']")
                for complex_type in complex_types:
                    for element in complex_type.xpath(".//*[local-name()='element']"):
                        name = element.get("name")
                        ref = element.get("ref")
                        min_occurs = element.get("minOccurs")
                        match = None
                        etype = None
                        clean_ref = None

                        # Determine element rule
                        if name in element_rules:
                            etype = element_rules[name]
                            match = "name"
                        elif ref in element_rules:
                            etype = element_rules[ref]
                            match = "ref"
                            clean_ref = ref.split(":")[-1]
                        else:
                            continue

                        # Handle configured attributes
                        if "attributes" in etype:
                            for attr_name, props in etype["attributes"].items():
                                for prop in props:
                                    if match == "name":
                                        val = element.xpath(
                                            f".//*[local-name()='attribute' and @name='{attr_name}']/@{prop}"
                                        )
                                    else:
                                        val = element.xpath(
                                            f".//*[local-name()='attribute' and @ref='{attr_name}']/@{prop}"
                                        )
                                    if val:
                                        data[f"{attr_name}_{prop}"] = val[0]

                        # Handle direct element properties
                        true_flags = [
                            key for key, value in etype.items()
                            if value is True and key != "geometry"
                        ]
                        for flag in true_flags:
                            val = element.get(flag)
                            if val is not None:
                                if flag == "minOccurs":
                                    data[f"{clean_ref}_{flag}"] = val
                                    data[clean_ref] = 1
                                else:
                                    data[name if match=="name" else ref] = val

                        # Handle geometry flag
                        if etype.get("geometry") is True:
                            data["geom_minOccurs"] = min_occurs
                            ref_elem = element.xpath(".//*[local-name()='element' and @ref]")
                            data["geometry"] = [g.get("ref") for g in ref_elem]

                records.append(data)

            except Exception as e:
                print(f"[Error] {file_path.name}: {e}")
                raise

        df = pd.DataFrame(records)
        df.to_csv(output_detailed_csv, index=False, encoding="utf-8")
        print(f"Saved {len(df)} rows to {output_detailed_csv}")

# CLI entrypoint
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Unpack XSD ZIP, check imports, and extract element refs to CSV."
    )
    parser.add_argument("--input",    type=Path, required=True,
                        help="Path to ZIP archive containing XSD files")
    parser.add_argument("--summary",  type=Path, required=True,
                        help="Output path for the summary CSV")
    parser.add_argument("--detailed", type=Path, required=True,
                        help="Output path for the detailed CSV")
    parser.add_argument("--config",   type=Path, required=True,
                        help="JSON config file for detailed CSV")
    args = parser.parse_args()

    # ── 1) Unpack ZIP to temp, auto-detect main XSD, and run import check ──
    with tempfile.TemporaryDirectory() as tmpdir_str:
        tmpdir = Path(tmpdir_str)
        with zipfile.ZipFile(args.input, 'r') as zf:
            zf.extractall(tmpdir)

        xsd_root = tmpdir / "xsd"
        main_xsd = find_main_xsd(xsd_root)
        print(f"Using main XSD: {main_xsd.relative_to(tmpdir)}", file=sys.stderr)

        for path, status in check_imports(main_xsd, xsd_root):
            if status != "OK":
                print(f"Warning: {path} → {status}", file=sys.stderr)

    # ── 2) Generate the CSV outputs ──
    extract_and_process(args.input, args.summary)
    create_detailed_csv(args.input, args.detailed, args.config)
