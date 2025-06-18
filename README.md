# 2025-b-jvf-dtm-xsd
Group B (academic year 2024/2025)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📄 Description

This repository contains the semestral project for the course **[Free Software GIS](https://geo.fsv.cvut.cz/vyuka/155fgis/)**, focused on processing **XSD** files for **JVF DTM** using Python scripts and Jupyter notebooks. You can find the **XSD schemas for JVF DTM** here: [XSD for DTM](https://cuzk.gov.cz/DMVS/JVF-DTM/Platna-verze.aspx)

## 👥 Authors

- [Matěj Klimeš](https://github.com/klimesm)
- [Michal Kovář](https://github.com/kovarmi9)


## 📖 Documentation

**Full online documentation here:** [https://ctu-fgis.github.io/2025-b-jvf-dtm-xsd/](https://ctu-fgis.github.io/2025-b-jvf-dtm-xsd/)


## 🔧 Usage

#### Windows

```cmd
python .\src\parse_xsd_to_csv.py --input .\tests\data\JVF_DTM_143_XSD.zip --summary .\tests\output\summary.csv --detailed .\tests\output\detailed.csv --config .\tests\data\config_str1_test.json
```

#### Linux

```cmd
python3 ./src/parse_xsd_to_csv.py --input ./tests/data/JVF_DTM_143_XSD.zip --summary ./tests/output/summary.csv --detailed ./tests/output/detailed.csv --config ./tests/data/config_str1_test.json
```

## 📜 License

This project is licensed under the [MIT License](LICENSE).


