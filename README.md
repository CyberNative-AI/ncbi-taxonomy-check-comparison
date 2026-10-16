# NCBI Taxonomy name/ID check: legacy tool vs Datasets v2 vs E-utilities

Inputs, per-input results and method for a one-time comparison of how three NCBI services resolved the same
taxonomy names and taxids on 11–12 October 2026 (UTC). Every count and share in this README is recomputed from
the files in this repository by `python3 check.py`.

## What was compared

| Arm | Endpoint | How it was called |
|---|---|---|
| Legacy | Taxonomy Name/Id Status Report, `https://www.ncbi.nlm.nih.gov/Taxonomy/TaxIdentifier/tax_identifier.cgi` | multipart POST, `tax=<newline-separated list>`, `button=Save in file`; up to 200 inputs per POST |
| Datasets | Datasets v2 `POST https://api.ncbi.nlm.nih.gov/datasets/v2/taxonomy/dataset_report` | JSON `{"taxons": [...], "page_size": 1000}`; up to 100 inputs per POST |
| E-utilities | `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=taxonomy&term=<input>&retmode=json&retmax=50` | one request per name input; taxid inputs were not sent |

The Datasets arm is the API call that the redesigned check page (`/datasets/taxonomy/check/`) makes. We measured
the API, not the page, except for one small browser check described under Limitations.

Request log (`results/requests.csv`): legacy 21 POSTs (20 HTTP 200), 2026-10-11T23:43:12Z to 2026-10-12T00:35:51Z;
one N5 POST returned HTTP 502 and was re-sent once, and only the re-sent response is used. Datasets 38 POSTs (38 HTTP 200), 2026-10-11T23:44:47Z to 2026-10-12T00:36:34Z.
E-utilities requests were sent on 2026-10-11/12 UTC and the frame R names were drawn from GBIF in the same window;
those request times come from our run notes and are not in these files (see `method.md`).

Name inputs came from NCBI's `taxdump.tar.gz` downloaded on 2026-10-11 (HTTP Last-Modified 2026-10-11 23:30:11 GMT,
SHA-256 `5b529fe94cf88c9d9f7fd3cb2ffaa5e263234efea25acfd8cf899040eef84cd7`). That release is not included here;
`in_dump` in the results refers to its `names.dmp`.

## Inputs (`inputs/`)

One UTF-8, LF-terminated file per stratum, one input per line, in the order sent. `inputs/strata.csv` gives each
stratum's description, the `names.dmp` pool it was sampled from and its size.

| Stratum | What it is |
|---|---|
| N1 | scientific names that have no unique-name disambiguator (control) |
| N2 | bare scientific names that NCBI also disambiguates with a unique name, sent without the disambiguator |
| N3 | unique-name strings with the disambiguator, e.g. `Agathis montana (in: seed plants)` |
| N4 | `synonym` |
| N5 | `equivalent name` |
| N6 | `authority` (name with author and year as NCBI stores it) |
| N7 | `genbank common name` |
| N8 | `common name` (not GenBank common names) |
| N9 | `includes` |
| N10 | `in-part` |
| N11 | `acronym` |
| N12 | `type material` |
| I1 | current taxids from `nodes.dmp` (control) |
| I2 | merged (old) taxids from `merged.dmp` |
| I3 | deleted taxids from `delnodes.dmp` |
| R | 1,000 distinct verbatim names: the verbatim `dwc:scientificName` of randomly drawn GBIF occurrence records (`inputs/R_draws.csv`) |

N and I strata are equal-sized random samples of each name class or taxid list, not weighted by how often people
use them.

## How each input was labelled

For each input: legacy set L = the taxids on legacy rows whose code starts with 1 or 2 (for taxid inputs: code 1
gives the input, code 2 the primary taxid, code 3 the input, code 4 nothing); Datasets set D = the `tax_id` of
every report for that query; E = the esearch `idlist`.

- **AGREE**: L and D both non-empty and equal.
- **LOST**: L non-empty, D empty.
- **COLLAPSED**: the legacy tool listed more than one row, and D is a smaller non-empty subset of L
  (Datasets returns one of several taxa).
- **CHANGED**: both non-empty, not equal, not COLLAPSED.
- **BOTH_NONE**: neither resolves the input.
- **MISSING_L**: the legacy output row could not be aligned to the input, so no label (see Limitations).

Legacy rows are aligned to inputs in order by the echoed name after Unicode NFC, whitespace collapsing and case
folding; Datasets reports are matched by their `query` field the same way. `check.py` recomputes all
3,440 of 3,440 labels from the TaxID columns of `results/per_input.csv`. `method.md` has the full rules.

