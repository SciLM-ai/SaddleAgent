#!/usr/bin/env python3
"""Trivial prechecks for VASP/VTST transition-state-search file uploads.

A "trivial precheck" is a deterministic, chemistry-agnostic, fast inspection of
the user's uploaded files whose output is fed verbatim into a downstream
debugging agent as preliminary context.

HARD CONTRACT (every check obeys all of these):
  1. NEVER-BLESS. A check only ever emits *positively detected* anomalies (or
     raw facts). It never emits "this is fine / consistent / clean". Silence
     about a dimension must never be read as "checked and OK" -- the runner
     prints, separately, exactly which checks ran and which were N/A, so the
     agent knows what was *not* verified.
  2. RAW OUTPUT ONLY. No interpretation, no fix suggestions, no severity. Facts.
  3. FALSE POSITIVES ARE ACCEPTABLE (the agent will look); FALSE NEGATIVES THAT
     READ AS REASSURANCE ARE NOT. When in doubt, flag or say N/A -- never bless.

This module is standalone. It is NOT wired into the generation agent.
"""

import os
import re
import sys

# A precheck must stay lightweight and never hog the box: cap the BLAS/OpenMP
# thread pools BEFORE importing numpy. The distance scan is many tiny 3x3
# matmuls, where multi-threading only adds oversubscription overhead -- single
# thread is both faster here and a good neighbour to the rest of the machine.
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

try:
    import numpy as np
except ImportError:                                # pragma: no cover
    np = None

# --------------------------------------------------------------------------- #
# Low-level helpers
# --------------------------------------------------------------------------- #

def _read_lines(path):
    try:
        with open(path, "r", errors="replace") as fh:
            return fh.read().splitlines()
    except OSError:
        return None


def _grep_contains(path, needle):
    """Stream-search a file for a literal substring. Returns True/False, or None
    if the file is unreadable. Stops at the first hit (cheap when present)."""
    try:
        with open(path, "r", errors="replace") as fh:
            for line in fh:
                if needle in line:
                    return True
    except OSError:
        return None
    return False


def _head_lines(path, n=20):
    """First n lines of a file (list), or None if unreadable."""
    out = []
    try:
        with open(path, "r", errors="replace") as fh:
            for i, line in enumerate(fh):
                if i >= n:
                    break
                out.append(line)
    except OSError:
        return None
    return out


def _is_compressed(path):
    """True if the file's magic bytes are a common compressor (gzip/zip/bz2/xz)."""
    try:
        with open(path, "rb") as fh:
            magic = fh.read(4)
    except OSError:
        return False
    return (magic[:2] == b"\x1f\x8b" or magic[:2] == b"PK"
            or magic[:3] == b"BZh" or magic[:4] == b"\xfd7zX")


def _is_uint(tok):
    return re.fullmatch(r"\d+", tok) is not None


def _clean_val(tok):
    """First value token, stripped of a trailing ';' and surrounding space."""
    return tok.strip().rstrip(";").strip()


_BOOL_TRUE = {".TRUE.", "TRUE", "T", ".T."}
_BOOL_FALSE = {".FALSE.", "FALSE", "F", ".F."}


def _norm_value(val):
    """Normalize a scalar value string for cross-file comparison.

    Only collapses the many spellings of Fortran booleans (.TRUE./T/TRUE -> T).
    Everything else is compared as its literal stripped string -- so a purely
    cosmetic reformat across VASP versions can cause a (harmless, allowed)
    false-positive flag, but two genuinely different values are never merged.
    """
    v = val.strip()
    up = v.upper()
    if up in _BOOL_TRUE:
        return "T"
    if up in _BOOL_FALSE:
        return "F"
    return v


# Matches a leading "TAG = value..." assignment (tag at start of line). Used for
# both the resolved OUTCAR block and raw INCAR echoes. Captures only the first
# value token; descriptive text after it is ignored.
_TAG_RE = re.compile(r"^\s*(?P<tag>[A-Za-z][A-Za-z0-9_]*)\s*=\s*(?P<val>\S+)")


# --------------------------------------------------------------------------- #
# Parsers
# --------------------------------------------------------------------------- #

def parse_incar(path):
    """Parse an INCAR into {TAG: value_string}. Last assignment of a tag wins
    (VASP semantics). Inline comments (# and !) are stripped; ';'-separated
    assignments on one line are split. Values keep their internal token spacing
    (needed by the list-length check). Returns None if unreadable.
    """
    lines = _read_lines(path)
    if lines is None:
        return None
    tags = {}
    for raw in lines:
        line = raw.split("#", 1)[0].split("!", 1)[0]
        for part in line.split(";"):
            if "=" not in part:
                continue
            key, _, val = part.partition("=")
            key = key.strip().upper()
            if not re.fullmatch(r"[A-Z][A-Z0-9_]*", key):
                continue
            tags[key] = val.strip()
    return tags


def parse_poscar(path):
    """Parse a POSCAR/CONTCAR. Returns a dict or None if structurally unparseable.

    Block-aware: a species line of "Fe Fe O" is kept as three blocks (so an
    antiferromagnetic split is preserved, not collapsed to {Fe, O}).
    Handles VASP4 (no species-symbol line; species=None) and VASP5.

    Keys: path, scale, lattice(3x3), species(list|None), counts(list[int]),
          natoms(int), selective(bool), coord_mode(str), coord_start(int),
          species_count_mismatch(bool), lines(list[str]).
    """
    lines = _read_lines(path)
    if lines is None or len(lines) < 8:
        return None
    try:
        scale = float(lines[1].split()[0])
    except (ValueError, IndexError):
        return None
    lattice = []
    for i in range(2, 5):
        parts = lines[i].split()
        if len(parts) < 3:
            return None
        try:
            lattice.append([float(x) for x in parts[:3]])
        except ValueError:
            return None
    l5 = lines[5].split()
    if not l5:
        return None
    species = None
    species_count_mismatch = False
    if all(_is_uint(t) for t in l5):
        # VASP4: line 5 is already the counts; no element symbols present.
        counts = [int(t) for t in l5]
        idx = 6
    else:
        species = l5
        l6 = lines[6].split()
        if not l6 or not all(_is_uint(t) for t in l6):
            return None
        counts = [int(t) for t in l6]
        idx = 7
        if len(species) != len(counts):
            species_count_mismatch = True
    natoms = sum(counts)
    selective = False
    if idx < len(lines) and lines[idx].strip()[:1] in ("S", "s"):
        selective = True
        idx += 1
    coord_mode = lines[idx].strip() if idx < len(lines) else ""
    return {
        "path": path,
        "scale": scale,
        "lattice": lattice,
        "species": species,
        "counts": counts,
        "natoms": natoms,
        "selective": selective,
        "coord_mode": coord_mode,
        "coord_start": idx + 1,
        "species_count_mismatch": species_count_mismatch,
        "lines": lines,
    }


