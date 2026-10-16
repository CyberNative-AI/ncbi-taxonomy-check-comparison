"""Recompute every number stated in README.md from the files in this repository, and nothing else.

Usage: python3 check.py        (Python 3.8+, standard library only; exits 1 on any mismatch)

Each check computes a value from inputs/ and results/, compares it with the value stated in README.md,
and also confirms that the stated text appears in README.md verbatim.
"""
import collections
import csv
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOP = "75956ee6-1a2b-4fa3-b3e8-ccda64ce6c2d"
NOT_RECOGNIZED = "is not a recognized NCBI Taxonomy name"
AUTH = re.compile(r"(\(|\b[12][0-9]{3}\b|^\S+\s+\S+\s+[A-Z])")
STRATA = ["N1", "N2", "N3", "N4", "N5", "N6", "N7", "N8", "N9", "N10", "N11", "N12", "I1", "I2", "I3", "R"]
CLASSIFIED = ("AGREE", "LOST", "CHANGED", "COLLAPSED")


def norm(s):
    return " ".join(unicodedata.normalize("NFC", s).split()).casefold()


def ids(s):
    return set(s.split(";")) if s else set()


def label(L, D, ambiguous):
    if L and D:
        if L == D:
            return "AGREE"
        if ambiguous and D < L:
            return "COLLAPSED"
        return "CHANGED"
    if L:
        return "LOST"
    if D:
        return "GAINED"
    return "BOTH_NONE"


def pct(a, b):
    return f"{100 * a / b:.1f}%"


