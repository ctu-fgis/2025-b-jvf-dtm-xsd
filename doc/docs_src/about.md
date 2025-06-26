## 📘 About

This project focuses on parsing and analyzing XSD schemas used in the Czech national digital technical map (DTM). Python utility parses and validates the XSD schemas. On each run it will:

1. **Unpack and validate**  
   - Confirms every `.xsd` file in the ZIP is referenced by `index_data.xsd`/`input_data.xsd`  
   - Flags any missing or unreferenced schemas with non-blocking warnings  

2. **Generate CSV reports**  
   - **Summary**: a concise list of all element references across your schemas  
   - **Detailed**: a fully configurable, JSON-driven export that extracts exactly the fields you need