def parse_outcar_params(path, tags):
    """Extract resolved + raw values for `tags` from an OUTCAR.

    Returns {TAG: (value_str, source)} where source is 'resolved' or 'raw', or
    None if the file is unreadable, or {} if no parameter regions were found.

    'resolved' = the post-'Startparameter for this run:' echo (defaults filled
    in, ALGO normalized to IALGO). 'raw' = the verbatim ' INCAR:' dump near the
    top. Resolved wins when both exist; raw is the fallback that catches tags
    VASP only prints when explicitly set (e.g. IVDW). The raw INCAR dump is
    parsed ONLY inside its own block so it can never leak into resolved values.
    """
    try:
        fh = open(path, "r", errors="replace")
    except OSError:
        return None
    resolved, raw = {}, {}
    in_incar = False
    in_resolved = False
    with fh:
        for line in fh:
            stripped = line.strip()
            if not in_resolved and stripped == "INCAR:":
                in_incar = True
                continue
            if in_incar:
                if stripped == "":
                    in_incar = False
                    continue
                if stripped.startswith("POTCAR:"):
                    in_incar = False
                    # fall through; this line is not a tag assignment
                else:
                    m = _TAG_RE.match(line)
                    if m:
                        tag = m.group("tag").upper()
                        if tag in tags and tag not in raw:
                            raw[tag] = _clean_val(m.group("val"))
                    continue
            if "Startparameter for this run:" in line:
                in_resolved = True
                continue
            if in_resolved:
                # The resolved dump lives entirely before the first SCF
                # iteration; stop there to avoid per-step reprints.
                if "Iteration" in line:
                    break
                m = _TAG_RE.match(line)
                if m:
                    tag = m.group("tag").upper()
                    if tag in tags and tag not in resolved:
                        resolved[tag] = _clean_val(m.group("val"))
    merged = {}
    for tag in tags:
        if tag in resolved:
            merged[tag] = (resolved[tag], "resolved")
        elif tag in raw:
            merged[tag] = (raw[tag], "raw")
    return merged


def parse_potcar_titels(path):
    """Ordered list of TITEL strings from a POTCAR (one per species block, in
    order). Returns None if unreadable, [] if none found."""
    lines = _read_lines(path)
    if lines is None:
        return None
    titels = []
    for line in lines:
        m = re.match(r"\s*TITEL\s*=\s*(.+?)\s*$", line)
        if m:
            titels.append(m.group(1).strip())
    return titels


# --------------------------------------------------------------------------- #
# Curated reference sets
# --------------------------------------------------------------------------- #

# Electronic-structure / numerical-accuracy / XC tags that must match between
# endpoint relaxations and the NEB band for energies to be comparable. Ionic
# control tags (IBRION/NSW/EDIFFG/POTIM/IMAGES/SPRING/IOPT/...) are deliberately
# EXCLUDED -- they legitimately differ between an endpoint relax and the band.
# GGA is intentionally EXCLUDED: a resolved "GGA = --" means "use the POTCAR's
# LEXCH", so a mechanical string diff (-- vs PE) is unreliable without resolving
# the POTCAR. The XC functional is instead handed to the agent via _XC_DIRECTIVE.
CONSISTENCY_TAGS = [
    "ISPIN", "ICHARG", "ENCUT", "PREC", "EDIFF", "IALGO", "ISYM",
    "GGA_COMPAT", "LMAXMIX", "LREAL", "LASPH", "METAGGA", "LNONCOLLINEAR",
    "LSORBIT", "ISMEAR", "SIGMA", "IVDW", "LHFCALC", "AEXX", "HFSCREEN",
    "NELECT", "NUPDOWN", "VOSKOWN", "ENAUG", "ADDGRID", "LDAU", "LDAUTYPE",
    "LDAUL", "LDAUU", "LDAUJ", "AMIX", "AMIX_MAG",
]

# Handed to the downstream agent in place of a mechanical GGA diff.
_XC_DIRECTIVE = (
    "NOTE for downstream agent: the XC functional (GGA / POTCAR LEXCH) is NOT "
    "diffed here -- a resolved 'GGA = --' means 'use the POTCAR default', which "
    "needs the POTCAR to resolve, so a string diff is unreliable. Verify "
    "yourself that the XC functional matches between endpoints and band.")

# Tags that VASP requires to be integers -- a fractional value is unambiguously
# a typo VASP will fail to read. Conservative: only unambiguous integer tags.
CERTAIN_INT_TAGS = {
    "ISPIN", "ICHARG", "ISTART", "INIWAV", "IBRION", "ISIF", "NSW", "NELM",
    "NELMIN", "NELMDL", "ISYM", "IALGO", "NPAR", "NCORE", "KPAR", "LMAXMIX",
    "IVDW", "ISMEAR", "LORBIT", "NSIM", "IMIX", "IDIPOL", "NEDOS", "ICHAIN",
    "IOPT", "IMAGES", "NFREE", "IWAVPR", "VOSKOWN", "NBANDS", "LMAXPAW",
    "LDAUTYPE", "NWRITE", "ISPIND", "INIMIX", "MAXMIX", "NUPDOWN_IS_INT_NO",
}
# (NUPDOWN can be -1/float in some setups -> excluded above intentionally.)

# INCAR tags whose presence means the user is asking for a VTST run/optimizer
# (NEB band, dimer/Lanczos chain, or a VTST IOPT optimizer). Surfaced raw next
# to the OUTCAR VTST-banner status so the agent can join them.
VTST_INTENT_TAGS = ["IMAGES", "SPRING", "LCLIMB", "ICHAIN", "IOPT", "LNEBCELL"]

# Per-cardinality INCAR list tags.
PER_ATOM_TAGS = ["MAGMOM"]                     # length == NIONS (x3 if noncollinear)
PER_SPECIES_TAGS = ["LDAUU", "LDAUJ", "LDAUL", "VDW_C6", "VDW_R0",
                    "VDW_RADIUS", "ROPT"]      # length == number of species blocks


# --------------------------------------------------------------------------- #
# Value-list expansion (n*val repeat syntax)
# --------------------------------------------------------------------------- #

def count_values(value_str):
    """Count VASP value-list entries, expanding 'n*val' repeats.

    Handles spaces around '*' ("3 * 0.0"), and multiple groups
    ("3*5 2*0 1.0" -> 6). Returns the integer count, or None if any token is
    malformed (so the caller stays silent rather than guessing == never-bless).
    """
    s = re.sub(r"\s*\*\s*", "*", value_str.strip())
    if s == "":
        return 0
    total = 0
    for tok in s.split():
        if "*" in tok:
            n, _, _v = tok.partition("*")
            if not _is_uint(n) or _v == "":
                return None
            total += int(n)
        else:
            total += 1
    return total