## Result 1: name classes (N and I strata)

| Stratum | Inputs | L non-empty | AGREE | LOST | COLLAPSED | CHANGED | BOTH_NONE | MISSING_L | E-utilities = legacy among LOST |
|---|---|---|---|---|---|---|---|---|---|
| N1 | 200 | 199 | 199 | 0 | 0 | 0 | 0 | 1 | - |
| N2 | 200 | 200 | 195 | 0 | 5 | 0 | 0 | 0 | - |
| N3 | 150 | 0 | 0 | 0 | 0 | 0 | 150 | 0 | - |
| N4 | 200 | 194 | 189 | 5 | 0 | 0 | 1 | 5 | 1/5 |
| N5 | 150 | 150 | 148 | 2 | 0 | 0 | 0 | 0 | 0/2 |
| N6 | 150 | 147 | 0 | 147 | 0 | 0 | 3 | 0 | 80/147 |
| N7 | 150 | 150 | 148 | 0 | 2 | 0 | 0 | 0 | - |
| N8 | 150 | 150 | 0 | 150 | 0 | 0 | 0 | 0 | 150/150 |
| N9 | 150 | 150 | 149 | 1 | 0 | 0 | 0 | 0 | 1/1 |
| N10 | 150 | 147 | 0 | 136 | 10 | 1 | 0 | 3 | 133/136 |
| N11 | 100 | 100 | 100 | 0 | 0 | 0 | 0 | 0 | - |
| N12 | 100 | 0 | 0 | 0 | 0 | 0 | 100 | 0 | - |
| I1 | 200 | 200 | 200 | 0 | 0 | 0 | 0 | 0 | not sent |
| I2 | 200 | 200 | 200 | 0 | 0 | 0 | 0 | 0 | not sent |
| I3 | 200 | 115 | 0 | 115 | 0 | 0 | 85 | 0 | not sent |

- Datasets did not resolve three name classes that the legacy tool resolved: `authority` (N6), non-GenBank
  `common name` (N8; GenBank common names in N7 still resolve) and `in-part` (N10). E-utilities still resolved
  most of them.
- Controls agree: N1 and I1. Merged taxids (I2) all agree, so Datasets follows merges.
- Neither tool resolved the disambiguated unique-name strings (N3) or type-material names (N12).
- Every census input that Datasets did not resolve (LOST or BOTH_NONE) came back with an error reason containing
  "is not a recognized NCBI Taxonomy name": 695/695 census non-results.
- **Partial results (in-part and others).** The census has 17 COLLAPSED (N2 5, N7 2, N10 10) and 1 CHANGED. Most
  COLLAPSED cases are Datasets returning one taxon where the legacy tool also listed other taxa that carry the same
  string in another name class (e.g. `Scrophulariaceae`, `Olacaceae`, `Symphyta`, `elk`). One is a homonym
  between two primary taxa: for `Hoffmania` the legacy tool lists 35910 and 58275, both code 1+; Datasets returns only 58275,
  with no sign that a second taxon exists.
- **The one CHANGED input, `Inflabilis barati` (N10).** `names.dmp` holds this string only as an `in-part` name of
  taxid 1528 (*Eubacterium barkeri*). Results: legacy 1528 (code 2), Datasets 1561 (Clostridium baratii), E-utilities 1528.
  We do not judge which taxon is right; we report that Datasets returned a taxon that `names.dmp` does not link to
  this string, with no warning.
- **I3 (deleted taxids) is not a real loss.** The legacy tool answered code 3 for 115 and code 4 for 85 of them.
  Our rule maps code 3 to the input taxid, which makes those 115 count as LOST. It shows that the legacy tool still
  reports those deleted IDs with code 3, not that Datasets lost a live taxon. Datasets returned the
  not-recognized reason for all 200 deleted taxids.

## Result 2: real verbatim names (frame R)

1,000 distinct verbatim names from 191 GBIF datasets.

| Label | Inputs |
|---|---|
| AGREE | 611 |
| LOST | 111 |
| BOTH_NONE | 277 |
| MISSING_L | 1 |
| CHANGED | 0 |
| COLLAPSED | 0 |

Share of legacy-resolved inputs that Datasets did not resolve: 111/722 = 15.4%.

**Read this next to the publisher caveat.** 101 of the 111 LOST inputs come from one GBIF dataset,
`75956ee6-1a2b-4fa3-b3e8-ccda64ce6c2d` ("INPN - Données flore des CBN agrégées par la FCBN"), which writes names as
`Genus species Author, Year` (for example `Galium mollugo L., 1753`). The legacy tool resolves such a string when
NCBI holds that exact string as an `authority` name; Datasets does not. Without that one dataset the share is
10/621 = 1.6%. Only 10 datasets contribute any LOST input. The frame R figure therefore says more about that
publisher's name format than about real lists in general.

