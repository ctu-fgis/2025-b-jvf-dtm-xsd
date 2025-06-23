# 🧰 Dependencies

To run this project, you need **Python 3.x** and the following dependencies:

## ✅ Standard Python libraries (no installation needed)
These are included with every Python distribution:

- `zipfile` – for extracting the ZIP archive
- `json` – for reading the config file
- `pathlib` – for working with filesystem paths
- `tempfile` – for creating temporary folders

## 📦 External packages (must be installed via `pip`)
These libraries must be installed manually:

- [`lxml`](https://lxml.de/) – fast XML and XSD parsing  
- [`pandas`](https://pandas.pydata.org/) – tabular data handling and CSV export  
- [`xmlschema`](https://pypi.org/project/xmlschema/) – optional schema-level validation *(used only in some modules)*

Install them using:

```bash
pip install lxml pandas xmlschema
```
