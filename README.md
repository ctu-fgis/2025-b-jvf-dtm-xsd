# 2025-b-jvf-dtm-xsd
Skupina B (akademický rok 2024/2025)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📄 Description
This repository contains the semestral project for the course **[Free Software GIS](https://geo.fsv.cvut.cz/vyuka/155fgis/)**, focused on processing **XSD** files for **JVF DTM** using Python scripts and Jupyter notebooks. You can find the **XSD schemas for JVM DTM** here: [XSD for DTM](https://cuzk.gov.cz/DMVS/JVF-DTM/Platna-verze.aspx)

## 👥 Authors

- [Matěj Klimeš](https://github.com/klimesm)
- [Michal Kovář](https://github.com/kovarmi9)

## 📁 Repository structure
<pre>
├── notebooks/                                    # Jupyter notebooks with development code
│   └── test-parse-input-xsd-to-csv.ipynb         # Example: xsd loading, parsing, etc.
├── tests/data/                                   # Input data for tests (e.g. XSD, GML)
├── .gitignore                                    # Git ignored files config
├── LICENSE                                       # MIT License file
└── README.md                                     # This documentation
</pre>

## 📦 Dependencies

- `xmlschema`
- `lxml`
- `pandas`

Install them using:

```bash
pip install xmlschema lxml pandas
```

## 📜 License

This project is licensed under the [MIT License](LICENSE).