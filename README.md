<!-- docs-start -->
# JVF DTM XSD Parser
Group B (academic year 2024/2025)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📄 Description

This repository contains the semestral project for the course **[Free Software GIS](https://geo.fsv.cvut.cz/vyuka/155fgis/)**, focused on processing **XSD** files for **JVF DTM** using Python scripts and Jupyter notebooks. You can find the **XSD schemas for JVF DTM** here: [XSD for DTM](https://cuzk.gov.cz/DMVS/JVF-DTM/Platna-verze.aspx)

## 👥 Authors

- [Matěj Klimeš](https://github.com/klimesm)
- [Michal Kovář](https://github.com/kovarmi9)
<!-- docs-end -->

## 📖 Documentation

**Full online documentation here:** [https://ctu-fgis.github.io/2025-b-jvf-dtm-xsd/](https://ctu-fgis.github.io/2025-b-jvf-dtm-xsd/)


## 🔧 Usage

### Basic syntax

```cmd
python parse_xsd_to_csv.py --input <ZIP_FILE> --summary <SUMMARY_CSV> --detailed <DETAILED_CSV> --config <CONFIG_JSON>
```
### Examples for Project Structure

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

## 📜 License

This project is licensed under the [MIT License](LICENSE).
