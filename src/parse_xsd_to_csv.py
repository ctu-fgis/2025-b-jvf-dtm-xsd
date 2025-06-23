# Imports
import zipfile
import pandas as pd
import json
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


def process_flag_value(data, element, matched_column, flag, is_unique=False):
    """
    Extracts the value of a specific attribute (flag) from an XML element and stores it in the data dictionary.

    Parameters:
    - data: dict where extracted values are stored.
    - element: XML element being processed.
    - matched_column: base name used to construct the output column name.
    - flag: the attribute name to extract from the element.
    - is_unique: if True, prevents duplicate values in the list for this column.
    """
    val = element.get(flag)
    if not val:
        return

    output_column_name = f"{matched_column}_{flag}"

    if output_column_name not in data:
        data[output_column_name] = [val]
    else:
        if not isinstance(data[output_column_name], list):
            data[output_column_name] = [data[output_column_name]]

        if is_unique and val in data[output_column_name]:
            return

        data[output_column_name].append(val)


def order_dataframe_columns_by_config(df, config, element_types):
    """
    Orders DataFrame columns based on the config and element_types definition.
    Columns from config (e.g. filename, namespace) and element attributes/flags
    will appear first, in the defined order. Any remaining columns are added at the end.
    """
    ordered_cols = []

    # Add basic config-defined columns
    for key in ["filename", "namespace", "name", "type"]:
        if config.get(key):
            ordered_cols.append(key)

    # Add columns defined in element_types
    for col, desc in element_types.items():
        base = col.split(":")[-1]

        # Add existence flag
        if desc.get("exist"):
            ordered_cols.append(base)

        # Add element flags like required, prohibited, etc.
        for flag, val in desc.items():
            if flag in {"exist", "match"}:
                continue
            if val is True or val == "unique":
                ordered_cols.append(f"{base}_{flag}")

        # Add attribute columns
        if "attributes" in desc:
            for attr, props in desc["attributes"].items():
                for prop in props:
                    ordered_cols.append(f"{attr}_{prop}")

    # Add any remaining columns from DataFrame
    remaining = [c for c in df.columns if c not in ordered_cols]
    return df.reindex(columns=ordered_cols + remaining)

# Main function for summary CSV
def create_summary_csv(zip_path: Path, output_csv: Path):
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
        element_types = config["element_types"]

        for file_path in xsd_objects_path.glob("*.xsd"):
            try:
                tree = etree.parse(str(file_path))
                root = tree.getroot()
                namespace = root.attrib.get("targetNamespace", "")

                data = {}
                if config.get("filename") is True:
                    data["filename"] = file_path.name
                if config.get("namespace") is True:
                    data["namespace"] = namespace

                # Get top-level element
                if config.get("name") is True or config.get("type") is True:
                    top_level_elems = root.xpath('./*[local-name()="element"]')
                    main_elem = top_level_elems[0]
                    if config.get("name") is True:
                        data["name"] = main_elem.get("name", "")
                    if config.get("type") is True:
                        data["type"] = main_elem.get("type", "")

                # Initialize the value of exist to 0 when asking for existence
                for column_name, description in element_types.items():
                    if description.get("exist") is True:
                        cleaned_column_name = column_name.split(":")[-1]
                        data[cleaned_column_name] = 0

                all_elements = root.xpath(".//*[local-name()='element']")
                for element in all_elements:
                    etype = None
                    match_key = None
                    matched_column = None
                    # Find "match" values from config file
                    for column_name, description in element_types.items():
                        config_match = description.get("match")
                        # if value of "match" is not given, use "name"
                        if not config_match:
                            config_match = "name"

                        # Try to find element match
                        match_element = element.get(config_match)
                        # if it is the right element save description, column_name and match value
                        if match_element == column_name:
                            etype = description
                            matched_column = column_name.split(":")[-1]
                            match_key = config_match
                            break

                    if not etype:
                        # skip if matching element type wasn't found
                        continue
                    # Handle attributes
                    if "attributes" in etype:
                        # Iterate over attributes and their properties
                        for attr_name, props in etype["attributes"].items():
                            for prop in props:
                                # find values using xpath
                                val = element.xpath(
                                    f".//*[local-name()='attribute' and @{match_key}='{attr_name}']/@{prop}")
                                # save to output data
                                if val:
                                    data[f"{attr_name}_{prop}"] = val[0]

                    # Handle existence of element
                    if etype.get("exist") is True:
                        cleaned_matched_column = matched_column.split(":")[-1]
                        data[cleaned_matched_column] = 1

                    # Special case for geometry in version 1.4.3 without explicit 'type' attribute
                    if matched_column == "GeometrieObjektu" and not element.get("type"):
                        # Find all child <element> nodes with a 'ref' attribute
                        ref_values = element.xpath(".//*[local-name()='element' and @ref]/@ref")
                        if ref_values:
                            data["GeometrieObjektu"] = ref_values

                    # Handle asking directly for element properties
                    true_flags = [key for key, value in etype.items() if value is True]
                    unique_flags = [key for key, value in etype.items() if value == "unique"]
                    unique_cols = list(f"{matched_column}_{flag}" for flag in unique_flags)
                    for flag in true_flags:
                        process_flag_value(data, element, matched_column, flag, is_unique=False)

                    for flag in unique_flags:
                        process_flag_value(data, element, matched_column, flag, is_unique=True)

                    for col in list(data):
                        if col in unique_cols:
                            if not isinstance(data[col], list):
                                data[col] = [data[col]]
                        else:
                            if isinstance(data[col], list) and len(data[col]) == 1 and col not in ("GeometrieObjektu_type", "GeometrieObjektu"):
                                data[col] = data[col][0]

                records.append(data)

            except Exception as e:
                print(f"[Error] {file_path.name}: {e}")
                raise

        df = pd.DataFrame(records)
        df = order_dataframe_columns_by_config(df, config, element_types)
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

    create_summary_csv(args.input, args.summary)
    create_detailed_csv(args.input, args.detailed, args.config)