# --------------------------------------------------------------------------- #
# Checks  (each returns a list of raw finding strings; [] == nothing detected)
# --------------------------------------------------------------------------- #

def check_incar_hygiene(incar_path):
    """Flag character/whitespace/format problems in an INCAR that silently break
    VASP's parser. Never-bless: only positively detected anomalies are emitted.
    """
    out = []
    lines = _read_lines(incar_path)
    if lines is None:
        return out
    rel = incar_path
    for n, line in enumerate(lines, 1):
        # Only the active (pre-comment) part matters: VASP ignores everything
        # after '#'/'!', so a tab inside a comment is harmless. The classic
        # breakage is a tab in the actual "TAG = value" text (e.g. IOPT=1<tab>).
        active = line.split("#", 1)[0].split("!", 1)[0]
        for ch, name in (("\t", "tab"), ("\xa0", "non-breaking-space"),
                         ("\r", "carriage-return"), ("\x0b", "vertical-tab"),
                         ("\x0c", "form-feed")):
            if ch in active:
                out.append(
                    f"{rel}:{n}: {name} character in the active (pre-comment) "
                    f"part of the line (VASP INCAR parser may misread it)")
    tags = parse_incar(incar_path) or {}
    for tag, val in tags.items():
        if tag in CERTAIN_INT_TAGS:
            first = val.split()[0] if val.split() else ""
            try:
                f = float(first)
            except ValueError:
                continue
            if f != int(f):  # has a nonzero fractional part
                out.append(
                    f"{rel}: integer tag {tag} has a non-integer value "
                    f"'{first}' (VASP reads {tag} as an integer)")
    return out


def check_ediffg_sign(incar_path):
    """Report EDIFFG's raw value and sign class. Pure fact -- it does NOT assert
    that any sign is wrong (positive is correct for a plain endpoint relax)."""
    tags = parse_incar(incar_path)
    if tags is None:
        return []
    if "EDIFFG" not in tags:
        return [f"{incar_path}: EDIFFG not set (VASP defaults to energy-based, "
                f"= +10*EDIFF)"]
    raw = tags["EDIFFG"].split()[0] if tags["EDIFFG"].split() else ""
    try:
        v = float(raw)
    except ValueError:
        return [f"{incar_path}: EDIFFG = '{raw}' (unparseable as a number)"]
    sign = "negative/force-based" if v < 0 else (
        "zero" if v == 0 else "positive/energy-based")
    return [f"{incar_path}: EDIFFG = {raw} ({sign})"]


def check_list_lengths(incar_path, poscar):
    """Flag per-species / per-atom INCAR list tags whose entry count (after
    n*val expansion) does not match the cardinality implied by the POSCAR.
    Length only -- values are not validated. Never-bless: a matching length is
    NOT reported (a right count can still hold wrong values)."""
    out = []
    tags = parse_incar(incar_path)
    if tags is None or poscar is None:
        return out
    nblocks = len(poscar["counts"])
    natoms = poscar["natoms"]
    noncollinear = (_norm_value(tags.get("LNONCOLLINEAR", "F")) == "T" or
                    _norm_value(tags.get("LSORBIT", "F")) == "T")
    for tag in PER_SPECIES_TAGS:
        if tag in tags:
            c = count_values(tags[tag])
            if c is not None and c != nblocks:
                out.append(
                    f"{incar_path}: {tag} has {c} entries but POSCAR "
                    f"({poscar['path']}) has {nblocks} species block(s)")
    for tag in PER_ATOM_TAGS:
        if tag in tags:
            c = count_values(tags[tag])
            if c is None:
                continue
            expected = 3 * natoms if noncollinear else natoms
            if c != expected:
                expect = (f"{expected} (noncollinear, 3x{natoms})"
                          if noncollinear else f"{expected}")
                out.append(
                    f"{incar_path}: {tag} has {c} entries but POSCAR "
                    f"({poscar['path']}) has {natoms} atom(s); expected {expect}")
    return out


def check_poscar_format(poscar):
    """Flag positively-detected POSCAR structural anomalies. Never-bless: emits
    nothing for a clean file and never asserts validity."""
    if poscar is None:
        return []
    out = []
    p = poscar["path"]
    if poscar["species_count_mismatch"]:
        out.append(f"{p}: species-symbol count != species-count count "
                   f"(line 6 vs line 7 mismatch)")
    cm = poscar["coord_mode"][:1].upper()
    if cm not in ("D", "C", "K"):
        out.append(f"{p}: coordinate-mode line is '{poscar['coord_mode']}' "
                   f"(expected Direct/Cartesian keyword)")
    lines = poscar["lines"]
    start = poscar["coord_start"]
    natoms = poscar["natoms"]
    if len(lines) - start < natoms:
        out.append(f"{p}: only {len(lines) - start} line(s) after the "
                   f"coordinate header but {natoms} atom(s) declared")
    # Coordinate-line content: first 3 tokens must be real numbers; flag NaN/Inf
    # and non-numeric leading tokens (e.g. element labels prepended to coords).
    nan_re = re.compile(r"^[+-]?(nan|inf|infinity)$", re.IGNORECASE)
    for i in range(start, min(start + natoms, len(lines))):
        toks = lines[i].split()
        if len(toks) < 3:
            out.append(f"{p}:{i+1}: coordinate line has < 3 tokens "
                       f"('{lines[i].strip()}')")
            continue
        for t in toks[:3]:
            if nan_re.match(t):
                out.append(f"{p}:{i+1}: NaN/Inf in coordinates "
                           f"('{lines[i].strip()}')")
                break
            try:
                float(t)
            except ValueError:
                out.append(f"{p}:{i+1}: non-numeric token '{t}' where a "
                           f"coordinate number is expected "
                           f"('{lines[i].strip()}')")
                break
    # Scan velocity / trailing blocks too (NaN velocities are a known failure).
    for i in range(start + natoms, len(lines)):
        for t in lines[i].split():
            if nan_re.match(t):
                out.append(f"{p}:{i+1}: NaN/Inf in trailing (velocity?) block")
                break
    return out


