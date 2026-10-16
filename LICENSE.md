# Licenses and data sources

## Where each part comes from

| Part | Source | Terms |
|---|---|---|
| `inputs/N*.txt`, `inputs/I*.txt` | sampled from `names.dmp`, `nodes.dmp`, `merged.dmp` and `delnodes.dmp` of the NCBI Taxonomy `taxdump.tar.gz` of 2026-10-11 | NCBI public data; see NCBI's policies and disclaimers, https://www.ncbi.nlm.nih.gov/home/about/policies/ |
| NCBI response fields in `results/per_input.csv` (TaxIDs, codes, names, error text, query translations) | responses of the legacy Taxonomy Name/Id Status Report, Datasets v2 and E-utilities, 2026-10-11/12 | NCBI public data, as above |
| `inputs/R.txt`, `inputs/R_draws.csv`, and the frame R rows of `results/per_input.csv` (input names, occurrence keys, datasetKeys) | GBIF occurrence records, https://www.gbif.org/ | each name carries the license of its GBIF dataset: CC0 1.0, CC BY 4.0 or CC BY-NC 4.0. The dataset, publisher, license and DOI for every input are in `results/gbif_datasets.csv` and the `gbif_dataset_license` column. Cite GBIF data by dataset DOI. CC BY-NC 4.0 names are shared for non-commercial research use and are not relicensed. |
| `results/gbif_datasets.csv` | GBIF dataset and organization API, read 2026-10-16 | GBIF metadata |
| `README.md`, `method.md`, `inputs/strata.csv`, `results/requests.csv`, and our derived columns (`label`, `in_dump`, `position`, `legacy_rows`, `gbif_kingdom`, `gbif_draw`) | CyberNative AI LLC | Creative Commons Attribution 4.0 International (CC BY 4.0), https://creativecommons.org/licenses/by/4.0/ |
| `check.py` | CyberNative AI LLC | MIT License, below |

The NCBI and GBIF material is included only so that the comparison can be checked. It does not change those sources'
own terms, and nothing here is endorsed by NCBI or GBIF.

## MIT License (check.py)

Copyright (c) 2026 CyberNative AI LLC

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
