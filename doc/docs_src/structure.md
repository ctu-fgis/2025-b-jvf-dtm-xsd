# 🗂️ Repository Structure

Project repository is organized into the following folders and files:

```
2025-b-jvf-dtm-xsd/
├── .github/
│   └── workflows/
│       └── deploy.yml                    # GitHub Actions
├── doc/                                  # Documentation texts
├── doc.yml                               # MkDocs configuration file
├── LICENSE                               # MIT license text
├── README.md                             # Project overview
├── notebooks/
│   ├── test-input-xsd.ipynb              # Notebook for validating XSD imports
│   └── test-parse-input-xsd-to-csv.ipynb # Notebook for parsing XSD
├── src/
│   └── parse_xsd_to_csv.py               # Main script for processing XSD files
├── tests/
│   ├── data/
│   │   ├── config_str1_test.json         # Configuration for parsing rules
│   │   └── JVF_DTM_143_XSD.zip           # Test ZIP archive of XSD schemas
│   └── output/
│       ├── detailed.csv                  # Detailed output CSV
│       └── summary.csv                   # Summary output CSV
└── .gitignore                            # Gitignore file
```