- No silent changes in frame R: CHANGED + COLLAPSED = 0. Every Datasets failure in frame R was a loud
  not-recognized message: 388/388 Datasets non-results (LOST and BOTH_NONE) carry
  "is not a recognized NCBI Taxonomy name". None silently resolved to another taxon in frame R.
- 287 inputs with an authorship pattern: LOST 109, BOTH_NONE 178, AGREE 0 (pattern: a `(`, a four-digit year, or an
  uppercase word after the first two words). Legacy matching is exact: `Origanum vulgare L.` without a year
  resolves in neither tool because NCBI does not hold that exact string.
- 107 of the 111 LOST inputs are an exact (case-insensitive) `names.dmp` name; the other 4 are resolved by the
  legacy tool from knowledge not in `names.dmp`.
- LOST by kingdom of the GBIF draw: Plantae 108, Fungi 3, Animalia 0.
- E-utilities returned the legacy taxid set for 699/722 legacy-resolved inputs, and for 88/111 of the Datasets-LOST
  inputs.

## Limitations

- Executed once, on our own hardware, on the dates above. A later rerun by us with a separately written client on
  a random subsample of these inputs gave the same labels. That rerun is our own check, not an outside
  reproduction. Services may behave differently now.
- The web page was not driven at scale. In one logged-out browser check on 2026-10-12, the page sent the same
  `dataset_report` POST; unrecognized names appeared as rows with blank name, TaxID and rank cells and no reason text.
  So the failure is loud in the API but shows only as an empty row on the page.
- Legacy matching is exact-string. The legacy tool echoes some names with a leading bracket or quote removed:
  10 inputs (N1 1, N4 5, N10 3, R 1) are MISSING_L; all 10 begin with `[`, `(`, `"` or `'`.
- The I3 code-3 result is a labelling artifact (above).
- E-utilities was called with plain terms, so automatic term mapping applies and E can exceed L for free text.
  `retmax=50` caps the idlist: 2 inputs had more than 50 matches, so their E set is incomplete.
- N and I strata are not usage-weighted. Frame R is GBIF publishers' verbatim names, not lists people paste into
  the check tool; the record at a drawn offset follows GBIF's index order, which is arbitrary rather than random;
  and one publisher dominates the loss.

## Files

| File | Contents |
|---|---|
| `inputs/N1.txt` ... `inputs/N12.txt`, `inputs/I1.txt` ... `inputs/I3.txt`, `inputs/R.txt` | inputs per stratum, in the order sent |
| `inputs/strata.csv` | stratum descriptions, sampling pool and pool size |
| `inputs/R_draws.csv` | every GBIF draw behind frame R: draw number, kingdomKey, year, partition count, offset, occurrence key, datasetKey, verbatim name |
| `results/per_input.csv` | 3,450 rows, one per input (columns below) |
| `results/gbif_datasets.csv` | every GBIF dataset in frame R with title, publisher, license and DOI, read from the GBIF API on 2026-10-16 |
| `results/requests.csv` | every legacy and Datasets POST: stratum, batch start and size, HTTP status, UTC time, whether used |
| `method.md` | endpoints, parameters, request rates, frame construction and labelling rules |
| `check.py` | recomputes every number in this README from the files above (standard library only) |
| `LICENSE.md` | licenses and data sources |

`results/per_input.csv` columns: `stratum`, `position` (1-based order sent), `input`, `label`, `legacy_taxids`,
`legacy_codes` (in legacy row order), `legacy_rows`, `datasets_taxids`, `datasets_names` (current scientific
name), `datasets_error` (full reason text), `eutils_term` (the term sent), `eutils_query_translation`,
`eutils_count`, `eutils_taxids`, `in_dump`, and for frame R `gbif_occurrence_key`, `gbif_dataset_key`,
`gbif_dataset_license`, `gbif_kingdom`, `gbif_draw`. Multiple values are separated by `;`.

## Data licenses

Frame R names carry their GBIF dataset's license. By input:

| License | Frame R inputs | Datasets |
|---|---|---|
| CC-BY-4.0 | 544 | 108 |
| CC0-1.0 | 195 | 25 |
| CC-BY-NC-4.0 | 261 | 58 |

The CC BY-NC 4.0 inputs (AGREE 208, LOST 2, BOTH_NONE 51) stay under that license and are shared here for
non-commercial research use. See `LICENSE.md` for the other files.

## Check

```
python3 check.py
```

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections: hello@cybernative.ai.