def check_settings_consistency(outcar_paths, incar_paths, root):
    """Flag electronic/accuracy/XC tags whose resolved value differs across the
    uploaded runs (endpoints vs band). Primary source: OUTCAR resolved block;
    falls back to raw INCAR text (with a caveat) only when <2 OUTCARs parse.

    Returns (findings, status) where status is a short string the runner prints
    so the agent knows the basis (and what was NOT done). Never-bless: only
    differing tags are listed, and the status names exactly which tags were
    compared so 'not listed' is never read as 'consistent'.
    """
    # Per-file value maps from OUTCARs (resolved|raw merged).
    file_vals = {}     # label -> {tag: value}
    sources = {}       # label -> {tag: 'resolved'|'raw'}
    for path in sorted(outcar_paths):
        merged = parse_outcar_params(path, set(CONSISTENCY_TAGS))
        if not merged:
            continue
        label = _label(path, root)
        file_vals[label] = {t: _norm_value(v) for t, (v, _s) in merged.items()}
        sources[label] = {t: s for t, (_v, s) in merged.items()}

    basis = "OUTCAR resolved block"
    caveat = ""
    if len(file_vals) < 2:
        # Fallback: compare raw INCAR text across >=2 INCARs.
        file_vals, sources = {}, {}
        for path in sorted(incar_paths):
            tags = parse_incar(path)
            if not tags:
                continue
            label = _label(path, root)
            file_vals[label] = {t: _norm_value(tags[t].split()[0])
                                for t in CONSISTENCY_TAGS
                                if t in tags and tags[t].split()}
            sources[label] = {t: "incar" for t in file_vals[label]}
        basis = "raw INCAR text"
        caveat = ("  CAVEAT: no >=2 OUTCARs to compare; defaults "
                  "(e.g. LREAL<-PREC, ENCUT<-POTCAR) are UNRESOLVED, so a "
                  "non-difference here is NOT a consistency guarantee.")

    if len(file_vals) < 2:
        return ([], "N/A: fewer than 2 comparable runs (need >=2 OUTCARs, or "
                ">=2 INCARs)")

    labels = sorted(file_vals)
    findings = []
    for tag in CONSISTENCY_TAGS:
        present = [lab for lab in labels if tag in file_vals[lab]]
        if not present:
            continue
        seen = {}
        for lab in labels:
            seen[lab] = file_vals[lab].get(tag, "<absent>")
        if len(set(seen.values())) > 1:
            parts = " ".join(f"{lab}={seen[lab]}" for lab in labels)
            findings.append(f"{tag}: {parts}")

    status = (f"basis={basis}; compared {len(labels)} run(s) "
              f"[{', '.join(labels)}]; tags compared = "
              f"{','.join(CONSISTENCY_TAGS)} (NOT exhaustive -- only these "
              f"tags were diffed){caveat}")
    return findings, status


def check_vtst_linkage(outcar_paths, incar_paths, root):
    """RAW FACT SURFACER (no conclusion): is the 'VTST' startup banner present in
    each OUTCAR, and which VTST/NEB tags appear in the INCAR(s)?

    The point is to make an ABSENCE explicit. A bare `grep VTST OUTCAR` returns
    nothing when the code is not linked, and an empty result is easily read as
    'no information' and dropped -- this states it in words instead. It does NOT
    conclude 'not linked = the bug': the interpretation (was VTST actually
    needed? CG lives in both plain VASP and VTST; a present-but-old banner is a
    different case) is the agent's job.
    """
    found, absent = [], []
    for path in sorted(outcar_paths):
        has = _grep_contains(path, "VTST")
        if has is None:
            continue
        (found if has else absent).append(_label(path, root))
    n = len(found) + len(absent)
    if n == 0:
        return []
    out = [f'"VTST" startup banner across {n} OUTCAR(s):']
    out.append("  FOUND  in: " + (",".join(found) if found else "(none)"))
    suffix = f"   (ALL {n})" if absent and not found else ""
    out.append("  ABSENT in: " + (",".join(absent) if absent else "(none)") + suffix)
    hits = []
    for path in sorted(incar_paths):
        tags = parse_incar(path) or {}
        present = [(t, (tags[t].split() or [""])[0])
                   for t in VTST_INTENT_TAGS if t in tags]
        if present:
            hits.append(f"{_label(path, root)}: " +
                        ", ".join(f"{t}={v}" for t, v in present))
    # Always state the INCAR side too -- a bare "banner absent" with no context
    # could anchor the agent on a non-issue for a plain (non-VTST) run. The
    # juxtaposition ("absent" + "none of these tags requested") disambiguates
    # without the precheck judging whether VTST was intended.
    if hits:
        out.append("VTST/NEB tags present in INCAR -- " + " | ".join(hits))
    elif incar_paths:
        out.append("VTST/NEB tags present in INCAR -- (none of %s)"
                   % "/".join(VTST_INTENT_TAGS))
    else:
        out.append("VTST/NEB tags in INCAR -- (no INCAR uploaded to check)")
    return out


_VASP_VER_RE = re.compile(r"\bvasp\.\S+")


def check_binary_version(outcar_paths, root):
    """RAW FACT SURFACER (no conclusion): per-OUTCAR VASP version + build kind
    (gamma-only / complex / serial), and a flag if the VASP version string is not
    identical across all OUTCARs (endpoints relaxed with a different binary than
    the band -- the 16188 case). The agent decides whether any of it matters."""
    rows, versions = [], set()
    for path in sorted(outcar_paths):
        head = _head_lines(path, 20)
        if not head:
            continue
        line0 = head[0]
        m = _VASP_VER_RE.search(line0)
        ver = m.group(0) if m else "?"
        versions.add(ver)
        kind = ("gamma-only" if "gamma-only" in line0
                else "complex" if "complex" in line0 else None)
        serial = any("serial version" in ln for ln in head)
        tags = [t for t in (kind, "serial" if serial else None) if t]
        rows.append(f"  {_label(path, root)}: {ver}" +
                    (f"  [{', '.join(tags)}]" if tags else ""))
    if not rows:
        return []
    out = ["VASP build per OUTCAR:"] + rows
    if len(versions) > 1:
        out.append(f"  DIFFER: more than one VASP version across OUTCARs: "
                   f"{sorted(versions)}")
    return out


def check_convergence(outcar_paths, root):
    """RAW FACT SURFACER (absence signal): which OUTCARs printed 'reached required
    accuracy' (ionic convergence) and which did NOT. Absent in an endpoint dir
    (00/NN) => that endpoint never relaxed; absent in a band image => it hit the
    NSW cap. States it explicitly so a blank result is not mistaken for 'no info'.
    No conclusion."""
    yes, no = [], []
    for path in sorted(outcar_paths):
        r = _grep_contains(path, "reached required accuracy")
        if r is None:
            continue
        (yes if r else no).append(_label(path, root))
    n = len(yes) + len(no)
    if n == 0:
        return []
    out = ["'reached required accuracy' (ionic convergence) per OUTCAR:"]
    out.append("  PRESENT in: " + (",".join(yes) if yes else "(none)"))
    suffix = f"   (ALL {n})" if no and not yes else ""
    out.append("  ABSENT  in: " + (",".join(no) if no else "(none)") + suffix)
    return out


