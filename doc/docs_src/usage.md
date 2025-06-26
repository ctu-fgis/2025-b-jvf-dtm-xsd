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
XSD version 1.4.3

```cmd
python .\src\parse_xsd_to_csv.py --input .\tests\data\JVF_DTM_143_XSD.zip --summary .\tests\output\summary_1.4.3.csv --detailed .\tests\output\detailed_1.4.3.csv --config .\tests\data\config_1.4.3.json
```

XSD version 1.5.0

```cmd
python .\src\parse_xsd_to_csv.py --input .\tests\data\JVF_DTM_150_beta3_XSD.zip --summary .\tests\output\summary_1.5.0.csv --detailed .\tests\output\detailed_1.5.0.csv --config .\tests\data\config_1.5.0.json
```

#### Linux / macOS
XSD version 1.4.3

```cmd
python3 ./src/parse_xsd_to_csv.py --input ./tests/data/JVF_DTM_143_XSD.zip --summary ./tests/output/summary_1.4.3.csv --detailed ./tests/output/detailed_1.4.3.csv --config ./tests/data/config_1.4.3.json
```
XSD version 1.5.0

```cmd
python3 ./src/parse_xsd_to_csv.py --input ./tests/data/JVF_DTM_150_beta3_XSD.zip --summary ./tests/output/summary_1.5.0.csv --detailed ./tests/output/detailed_1.5.0.csv --config ./tests/data/config_1.5.0.json
```
## Configuration File

For detailed information about the configuration file structure and settings, see the [Configuration File Structure](config.md).

## Notes

- The input ZIP archive must contain a folder structure ending with `xsd/objekty` where the `.xsd` files are located.
- The summary CSV file includes basic information about referenced elements like `atr:` and `gml:`.
- The detailed CSV file uses a JSON configuration to extract more specific attributes from the XSD schema.
