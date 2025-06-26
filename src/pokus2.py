#!/usr/bin/env python3
"""
pokus.py

1. Unpack the ZIP to a temp dir.
2. Find the main XSD file (input_data.xsd or index_data.xsd).
3. Perform the exact notebook import‐vs‐disk check and print warnings.
4. Run your existing summary and detailed CSV routines.
"""

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

def extract_and_process(zip_path: Path, output_csv: Path):
    """
    YOUR EXISTING SUMMARY LOGIC HERE.
    """
    # ---- Begin original summary code ----
    records = []
    seen_global = set()
    with tempfile.TemporaryDirectory() as tmpdir_str:
        tmpdir = Path(tmpdir_str)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmpdir)

        xsd_objects_path = tmpdir / "xsd" / "objekty"
        for file_path in xsd_objects_path.glob("*.xsd"):
            tree = etree.parse(str(file_path))
            root = tree.getroot()
            complex_types = root.xpath(".//*[local-name()='complexType']")
            for complex_type in complex_types:
                atr_normal, atr_ki = [], []
                gml_refs, gml_min_flags = [], []
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
                    final_min = "0" if "0" in gml_min_flags or atr_ki_with_0 else None
                    records.append({
                        "filename": file_path.name,
                        "nazev": str(gml_refs),
                        "minOccurs": final_min
                    })
                records.extend(atr_ki)

    df = pd.DataFrame(records)
    df.to_csv(output_csv, index=False, encoding="utf-8")
    print(f"Saved {len(df)} rows to {output_csv}")
    # ---- End original summary code ----

def create_detailed_csv(zip_path: Path, output_detailed_csv: Path, input_config: Path):
    """
    YOUR EXISTING DETAILED LOGIC HERE.
    """
    # ---- Begin original detailed code ----
    with open(input_config, "r", encoding="utf-8") as f:
        config = json.load(f)
    records = []
    with tempfile.TemporaryDirectory() as tmpdir_str:
        tmpdir = Path(tmpdir_str)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmpdir)
        xsd_objects_path = tmpdir / "xsd" / "objekty"
        output_fields = config["output_fields"]
        rules = config["element_types"]

        for file_path in xsd_objects_path.glob("*.xsd"):
            tree = etree.parse(str(file_path))
            root = tree.getroot()
            namespace = root.attrib.get("targetNamespace","")
            data = {k: "" for k in output_fields}
            data.update(filename=file_path.name, namespace=namespace,
                        zaznamy=[], OblastObjektuKI=0)
            # top-level element
            tops = root.xpath(
                f"./*[local-name()='element' and starts-with(@type, '{namespace}:')]"
            )
            if tops:
                e = tops[0]
                data["name"], data["type"] = e.get("name",""), e.get("type","")
            # element iteration
            for ct in root.xpath(".//*[local-name()='complexType']"):
                for elt in ct.xpath(".//*[local-name()='element']"):
                    nm, rf, mo = elt.get("name"), elt.get("ref"), elt.get("minOccurs")
                    match = None; etype=None; clean_ref=None
                    if nm in rules:
                        etype, match = rules[nm], "name"
                    elif rf in rules:
                        etype, match = rules[rf], "ref"
                        clean_ref = rf.split(":")[-1]
                    else:
                        continue
                    # attributes
                    if "attributes" in etype:
                        for an, props in etype["attributes"].items():
                            for prop in props:
                                path = (
                                    f".//*[local-name()='attribute' and @name='{an}']"
                                    if match=="name" else
                                    f".//*[local-name()='attribute' and @ref='{an}']"
                                )
                                val = elt.xpath(path+f"/@{prop}")
                                if val:
                                    data[f"{an}_{prop}"] = val[0]
                    # direct flags
                    true_flags = [k for k,v in etype.items() if v is True and k!="geometry"]
                    for flag in true_flags:
                        val = elt.get(flag)
                        if val is not None:
                            if flag=="minOccurs":
                                data[f"{clean_ref}_{flag}"] = val
                                data[clean_ref] = 1
                            else:
                                key = nm if match=="name" else rf
                                data[key] = val
                    # geometry
                    if etype.get("geometry") is True:
                        data["geom_minOccurs"] = mo
                        geom_elts = elt.xpath(".//*[local-name()='element' and @ref]")
                        data["geometry"] = [g.get("ref") for g in geom_elts]
            records.append(data)

    df = pd.DataFrame(records)
    df.to_csv(output_detailed_csv, index=False, encoding="utf-8")
    print(f"Saved {len(df)} rows to {output_detailed_csv}")
    # ---- End original detailed code ----

def main():
    parser = argparse.ArgumentParser(
        description="Unpack XSD ZIP, do notebook‐style import check, then export CSVs."
    )
    parser.add_argument("--input",    type=Path, required=True,
                        help="Path to ZIP archive")
    parser.add_argument("--summary",  type=Path, required=True,
                        help="Path for summary CSV")
    parser.add_argument("--detailed", type=Path, required=True,
                        help="Path for detailed CSV")
    parser.add_argument("--config",   type=Path, required=True,
                        help="JSON config for detailed CSV")
    args = parser.parse_args()

    # ── 1) Notebook‐exact import/disk check ──
    with tempfile.TemporaryDirectory() as tmpdir_str:
        output_path = Path(tmpdir_str)
        with zipfile.ZipFile(args.input, 'r') as zf:
            zf.extractall(output_path)

        # find main XSD exactly as notebook did
        xsd_path = None
        candidates = list(output_path.rglob("input_data.xsd")) \
                   + list(output_path.rglob("index_data.xsd"))
        if candidates:
            xsd_path = candidates[0]
            print(f"Found main XSD: {xsd_path.relative_to(output_path)}", file=sys.stderr)
        else:
            raise FileNotFoundError(
                "Neither 'input_data.xsd' nor 'index_data.xsd' was found."
            )

        # parse imports/includes
        tree = etree.parse(str(xsd_path))
        ns = {"xs": "http://www.w3.org/2001/XMLSchema"}
        raw_imports = {
            el.get("schemaLocation")
            for tag in ("import","include")
            for el in tree.getroot().findall(f".//xs:{tag}", namespaces=ns)
            if el.get("schemaLocation")
        }

        # normalize and gather sets
        imported = {
            normalize_path(Path(loc).as_posix())
            for loc in raw_imports
        }
        all_files = {
            normalize_path(p.relative_to(output_path).as_posix())
            for p in output_path.rglob("*.xsd")
        }

        # compare and warn
        for path in sorted(imported.union(all_files)):
            in_imp = path in imported
            on_disk = path in all_files
            if in_imp and on_disk:
                status = "OK"
            elif in_imp and not on_disk:
                status = "Missing"
            else:
                status = "Unreferenced"
            if status != "OK":
                print(f"Warning: {path} → {status}", file=sys.stderr)

    # ── 2) Run your CSV exports ──
    extract_and_process(args.input,   args.summary)
    create_detailed_csv(args.input,   args.detailed,  args.config)

if __name__ == "__main__":
    main()