def check_scf_convergence(outcar_paths, root):
    """RAW FACT SURFACER: OUTCARs whose SCF hit NELM without converging ('EDIFF
    was not reached') -- those ionic steps give forces from a non-self-consistent
    density. No conclusion."""
    hits = [_label(p, root) for p in sorted(outcar_paths)
            if _grep_contains(p, "EDIFF was not reached")]
    if not hits:
        return []
    return ["SCF did not reach EDIFF ('EDIFF was not reached') in: "
            + ",".join(hits)]


def check_analysis_files(root):
    """RAW FACT SURFACER: numbered image dirs whose OUTCAR is compressed, or
    present only as a compressed variant -- VTST post-processing silently skips
    these. No conclusion."""
    out = []
    for dirpath, dirnames, _files in os.walk(root):
        for d in sorted(dirnames):
            if not re.fullmatch(r"\d\d", d):
                continue
            ddir = os.path.join(dirpath, d)
            lab = os.path.relpath(ddir, root)
            oc = os.path.join(ddir, "OUTCAR")
            if os.path.exists(oc):
                if _is_compressed(oc):
                    out.append(f"{lab}/OUTCAR has compressor magic bytes -- "
                               f"decompress before VTST post-processing")
            else:
                comp = sorted(g for g in os.listdir(ddir)
                              if g.startswith("OUTCAR") and g != "OUTCAR")
                if comp:
                    out.append(f"{lab}/ has no plain OUTCAR but has {comp} -- "
                               f"decompress before post-processing")
    return out


NOTABLE_INCAR_FLAGS = ["LDIPOL", "IDIPOL", "DIPOL", "PSTRESS", "LSOL"]


def check_notable_incar_flags(incar_paths, root):
    """RAW FACT SURFACER: presence (with value) of INCAR tags carrying known NEB
    gotchas -- dipole correction, applied pressure, implicit solvation. Lists
    them so the agent weighs them; no conclusion."""
    out = []
    for path in sorted(incar_paths):
        tags = parse_incar(path) or {}
        present = [(t, (tags[t].split() or [""])[0])
                   for t in NOTABLE_INCAR_FLAGS if t in tags]
        if present:
            out.append(f"{_label(path, root)}: " +
                       ", ".join(f"{t}={v}" for t, v in present))
    return out


def check_neb_layout(root):
    """Report NEB directory-layout facts: IMAGES value, the numbered image dirs
    present, which hold a POSCAR, and which endpoint dirs hold an OUTCAR. Raw
    facts only -- it does not assert the layout is correct or broken."""
    out = []
    # Find numbered image dirs (00,01,...) anywhere under root.
    image_dirs = {}   # parentpath -> {num: dirpath}
    for dirpath, dirnames, _files in os.walk(root):
        for d in dirnames:
            if re.fullmatch(r"\d\d", d):
                image_dirs.setdefault(dirpath, {})[int(d)] = os.path.join(dirpath, d)
    if not image_dirs:
        return out
    # The IMAGES tag from any INCAR under root (report each distinct value).
    images_vals = set()
    for dirpath, _dn, files in os.walk(root):
        if "INCAR" in files:
            tags = parse_incar(os.path.join(dirpath, "INCAR")) or {}
            if "IMAGES" in tags and tags["IMAGES"].split():
                images_vals.add(tags["IMAGES"].split()[0])
    for parent, dirs in sorted(image_dirs.items()):
        nums = sorted(dirs)
        rel = _label(parent, root) or "."
        present = ",".join(f"{n:02d}" for n in nums)
        no_poscar = [f"{n:02d}" for n in nums
                     if not os.path.exists(os.path.join(dirs[n], "POSCAR"))]
        endpoints = [nums[0], nums[-1]]
        no_outcar_ep = [f"{n:02d}" for n in endpoints
                        if not os.path.exists(os.path.join(dirs[n], "OUTCAR"))]
        out.append(f"[{rel}] IMAGES tag value(s)={sorted(images_vals) or 'none-found'}; "
                   f"image dirs present=[{present}] (count={len(nums)})")
        if no_poscar:
            out.append(f"[{rel}] image dirs missing a POSCAR: {no_poscar}")
        if no_outcar_ep:
            out.append(f"[{rel}] endpoint dir(s) missing an OUTCAR: {no_outcar_ep}")
    return out


_PERM_DIRECTIVE = (
    "DIRECTIVE for downstream agent: element-block order/counts are the ONLY "
    "thing verified here. Per-atom correspondence within a block is NOT verified "
    "-- nebmake interpolates atom-i->atom-i by line order, so a permutation of "
    "same-species atoms between endpoints silently breaks the path. Confirm each "
    "atom's initial->final displacement is physically small/sensible.")


def check_atom_order(endpoints):
    """Coarse endpoint atom-order check + a fixed directive. `endpoints` is a
    list of (label, poscar_dict). Compares element-block symbol sequence and
    per-block counts; emits the permutation directive unconditionally. Never
    blesses ordering."""
    if len(endpoints) < 2:
        return []
    out = []
    (la, pa), (lb, pb) = endpoints[0], endpoints[1]
    if pa["species"] is not None and pb["species"] is not None:
        if pa["species"] != pb["species"]:
            out.append(f"element-block symbol sequence differs: "
                       f"{la}={pa['species']} vs {lb}={pb['species']}")
        if pa["counts"] != pb["counts"]:
            out.append(f"per-species block counts differ: "
                       f"{la}={pa['counts']} vs {lb}={pb['counts']}")
    else:
        if pa["counts"] != pb["counts"]:
            out.append(f"per-block atom counts differ (VASP4 POSCAR, element "
                       f"identity unknown): {la}={pa['counts']} vs "
                       f"{lb}={pb['counts']}")
    if pa["natoms"] != pb["natoms"]:
        out.append(f"total atom count differs: {la}={pa['natoms']} vs "
                   f"{lb}={pb['natoms']}")
    out.append(_PERM_DIRECTIVE)
    return out


_SELDYN_DIRECTIVE = (
    "DIRECTIVE for downstream agent: only order-invariant frozen/free COUNTS per "
    "element block are compared here. Whether the SAME physical atoms are frozen "
    "across endpoints (and whether a frozen atom's coordinates moved) is NOT "
    "verified -- check that downstream.")


