# 📘 About

This project focuses on parsing and analyzing XSD schemas used in the Czech national digital technical map (DTM). Python utility parses and validates the XSD schemas. On each run it will:

- Unpacks the ZIP and verifies every `.xsd` file is referenced by `index_data.xsd` or `input_data.xsd`  
- Prints a warning for any missing or unreferenced schemas (non-blocking)  

It then produces two CSV outputs:

- **summary.csv**: Provides a overview of key elements found in XSD files
- **detailed.csv**: Contains a full breakdown of elements, types, and attributes extracted from XSD files based on a configuration file.

**Tested on DTM schema versions 1.4.3 and 1.5.0.beta3.**
