# Imports
import zipfile
import pandas as pd
from pathlib import Path
from lxml import etree
import tempfile

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

# CLI entrypoint
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract <element> references from XSD ZIP archive.")
    parser.add_argument("--input", type=Path, required=True, help="Path to ZIP archive.")
    parser.add_argument("--output", type=Path, required=True, help="Path to output CSV file.")
    args = parser.parse_args()

    extract_and_process(args.input, args.output)