def _seldyn_block_tally(poscar):
    """Per-block (TTT-free / FFF-frozen / mixed) tallies, or None if selective
    dynamics is not declared or coordinates are unreadable."""
    if not poscar["selective"]:
        return None
    counts = poscar["counts"]
    lines = poscar["lines"]
    start = poscar["coord_start"]
    # Map atom index -> block index.
    block_of = []
    for b, c in enumerate(counts):
        block_of.extend([b] * c)
    tally = [{"free": 0, "frozen": 0, "mixed": 0} for _ in counts]
    for i in range(poscar["natoms"]):
        ln = start + i
        if ln >= len(lines):
            return None
        toks = lines[ln].split()
        flags = toks[3:6]
        if len(flags) < 3:
            return None
        norm = ["T" if f.upper().startswith("T") else
                ("F" if f.upper().startswith("F") else "?") for f in flags]
        if "?" in norm:
            return None
        kind = ("free" if norm == ["T", "T", "T"] else
                "frozen" if norm == ["F", "F", "F"] else "mixed")
        tally[block_of[i]][kind] += 1
    return tally


def check_selective_dynamics(endpoints):
    """Compare order-invariant frozen/free per-block tallies across the two
    endpoints + emit the directive. Never blesses."""
    if len(endpoints) < 2:
        return []
    (la, pa), (lb, pb) = endpoints[0], endpoints[1]
    ta, tb = _seldyn_block_tally(pa), _seldyn_block_tally(pb)
    out = []
    if (ta is None) != (tb is None):
        out.append(f"selective dynamics declared in one endpoint but not the "
                   f"other: {la} selective={pa['selective']}, "
                   f"{lb} selective={pb['selective']}")
    elif ta is not None and tb is not None:
        if len(ta) != len(tb):
            out.append(f"different number of species blocks ({la}={len(ta)} vs "
                       f"{lb}={len(tb)}); cannot align frozen tallies")
        elif ta != tb:
            out.append(f"frozen/free per-block tally differs: {la}={ta} vs "
                       f"{lb}={tb}")
    if pa["selective"] or pb["selective"]:
        out.append(_SELDYN_DIRECTIVE)
    return out


# --------------------------------------------------------------------------- #
# Interatomic distances  (PBC minimum-image, triclinic-safe)
# --------------------------------------------------------------------------- #

# Å. A pair closer than this is below the shortest real bond (H-H ~0.74 Å), so it
# is a near-certain atomic overlap regardless of element -- the only absolute,
# chemistry-agnostic call this check makes. Whether a LARGER distance is "too
# close" depends on the actual elements and is left to the agent.
_DIST_FLOOR = 0.7
# Atom-count cap for the exhaustive O(N^2) scan; above it we say "not scanned"
# (never-bless) rather than risk a slow precheck.
_MAXN = 800
# Max image-shell radius for the minimum-image search before declaring the cell
# too skewed for a bounded search (then the reported distance is an upper bound).
_IMG_KMAX = 4


def _structure_for_distance(poscar):
    """From a parsed POSCAR dict, return (frac_coords Nx3, species_per_atom or
    None, scaled_lattice 3x3) ready for the minimum-image search, or None if the
    coordinates are unreadable or the cell is degenerate. Cartesian POSCARs are
    converted to fractional; a negative scale (target volume) is resolved."""
    if poscar is None or np is None:
        return None
    lines, start, n = poscar["lines"], poscar["coord_start"], poscar["natoms"]
    if n < 2 or start + n > len(lines):
        return None
    L0 = np.asarray(poscar["lattice"], dtype=float)        # rows = lattice vectors
    det = float(np.linalg.det(L0))
    if abs(det) < 1e-8:
        return None
    scale = poscar["scale"]
    s = (abs(scale) / abs(det)) ** (1.0 / 3.0) if scale < 0 else scale
    if s <= 0:
        return None
    L = L0 * s
    coords = []
    for k in range(n):
        toks = lines[start + k].split()
        if len(toks) < 3:
            return None
        try:
            coords.append([float(toks[0]), float(toks[1]), float(toks[2])])
        except ValueError:
            return None
    C = np.asarray(coords, dtype=float)
    mode = (poscar["coord_mode"] or "").strip()[:1].lower()
    if mode in ("c", "k"):                                  # Cartesian
        frac = (C * s) @ np.linalg.inv(L)
    else:                                                   # Direct (fractional)
        frac = C
    spa = None
    if poscar["species"]:
        spa = []
        for sym, cnt in zip(poscar["species"], poscar["counts"]):
            spa.extend([sym] * cnt)
        if len(spa) != n:
            spa = None
    return frac, spa, L


def _min_image_nearest(frac, lattice):
    """Nearest-pair PBC minimum-image distance, triclinic-safe.

    frac: N x 3 fractional coords; lattice: 3 x 3 (rows = scaled vectors).
    Returns (dist_A, i, j, exact) or None if N<2. The search grows the image
    shell radius until the nearest distance stops decreasing -- so when
    `exact` is True the value is the true minimum, never an overestimate (an
    overestimate would be a false "no close contact" = forbidden). `exact` is
    False only if the cell is so skewed the bounded search (radius _IMG_KMAX)
    never converged, in which case the value is an UPPER bound.
    """
    if np is None:
        return None
    F = np.asarray(frac, dtype=float)
    n = F.shape[0]
    if n < 2:
        return None
    L = np.asarray(lattice, dtype=float)
    D = F[:, None, :] - F[None, :, :]          # N x N x 3 fractional differences
    D -= np.round(D)                           # wrap each to the home cell
    d2 = None
    m_prev = None
    exact = False
    for K in range(0, _IMG_KMAX + 1):
        for a in range(-K, K + 1):             # add only the new outer shell |.|=K
            for b in range(-K, K + 1):
                for c in range(-K, K + 1):
                    if max(abs(a), abs(b), abs(c)) != K:
                        continue
                    cart = (D + np.array([a, b, c], dtype=float)) @ L
                    s = np.einsum("ijk,ijk->ij", cart, cart)
                    d2 = s if d2 is None else np.minimum(d2, s)
        if K == 0:
            continue
        dd = d2.copy()
        np.fill_diagonal(dd, np.inf)
        m = float(np.sqrt(dd.min()))
        if m_prev is not None and m >= m_prev - 1e-9:   # outer shell didn't help
            exact = True
            break
        m_prev = m
    else:
        exact = False                          # never converged within _IMG_KMAX
    np.fill_diagonal(d2, np.inf)
    flat = int(np.argmin(d2))
    i, j = flat // n, flat % n
    return float(np.sqrt(d2[i, j])), min(i, j), max(i, j), exact