def load():
    with open(HERE / "results" / "per_input.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    with open(HERE / "results" / "gbif_datasets.csv", encoding="utf-8", newline="") as f:
        datasets = list(csv.DictReader(f))
    with open(HERE / "results" / "requests.csv", encoding="utf-8", newline="") as f:
        requests = list(csv.DictReader(f))
    return rows, datasets, requests


def main():
    rows, datasets, requests = load()
    readme = (HERE / "README.md").read_text(encoding="utf-8")
    checks = []  # (description, computed, README text that must contain the computed value)

    def claim(desc, value, text):
        checks.append((desc, str(value), text))

    # Structural checks: inputs files are the rows, in order; labels follow the stated rules.
    by = collections.defaultdict(list)
    for r in rows:
        by[r["stratum"]].append(r)
    assert list(by) == STRATA, list(by)
    for s in STRATA:
        raw = (HERE / "inputs" / f"{s}.txt").read_bytes()
        assert b"\r" not in raw and raw.endswith(b"\n"), s
        lines = raw.decode("utf-8").split("\n")[:-1]
        assert lines == [r["input"] for r in by[s]], s
        assert [int(r["position"]) for r in by[s]] == list(range(1, len(lines) + 1)), s
    relabel_ok = 0
    for r in rows:
        if r["label"] == "MISSING_L":
            assert not r["legacy_codes"], r
            continue
        L, D = ids(r["legacy_taxids"]), ids(r["datasets_taxids"])
        assert label(L, D, int(r["legacy_rows"]) > 1) == r["label"], r["input"]
        relabel_ok += 1
    claim("rows in per_input.csv", len(rows), f"{len(rows):,} rows")
    claim("labels recomputed from TaxID columns", f"{relabel_ok}/{sum(r['label'] != 'MISSING_L' for r in rows)}",
          f"{relabel_ok:,} of {sum(r['label'] != 'MISSING_L' for r in rows):,} labels")

    # Frame R.
    R = by["R"]
    c = collections.Counter(r["label"] for r in R)
    lne = [r for r in R if r["label"] in CLASSIFIED]
    lost = [r for r in R if r["label"] == "LOST"]
    claim("R inputs", len(R), f"{len(R):,} distinct verbatim names")
    for k in ("AGREE", "LOST", "BOTH_NONE", "MISSING_L", "CHANGED", "COLLAPSED"):
        claim(f"R {k}", c[k], f"| {k} | {c[k]} |")
    claim("R loss", f"{len(lost)}/{len(lne)}", f"{len(lost)}/{len(lne)} = {pct(len(lost), len(lne))}")
    claim("R silent (CHANGED+COLLAPSED)", c["CHANGED"] + c["COLLAPSED"], f"CHANGED + COLLAPSED = {c['CHANGED'] + c['COLLAPSED']}")
    top = sum(r["gbif_dataset_key"] == TOP for r in lost)
    claim("R LOST from top dataset", f"{top}/{len(lost)}", f"{top} of the {len(lost)} LOST")
    rest = [r for r in lne if r["gbif_dataset_key"] != TOP]
    rest_lost = sum(r["label"] == "LOST" for r in rest)
    claim("R loss without top dataset", f"{rest_lost}/{len(rest)}", f"{rest_lost}/{len(rest)} = {pct(rest_lost, len(rest))}")
    claim("datasets with a LOST input", len({r["gbif_dataset_key"] for r in lost}), f"{len({r['gbif_dataset_key'] for r in lost})} datasets contribute")
    keys = {r["gbif_dataset_key"] for r in R}
    assert keys == {d["datasetKey"] for d in datasets}
    claim("datasets in frame R", len(keys), f"{len(keys)} GBIF datasets")
    d_empty = [r for r in R if r["label"] in ("LOST", "BOTH_NONE")]
    loud = sum(NOT_RECOGNIZED in r["datasets_error"] and not r["datasets_taxids"] for r in d_empty)
    claim("R Datasets-empty with not-recognized message", f"{loud}/{len(d_empty)}", f"{loud}/{len(d_empty)} Datasets non-results")
    auth = [r for r in R if r["label"] != "MISSING_L" and AUTH.search(r["input"])]
    ca = collections.Counter(r["label"] for r in auth)
    claim("R authorship-pattern inputs", f"{len(auth)}: LOST {ca['LOST']}, BOTH_NONE {ca['BOTH_NONE']}, AGREE {ca['AGREE']}",
          f"{len(auth)} inputs with an authorship pattern: LOST {ca['LOST']}, BOTH_NONE {ca['BOTH_NONE']}, AGREE {ca['AGREE']}")
    ind = sum(r["in_dump"] == "yes" for r in lost)
    claim("R LOST inputs present in names.dmp", f"{ind}/{len(lost)}", f"{ind} of the {len(lost)} LOST inputs")
    ck = collections.Counter(r["gbif_kingdom"] for r in lost)
    claim("R LOST by kingdom", f"Plantae {ck['Plantae']}, Fungi {ck['Fungi']}, Animalia {ck['Animalia']}",
          f"Plantae {ck['Plantae']}, Fungi {ck['Fungi']}, Animalia {ck['Animalia']}")
    e_eq = sum(ids(r["eutils_taxids"]) == ids(r["legacy_taxids"]) for r in lne)
    e_lost = sum(ids(r["eutils_taxids"]) == ids(r["legacy_taxids"]) for r in lost)
    claim("R E-utilities = legacy", f"{e_eq}/{len(lne)}", f"{e_eq}/{len(lne)}")
    claim("R E-utilities = legacy among LOST", f"{e_lost}/{len(lost)}", f"{e_lost}/{len(lost)} of the Datasets-LOST")
    lic = collections.Counter(r["gbif_dataset_license"] for r in R)
    dlic = collections.Counter(d["license"] for d in datasets)
    for k in ("CC-BY-4.0", "CC0-1.0", "CC-BY-NC-4.0"):
        claim(f"R inputs / datasets under {k}", f"{lic[k]} / {dlic[k]}", f"| {k} | {lic[k]} | {dlic[k]} |")
    nc_c = collections.Counter(r["label"] for r in R if r["gbif_dataset_license"] == "CC-BY-NC-4.0")
    claim("CC BY-NC inputs by label", f"AGREE {nc_c['AGREE']}, LOST {nc_c['LOST']}, BOTH_NONE {nc_c['BOTH_NONE']}",
          f"AGREE {nc_c['AGREE']}, LOST {nc_c['LOST']}, BOTH_NONE {nc_c['BOTH_NONE']}")

    # Census strata table.
    for s in STRATA[:-1]:
        rs = by[s]
        cs = collections.Counter(r["label"] for r in rs)
        l_ne = sum(cs[k] for k in CLASSIFIED)
        lo = [r for r in rs if r["label"] == "LOST"]
        if s.startswith("N"):
            el = f"{sum(ids(r['eutils_taxids']) == ids(r['legacy_taxids']) for r in lo)}/{len(lo)}" if lo else "-"
        else:
            el = "not sent"
        row = f"| {s} | {len(rs)} | {l_ne} | {cs['AGREE']} | {cs['LOST']} | {cs['COLLAPSED']} | {cs['CHANGED']} | {cs['BOTH_NONE']} | {cs['MISSING_L']} | {el} |"
        claim(f"census row {s}", row, row)
    census = [r for s in STRATA[:12] for r in by[s]]
    cc = collections.Counter(r["label"] for r in census)
    per = {s: sum(r["label"] == "COLLAPSED" for r in by[s]) for s in STRATA[:12]}
    per = ", ".join(f"{s} {n}" for s, n in per.items() if n)
    claim("census COLLAPSED / CHANGED", f"{cc['COLLAPSED']} ({per}) / {cc['CHANGED']}",
          f"{cc['COLLAPSED']} COLLAPSED ({per}) and {cc['CHANGED']} CHANGED")
    ib = next(r for r in by["N10"] if r["input"] == "Inflabilis barati")
    claim("Inflabilis barati", f"{ib['label']} legacy {ib['legacy_taxids']} code {ib['legacy_codes']}, Datasets {ib['datasets_taxids']} "
          f"{ib['datasets_names']}, E-utilities {ib['eutils_taxids']}",
          f"legacy {ib['legacy_taxids']} (code {ib['legacy_codes']}), Datasets {ib['datasets_taxids']} ({ib['datasets_names']}), "
          f"E-utilities {ib['eutils_taxids']}")
    hf = next(r for r in by["N2"] if r["input"] == "Hoffmania")
    claim("Hoffmania", f"legacy {hf['legacy_taxids']} codes {hf['legacy_codes']}; Datasets {hf['datasets_taxids']}",
          f"the legacy tool lists {hf['legacy_taxids'].replace(';', ' and ')}, both code {hf['legacy_codes'].split(';')[0]}; Datasets returns only {hf['datasets_taxids']}")
    ex = {r["input"]: r["label"] for r in R}
    claim("example Galium mollugo L., 1753", ex["Galium mollugo L., 1753"], "for example `Galium mollugo L., 1753`")
    claim("example Origanum vulgare L.", ex["Origanum vulgare L."], "`Origanum vulgare L.` without a year")
    assert ex["Galium mollugo L., 1753"] == "LOST" and ex["Origanum vulgare L."] == "BOTH_NONE"
    for name, s_ in (("Scrophulariaceae", "N2"), ("Olacaceae", "N2"), ("Symphyta", "N10"), ("elk", "N7")):
        assert next(r for r in by[s_] if r["input"] == name)["label"] == "COLLAPSED", name
    claim("COLLAPSED examples", "COLLAPSED x4", "(e.g. `Scrophulariaceae`, `Olacaceae`, `Symphyta`, `elk`)")
    nn = {s_: collections.Counter(r["label"] for r in by[s_]) for s_ in ("N3", "N12")}
    assert all(set(v) == {"BOTH_NONE"} for v in nn.values())
    claim("N3 and N12 resolved by neither", "BOTH_NONE only", "Neither tool resolved the disambiguated unique-name strings (N3)")
    i3 = collections.Counter(r["legacy_codes"] for r in by["I3"])
    i3_loud = sum(NOT_RECOGNIZED in r["datasets_error"] for r in by["I3"])
    claim("I3 legacy codes", f"code 3 {i3['3']}, code 4 {i3['4']}; Datasets message {i3_loud}/{len(by['I3'])}",
          f"code 3 for {i3['3']} and code 4 for {i3['4']}")
    claim("I3 Datasets message", f"{i3_loud}/{len(by['I3'])}", f"all {i3_loud} deleted taxids")
    names_empty = [r for s in STRATA[:12] for r in by[s] if r["label"] in ("LOST", "BOTH_NONE")]
    nl = sum(NOT_RECOGNIZED in r["datasets_error"] for r in names_empty)
    claim("census Datasets-empty with message", f"{nl}/{len(names_empty)}", f"{nl}/{len(names_empty)} census non-results")
    miss = [r for r in rows if r["label"] == "MISSING_L"]
    pm = collections.Counter(r["stratum"] for r in miss)
    lead = sum(r["input"][:1] in "[(\"'" for r in miss)
    claim("MISSING_L", f"{len(miss)} ({', '.join(f'{k} {v}' for k, v in pm.items())}); leading bracket/quote {lead}",
          f"{len(miss)} inputs ({', '.join(f'{k} {v}' for k, v in pm.items())}) are MISSING_L; all {lead} begin")
    capped = sum(int(r["eutils_count"] or 0) > 50 for r in rows)
    claim("E-utilities results over retmax", capped, f"{capped} inputs had more than 50")

    # Requests.
    for arm in ("legacy", "datasets"):
        rq = [q for q in requests if q["arm"] == arm]
        ok = sum(q["http_status"] == "200" for q in rq)
        t = sorted(q["utc"] for q in rq)
        claim(f"{arm} requests", f"{len(rq)} POSTs, {ok} HTTP 200, {t[0]} to {t[-1]}",
              f"{len(rq)} POSTs ({ok} HTTP 200), {t[0]} to {t[-1]}")

    r502 = [q for q in requests if q["http_status"] != "200"]
    assert len(r502) == 1 and r502[0]["used"] == "no" and r502[0]["stratum"] == "N5"
    claim("legacy non-200 POSTs", f"{len(r502)} ({r502[0]['stratum']} HTTP {r502[0]['http_status']}, not used)",
          f"one {r502[0]['stratum']} POST returned HTTP {r502[0]['http_status']}")

    bad = 0
    for desc, value, text in checks:
        ok = text in readme
        bad += not ok
        print(f"{'OK  ' if ok else 'FAIL'} {desc}: {value}")
        if not ok:
            print(f"     README.md lacks: {text}")
    print(f"{len(checks) - bad}/{len(checks)} README statements match the files")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
