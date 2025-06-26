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
    Remove leading '../' segments and 'xsd/' prefix from paths.
    """
    while p.startswith("../"):
        p = p[3:]
    if p.startswith("xsd/"):
        p = p[4:]
    return p


def test_imported_xsd(zip_path: Path):
    """
    Unpack the ZIP, locate main XSD (input_data.xsd or index_data.xsd),
    perform import-vs-disk check, and print warnings.
    """
    with tempfile.TemporaryDirectory() as tmpdir_str:
        output_path = Path(tmpdir_str)
        # Extract ZIP
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(output_path)

        # Locate main XSD
        candidates = list(output_path.rglob("input_data.xsd")) + \
                     list(output_path.rglob("index_data.xsd"))
        if not candidates:
            raise FileNotFoundError("Neither 'input_data.xsd' nor 'index_data.xsd' found.")
        xsd_path = candidates[0]
        print(f"Found main XSD: {xsd_path.relative_to(output_path)}", file=sys.stderr)

        # Parse imports/includes
        tree = etree.parse(str(xsd_path))
        ns = {"xs": "http://www.w3.org/2001/XMLSchema"}
        raw_imports = {
            el.get("schemaLocation")
            for tag in ("import", "include")
            for el in tree.getroot().findall(f".//xs:{tag}", namespaces=ns)
            if el.get("schemaLocation")
        }

        # Normalize and collect sets
        imported = { normalize_path(Path(loc).as_posix()) for loc in raw_imports }
        all_files = {
            normalize_path(p.relative_to(output_path).as_posix())
            for p in output_path.rglob("*.xsd")
        }

        # Compare and warn
        for path in sorted(imported.union(all_files)):
            if   path in imported and path in all_files:
                status = "OK"
            elif path in imported:
                status = "Missing"
            else:
                status = "Unreferenced"

            if status != "OK":
                print(f"Warning: {path} → {status}", file=sys.stderr)

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
                top_level_elems = root.xpath(f"./*[local-name()='element' and starts-with(@type, '{namespace}:')]")
                if top_level_elems:
                    main_elem = top_level_elems[0]
                    data["name"] = main_elem.get("name", "")
                    data["type"] = main_elem.get("type", "")

                # Find all complex types and iterate over elements inside
                complex_types = root.xpath(".//*[local-name()='complexType']")
                for complex_type in complex_types:
                    for element in complex_type.xpath(".//*[local-name()='element']"):
                        name = element.get("name")
                        ref = element.get("ref")
                        min_occurs = element.get("minOccurs")
                        match = None
                        etype =None
                        clean_ref = None
                        # Handle defined element types
                        if name in element_rules:
                            etype = element_rules[name]
                            match = "name"
                        elif ref in element_rules:
                            etype = element_rules[ref]
                            match = "ref"
                            clean_ref = ref.split(":")[-1]
                        else:
                            continue

                        # Handle attributes
                        if "attributes" in etype:
                            for attr_name, props in etype["attributes"].items():
                                for prop in props:
                                    if match == "name":
                                        val = element.xpath(f".//*[local-name()='attribute' and @name='{attr_name}']/@{prop}"
                                                            )
                                    elif match == "ref":
                                        val = element.xpath(f".//*[local-name()='attribute' and @ref='{attr_name}']/@{prop}"
                                                            )
                                    if val:
                                        data[f"{attr_name}_{prop}"] = val[0]

                        # Handle special case when asking directly for element properties
                        true_flags = [key for key, value in etype.items() if value is True and key != "geometry"]

                        for flag in true_flags:
                            # if flag != "geometry":
                            val = element.get(flag)
                            if val is not None:
                                if flag == "minOccurs":
                                    data[f"{clean_ref}_{flag}"] = val
                                    data[clean_ref] = 1
                                else:
                                    if match == "name":
                                        data[name] = val
                                    elif match == "ref":
                                        data[ref] = val

                        # Handle special case for geometry
                        if etype.get("geometry") is True:
                            data["geom_minOccurs"] = min_occurs
                            ref_elem = element.xpath(".//*[local-name()='element' and @ref]")
                            data["geometry"] = [geom.get("ref") for geom in ref_elem]

                records.append(data)

            except Exception as e:
                print(f"[Error] {file_path.name}: {e}")
                raise

        df = pd.DataFrame(records)
        df.to_csv(output_detailed_csv, index=False, encoding="utf-8")
        print(f"Saved {len(df)} rows to {output_detailed_csv}")


# CLI entrypoint
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract <element> references from XSD ZIP archive.")
    parser.add_argument("--input", type=Path, required=True, help="Path to ZIP archive.")
    parser.add_argument("--summary", type=Path, required=True, help="Path to output summary CSV file.")
    parser.add_argument("--detailed", type=Path, required=True, help="Path to output detailed CSV file.")
    parser.add_argument("--config", type=Path, required=True, help="Path to JSON config file.")
    args = parser.parse_args()

    test_imported_xsd(args.input)
    extract_and_process(args.input, args.summary)
    create_detailed_csv(args.input, args.detailed, args.config)
