# 🔧 Usage

This section explains how to use the script to extract data from ZIP archives containing XSD files and output the results into summary and detailed CSV files.

## General Instructions

You can run the script from the command line using Python.

Basic syntax:

```cmd
python parse_xsd_to_csv.py --input <ZIP_FILE> --summary <SUMMARY_CSV> --detailed <DETAILED_CSV> --config <CONFIG_JSON>
```

Where:

- `--input` is the path to the input ZIP archive containing XSD files.
- `--summary` is the path to the output CSV file with a summary of elements.
- `--detailed` is the path to the output CSV file with detailed element descriptions.
- `--config` is the path to the JSON file specifying element types and fields for detailed export.

## Examples for Project Structure

If you're running from the root of the repository, and using the provided test data and configuration:

#### Windows

```cmd
python .\src\parse_xsd_to_csv.py --input .\tests\data\JVF_DTM_143_XSD.zip --summary .\tests\output\summary.csv --detailed .\tests\output\detailed.csv --config .\tests\data\config_str1_test.json
```

#### Linux

```cmd
python3 ./src/parse_xsd_to_csv.py --input ./tests/data/JVF_DTM_143_XSD.zip --summary ./tests/output/summary.csv --detailed ./tests/output/detailed.csv --config ./tests/data/config_str1_test.json
```

## Notes

- The input ZIP archive must contain a folder structure ending with `xsd/objekty` where the `.xsd` files are located.
- The summary CSV file includes basic information about referenced elements like `atr:` and `gml:`.
- The detailed CSV file uses a JSON configuration to extract more specific attributes from the XSD schema.