def _pair_str(i, j, spa):
    if spa:
        return f"{i + 1}({spa[i]})-{j + 1}({spa[j]})"
    return f"{i + 1}-{j + 1}"


def _mindist_rec(path):
    """('ok', dist, i, j, exact, spa) | ('few',) | ('big', natoms) | ('parse',)."""
    poscar = parse_poscar(path)
    if poscar is None:
        return ("parse",)
    if poscar["natoms"] < 2:
        return ("few",)
    if poscar["natoms"] > _MAXN:
        return ("big", poscar["natoms"])
    struct = _structure_for_distance(poscar)
    if struct is None:
        return ("parse",)
    frac, spa, L = struct
    mi = _min_image_nearest(frac, L)
    if mi is None:
        return ("parse",)
    dist, i, j, exact = mi
    return ("ok", dist, i, j, exact, spa)


def _mindist_val(rec):
    """Compact value token for a per-image vector entry."""
    if rec[0] == "ok":
        return f"{rec[1]:.2f}" + ("" if rec[4] else "*")
    return {"few": "n/a<2at", "big": "n/a-big"}.get(rec[0], "n/a-parse")


def check_min_distances(poscar_paths, root):
    """RAW FACT SURFACER: nearest-pair PBC minimum-image interatomic distance for
    every uploaded structure, and, across an NEB band, which image's nearest pair
    is smallest. Never blesses: it prints the raw distance for *every* readable
    structure (so an unflagged file is NOT 'cleared'), explicitly marks any file
    it could not scan, and only FLAGS the chemistry-agnostic certainty of a
    sub-0.7 Å overlap. It does NOT decide whether a larger distance is 'too close'
    for the real elements -- that is bond-dependent (the agent's call). Mirrors
    the detection step of the triage rows on sub-Å pairs / atoms passing through
    each other, feeding the 'atom correspondence?' judgment."""
    if np is None:
        return ["N/A: numpy unavailable -- interatomic-distance scan skipped"]
    bands = {}          # (band_parent_label, basename) -> [(imgnum, rec)]
    standalone = []     # (label, rec)
    for p in sorted(set(poscar_paths)):
        d = os.path.dirname(p)
        base = os.path.basename(p)
        rec = _mindist_rec(p)
        if base in ("POSCAR", "CONTCAR") and re.fullmatch(r"\d\d", os.path.basename(d)):
            bp = os.path.dirname(d)
            label = os.path.relpath(bp, root)
            bands.setdefault((label, base), []).append((int(os.path.basename(d)), rec))
        else:
            standalone.append((_label(p, root), rec))
    if not bands and not standalone:
        return []
    out = [(f"nearest-pair PBC min-image distance per structure (A); "
            f"FLAG = a pair < {_DIST_FLOOR} A apart (below any real bond = near-certain "
            f"overlap). A LARGER distance being 'too close' is bond-dependent -- agent "
            f"decides. '*' = cell too skewed for the bounded search (value is an UPPER "
            f"bound). 'n/a' = structure not scanned (reason shown).")]
    for label, base in sorted(bands):
        entries = sorted(bands[(label, base)])
        nums = [n for n, _ in entries]
        vec = " ".join(f"{n:02d}:{_mindist_val(rec)}" for n, rec in entries)
        line = f"  NEB band [{label}] {base} {nums[0]:02d}-{nums[-1]:02d}: {vec}"
        oks = [(n, rec) for n, rec in entries if rec[0] == "ok"]
        if len(oks) >= 2:
            dists = sorted(r[1] for _, r in oks)
            median = dists[len(dists) // 2]
            n_small, r_small = min(oks, key=lambda x: x[1][1])
            ratio = (r_small[1] / median) if median > 0 else 0.0
            line += (f"  -> smallest {n_small:02d}={r_small[1]:.2f}A "
                     f"(median {median:.2f}, ratio {ratio:.2f})")
        for n, r in oks:
            if r[1] < _DIST_FLOOR:
                line += (f"  FLAG {n:02d}={r[1]:.2f}A <{_DIST_FLOOR} pair "
                         f"{_pair_str(r[2], r[3], r[5])}")
        out.append(line)
    for label, rec in sorted(standalone, key=lambda x: x[0]):
        if rec[0] == "ok":
            s = f"  {label}: {rec[1]:.2f}A (atoms {_pair_str(rec[2], rec[3], rec[5])})"
            if not rec[4]:
                s += " [UPPER-BOUND: cell too skewed for bounded image search]"
            if rec[1] < _DIST_FLOOR:
                s += f"  FLAG <{_DIST_FLOOR}A (below any real bond)"
        elif rec[0] == "few":
            s = f"  {label}: not scanned (<2 atoms)"
        elif rec[0] == "big":
            s = f"  {label}: not scanned ({rec[1]} atoms > {_MAXN}-atom cap)"
        else:
            s = f"  {label}: not scanned (unreadable coordinates)"
        out.append(s)
    return out


# --------------------------------------------------------------------------- #
# File discovery + endpoint identification
# --------------------------------------------------------------------------- #

def _label(path, root):
    """Short, stable label for a file: its directory's path relative to root
    (so .../LiMox/00/OUTCAR -> '00', .../LiMox/POSCAR1 -> 'LiMox/POSCAR1')."""
    rel = os.path.relpath(path, root)
    parent = os.path.dirname(rel)
    base = os.path.basename(path)
    if base in ("OUTCAR", "INCAR"):
        return parent if parent not in ("", ".") else base
    return rel


def discover(root):
    found = {"OUTCAR": [], "INCAR": [], "POSCAR": [], "CONTCAR": [],
             "KPOINTS": [], "POTCAR": []}
    for dirpath, _dn, files in os.walk(root):
        for f in files:
            if f in found:
                found[f].append(os.path.join(dirpath, f))
            elif re.fullmatch(r"POSCAR\d+", f):
                found["POSCAR"].append(os.path.join(dirpath, f))
    return found


def identify_endpoints(root, found):
    """Return up to two (label, poscar_dict) endpoint candidates, or [].

    Only the unambiguous layouts are supported (else N/A, never a guess):
      (a) numbered NEB dirs: lowest 'NN/POSCAR' and highest 'NN/POSCAR';
      (b) a single dir containing exactly POSCAR1 and POSCAR2.
    """
    # (a) numbered dirs sharing a parent.
    by_parent = {}
    for p in found["POSCAR"]:
        d = os.path.dirname(p)
        name = os.path.basename(d)
        if re.fullmatch(r"\d\d", name) and os.path.basename(p) == "POSCAR":
            by_parent.setdefault(os.path.dirname(d), {})[int(name)] = p
    for parent, m in sorted(by_parent.items()):
        if len(m) >= 2:
            lo, hi = min(m), max(m)
            pa, pb = parse_poscar(m[lo]), parse_poscar(m[hi])
            if pa and pb:
                return [(_label(m[lo], root), pa), (_label(m[hi], root), pb)]
    # (b) POSCAR1/POSCAR2 pair in one dir.
    pair = {}
    for p in found["POSCAR"]:
        b = os.path.basename(p)
        if b in ("POSCAR1", "POSCAR2"):
            pair.setdefault(os.path.dirname(p), {})[b] = p
    for d, m in sorted(pair.items()):
        if "POSCAR1" in m and "POSCAR2" in m:
            pa, pb = parse_poscar(m["POSCAR1"]), parse_poscar(m["POSCAR2"])
            if pa and pb:
                return [(_label(m["POSCAR1"], root), pa),
                        (_label(m["POSCAR2"], root), pb)]
    return []


# --------------------------------------------------------------------------- #
# Runner
# --------------------------------------------------------------------------- #

def run(root):
    """Run all trivial prechecks under `root`; return a raw report string.
    The report lists, per check: detected findings, or an explicit N/A reason --
    never an 'all clear'."""
    found = discover(root)
    blocks = []

    def emit(name, findings, na=None):
        if findings:
            blocks.append(f"== {name} ==\n" + "\n".join(findings))
        elif na:
            blocks.append(f"== {name} ==\nN/A: {na}")
        else:
            blocks.append(f"== {name} ==\n(no anomalies detected by this check)")

    # Settings consistency.
    cons, status = check_settings_consistency(found["OUTCAR"], found["INCAR"], root)
    body = [f"(status: {status})"]
    if cons:
        body += cons
    elif not status.startswith("N/A"):
        body.append("(no differing tags among the compared set)")
    if not status.startswith("N/A"):
        body.append(_XC_DIRECTIVE)
    blocks.append("== settings_consistency_endpoints_vs_band ==\n" + "\n".join(body))

    # VTST linkage (raw-fact surfacer; absence made explicit).
    emit("vtst_linkage (raw fact)",
         check_vtst_linkage(found["OUTCAR"], found["INCAR"], root),
         na="no OUTCAR uploaded" if not found["OUTCAR"] else "no readable OUTCAR")

    # Binary / VASP version (raw-fact surfacer; cross-OUTCAR version diff flagged).
    emit("binary_version (raw fact)",
         check_binary_version(found["OUTCAR"], root),
         na="no OUTCAR uploaded" if not found["OUTCAR"] else "no readable OUTCAR")

    # Ionic convergence per OUTCAR (raw-fact surfacer; absence made explicit).
    emit("ionic_convergence (raw fact)",
         check_convergence(found["OUTCAR"], root),
         na="no OUTCAR uploaded" if not found["OUTCAR"] else "no readable OUTCAR")

    # SCF non-convergence (raw-fact surfacer).
    emit("scf_convergence (raw fact)",
         check_scf_convergence(found["OUTCAR"], root),
         na="no OUTCAR uploaded" if not found["OUTCAR"] else None)

    # INCAR hygiene + EDIFFG sign (per INCAR).
    hyg, edi = [], []
    for inc in sorted(found["INCAR"]):
        hyg += check_incar_hygiene(inc)
        edi += check_ediffg_sign(inc)
    emit("incar_format_hygiene", hyg,
         na=None if found["INCAR"] else "no INCAR uploaded")
    blocks.append("== ediffg_sign (raw fact) ==\n" +
                  ("\n".join(edi) if edi else "N/A: no INCAR uploaded"))

    # Notable INCAR gotcha flags (raw-fact surfacer).
    emit("notable_incar_flags (raw fact)",
         check_notable_incar_flags(found["INCAR"], root),
         na=None if found["INCAR"] else "no INCAR uploaded")

    # List-length (pair each INCAR with a POSCAR in its dir, else a sibling).
    ll = []
    for inc in sorted(found["INCAR"]):
        pos = _nearest_poscar(inc, found)
        if pos:
            ll += check_list_lengths(inc, parse_poscar(pos))
    emit("incar_list_lengths", ll,
         na=None if found["INCAR"] else "no INCAR uploaded")

    # POSCAR format (all POSCAR/CONTCAR).
    pf = []
    for p in sorted(found["POSCAR"] + found["CONTCAR"]):
        pf += check_poscar_format(parse_poscar(p))
    emit("poscar_format", pf,
         na=None if (found["POSCAR"] or found["CONTCAR"]) else "no POSCAR uploaded")

    # Interatomic minimum distances (raw-fact surfacer; PBC minimum-image).
    emit("interatomic_min_distance (raw fact)",
         check_min_distances(found["POSCAR"] + found["CONTCAR"], root),
         na="no POSCAR/CONTCAR uploaded"
            if not (found["POSCAR"] or found["CONTCAR"]) else None)

    # NEB layout.
    emit("neb_dir_layout", check_neb_layout(root),
         na="no numbered image dirs (00,01,...) found")

    # Analysis-file readability (compressed/missing image OUTCARs).
    emit("analysis_file_readability", check_analysis_files(root))

    # Atom order + selective dynamics (need identified endpoints).
    eps = identify_endpoints(root, found)
    if eps:
        emit("atom_order_endpoints", check_atom_order(eps))
        emit("selective_dynamics_endpoints", check_selective_dynamics(eps))
    else:
        emit("atom_order_endpoints", [],
             na="could not unambiguously identify two endpoint POSCARs")
        emit("selective_dynamics_endpoints", [],
             na="could not unambiguously identify two endpoint POSCARs")

    header = (f"TRIVIAL PRECHECKS  root={root}\n"
              f"discovered: " +
              ", ".join(f"{k}={len(v)}" for k, v in found.items()) +
              "\n(Findings are raw facts for the agent. A check reporting "
              "nothing or N/A is NOT a guarantee that dimension is fine.)")
    return header + "\n\n" + "\n\n".join(blocks) + "\n"


def _nearest_poscar(incar_path, found):
    """A POSCAR/CONTCAR in the same dir as the INCAR, else in a 00/ child, else
    any sibling image dir -- for cardinality (NIONS) of the run."""
    d = os.path.dirname(incar_path)
    for cand in ("POSCAR", "CONTCAR"):
        p = os.path.join(d, cand)
        if os.path.exists(p):
            return p
    for p in sorted(found["POSCAR"] + found["CONTCAR"]):
        if os.path.dirname(os.path.dirname(p)) == d:  # d/NN/POSCAR
            return p
    return None


def main(argv):
    if len(argv) != 2:
        print("usage: precheck.py <root_dir>", file=sys.stderr)
        return 2
    print(run(argv[1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
