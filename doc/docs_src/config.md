# ⚙️ XSD Configuration File

This page documents the structure and meaning of configuration file used to extract metadata from `.xsd` files, specifically for versions **1.4.3** and **1.5.0**.

These JSON config file drive the behavior of XSD parsing scripts and influence the generated detailed CSV output (`detailed_*.csv`).

---

## Top-Level Keys

| Key         | Type  | Description                                                               |
|-------------|-------|---------------------------------------------------------------------------|
| `filename`  | bool  | Includes the XSD filename in output.                                     |
| `namespace` | bool  | Extracts the `targetNamespace` of the schema.                            |
| `name`      | bool  | Extracts the `@name` attribute of the root element.                      |
| `type`      | bool  | Extracts the `@type` attribute of the root element.                      |
| `element_types` | dict | Mapping of element names to extraction rules (see below).               |

These keys are identical in both config versions.

---

###  `element_types`

Each entry under `element_types` defines how a specific element should be matched and which data should be extracted.

#### Common Options per Element

| Key        | Type      | Description                                                                 |
|------------|-----------|-----------------------------------------------------------------------------|
| `match`    | string    | Attribute to use for identifying elements (e.g. `name`, `ref`, `substitutionGroup`). |
| `exist`    | bool      | If `true`, check if the element exists in XSD file                          |
| `minOccurs`| bool      | If `true`, extract the `minOccurs` attribute value.                         |
| `fixed`    | bool      | If `true`, extract the `fixed` attribute.                                   |
| `type`     | bool/"unique" | Extract all `type` attributes; `"unique"` means extract only unique values. |
| `attributes` | dict   | Nested attributes to extract (e.g. `code_base`, `code_suffix`).     |
> **Note:**  
> If `match` is not defined for an element in the config, the default matching attribute is `name`.
```json
"KategorieObjektu": {
      "match": "name",
      "fixed": true
    }
```

#### `attributes`

The `attributes` dictionary allows specifying particular attributes of complex elements to extract.

Each key in `attributes` represents an attribute name (e.g. `code_base`, `dim`, etc.), and its value is a **list** of attribute properties to extract from that attribute:

```json
"attributes": {
  "code_base": ["fixed", "use"],
  "dim": ["fixed", "use"]
}
```
---
## Specifics for version 1.4.3

In XSD version 1.4.3, **GeometrieObjektu** does not have a defined `type`.  
If **GeometrieObjektu** is present in `element_types`, the geometry type is saved automatically.
