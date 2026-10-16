# Method

The method below was written down before any frame input was sent to any service. Two execution changes made
during the run are listed under "Run changes"; neither changed a frame, rule or metric. All code was Python 3.12,
standard library only, calling public HTTP endpoints without an API key or account.

## Frames

### N strata (names)

From `names.dmp` of the 2026-10-11 `taxdump.tar.gz` (SHA-256 in the README), the pool of each stratum is the set of
distinct name strings of one name class:

| Stratum | names.dmp class | Pool |
|---|---|---|
| N1 | scientific name | names whose unique-name field is empty |
| N2 | scientific name | names whose unique-name field is set; the bare name is sent |
| N3 | scientific name | the unique-name string itself, e.g. `Agathis montana (in: seed plants)` |
| N4 | synonym | all |
| N5 | equivalent name | all |
| N6 | authority | all |
| N7 | genbank common name | all |
| N8 | common name | all |
| N9 | includes | all |
| N10 | in-part | all |
| N11 | acronym | all |
| N12 | type material | all |

Sample sizes are in `inputs/strata.csv`. Sampling: one `random.Random(12998)` generator, then for each stratum in
the order N1..N12, `rng.sample(sorted(pool), k)`. The inputs are listed in sample order.

Before the main run we sent a short pilot list of names and taxids to the services (the legacy tool's own demo
list, `Bacillus coli`, `Homo sapien`, `human`, and taxids 1–12). Those inputs were removed from every pool
(case-insensitive) so that no frame contains a name already seen.

### I strata (taxids)

Pools: I1 the taxids of `nodes.dmp`, I2 the old taxids of `merged.dmp`, I3 the taxids of `delnodes.dmp`, each
without taxids 1–12. A fresh `random.Random(12998)` samples 200 from each pool (sorted numerically) in the order
I1, I2, I3.

### Frame R (GBIF verbatim names)

For draw i = 0, 1, 2, ...: `rng = random.Random(f"12998-{i}")`; kingdomKey = `rng.choice([1, 6, 5])`
(Animalia, Plantae, Fungi); year = `rng.randint(1990, 2025)`. The record count of
`https://api.gbif.org/v1/occurrence/search?kingdomKey=<k>&year=<y>&limit=0` is read; offset =
`rng.randrange(min(count, 100000))`; the record at that offset (`...&limit=1&offset=<offset>`) gives the occurrence
key; `https://api.gbif.org/v1/occurrence/<key>/verbatim` gives `http://rs.tdwg.org/dwc/terms/scientificName`, with
surrounding whitespace removed. Frame R is the first 1,000 distinct non-empty strings in draw order (draws
0–1,238; `inputs/R_draws.csv`). The datasetKey of an input is that of the first draw that produced it.
GBIF requests were kept at or below 2 per second.

## Arms

| Arm | Request | Batch | Rate |
|---|---|---|---|
| Legacy | POST `multipart/form-data` to `https://www.ncbi.nlm.nih.gov/Taxonomy/TaxIdentifier/tax_identifier.cgi` with fields `tax` (inputs joined by LF) and `button=Save in file`; redirects not followed | 200 inputs; names and taxids in separate POSTs | at least 5 s between POSTs |
| Datasets | POST `https://api.ncbi.nlm.nih.gov/datasets/v2/taxonomy/dataset_report`, body `{"taxons": [...], "page_size": 1000}`, following `next_page_token` if present | 100 inputs | at least 1 s between POSTs |
| E-utilities | GET `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi` with `db=taxonomy`, `term=<input>`, `retmode=json`, `retmax=50` | 1 input; name strata only | at most 3 requests per second |

Legacy and Datasets requests carried a generic desktop-browser `User-Agent` string; E-utilities requests carried
the default Python `urllib` agent and no `tool` or `email` parameter. The run would have stopped after three
consecutive failed, redirected or unparseable legacy batches; that did not happen. A Datasets batch that failed as a
whole would have been re-sent one input at a time; none failed.

## Labelling

`norm(s)` = Unicode NFC, whitespace runs collapsed to one space, case-folded.

- **Legacy.** The response is a pipe-separated table whose header line starts with `code`. Rows are aligned to the
  inputs of their POST in order: each row is assigned to the next input (at or after the current position) whose
  `norm` equals the `norm` of the row's echoed name. An input with no aligned row is MISSING_L. For names, L is the
  set of taxids on rows whose code starts with `1` or `2` (a `+` marks a name with several taxa). For taxids, code
  1 gives the input taxid, code 2 the primary taxid in the third column, code 3 (taxid exists, no public sequence)
  the input taxid, code 4 (not found) nothing. The input counts as ambiguous when it has more than one row.
- **Datasets.** For each report, every string in its `query` list is keyed by `norm`; D is the set of
  `taxonomy.tax_id` over that input's reports, `datasets_names` their `current_scientific_name.name`, and
  `datasets_error` every `errors[].reason`.
- **E-utilities.** E is `esearchresult.idlist`; `querytranslation` and `count` are kept.
- **Label.** AGREE: L = D, both non-empty. LOST: L non-empty, D empty. GAINED: L empty, D non-empty (none occurred).
  COLLAPSED: ambiguous in legacy and D a strict non-empty subset of L. CHANGED: both non-empty, unequal, not
  COLLAPSED. BOTH_NONE: both empty.
- **in_dump.** `yes` when `norm(input)` equals `norm` of some `names.dmp` name or unique name.
- **Authorship pattern** (README, frame R): the regular expression `(\(|\b[12][0-9]{3}\b|^\S+\s+\S+\s+[A-Z])`.

## Run changes

- Serial fetching from GBIF and E-utilities was slower than planned, so the same requests were sent from a small
  thread pool under the same global rate ceilings. Draws are still defined by draw number and assembled in draw
  order.
- About a minute of local DNS failure interrupted 3 GBIF draws and 12 E-utilities requests (N3 3, N4 9). The 3 draws
  were repeated with the same draw number and offset; the 12 E-utilities requests were re-sent and the re-sent
  answers are used.
- One legacy POST (N5) returned HTTP 502 and was re-sent once (see `results/requests.csv`).
- E-utilities on frame R was sent on 2026-10-12 between 03:04 and 03:11 UTC, after a host DNS outage; the other
  E-utilities requests were sent within the 2026-10-11 23:43 to 2026-10-12 00:36 UTC window of the other arms. These times are
  from our run notes; E-utilities responses were not time-stamped individually.

## Browser check of the page

On 2026-10-12 around 03:26 UTC a logged-out desktop Chrome session opened `https://www.ncbi.nlm.nih.gov/datasets/taxonomy/check/`
and typed 20 inputs from these frames (10 authorship strings, 5 common names, 5 controls) into the textarea. The page
sent one POST to `datasets/api/datasets/v2/taxonomy/dataset_report` with the 20 lines. The 15 names that the API
does not recognize appeared as rows with empty name, TaxID and rank cells, with no reason text and listed first;
the 5 controls resolved to the same TaxIDs as the API.
