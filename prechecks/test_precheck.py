"""Rigorous tests for the trivial prechecks.

Focus areas: the never-bless contract, the resolved-vs-raw OUTCAR merge (default
divergence + ALGO/IALGO aliasing + raw-only tags like IVDW), n*val expansion,
AFM split species blocks, VASP4 POSCARs, noncollinear MAGMOM, and the POSCAR
anomaly detectors.
"""

import os
import textwrap

import precheck as P


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def _w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(textwrap.dedent(text))
    return path


POSCAR_BASIC = """\
    LiMoS comment
 1.0
   5.0 0.0 0.0
   0.0 5.0 0.0
   0.0 0.0 5.0
 Li O
 2 1
 Direct
 0.0 0.0 0.0
 0.5 0.5 0.5
 0.25 0.25 0.25
"""


def _outcar(incar_block, resolved_block):
    return (" vasp.6.2.0 18Jan21 gamma-only\n\n INCAR:\n" + incar_block +
            "\n POTCAR:    PAW_PBE Mo 08Apr2002\n"
            " Startparameter for this run:\n" + resolved_block +
            "\n--------------- Iteration   1(   1)\n more per-step text\n")


# --------------------------------------------------------------------------- #
# count_values (n*val expansion)
# --------------------------------------------------------------------------- #

def test_count_values_plain():
    assert P.count_values("0.0 0.0 0.0") == 3

def test_count_values_repeat_compact():
    assert P.count_values("3*0.0") == 3

def test_count_values_repeat_spaces():
    assert P.count_values("3 * 0.0") == 3
    assert P.count_values("3* 0.0") == 3
    assert P.count_values("3 *0.0") == 3

def test_count_values_mixed():
    assert P.count_values("3*5 2*0 1.0") == 6
    assert P.count_values("48*0.0") == 48

def test_count_values_empty():
    assert P.count_values("") == 0

def test_count_values_malformed_returns_none():
    assert P.count_values("x*1") is None
    assert P.count_values("3*") is None


# --------------------------------------------------------------------------- #
# parse_incar
# --------------------------------------------------------------------------- #

def test_parse_incar_comments_and_semicolons(tmp_path):
    inc = _w(str(tmp_path / "INCAR"), """\
        ISPIN = 2  # spin
        IBRION = 3 ; POTIM = 0  ! inline
        ISPIN = 1
    """)
    tags = P.parse_incar(inc)
    assert tags["ISPIN"] == "1"        # last wins
    assert tags["IBRION"] == "3"
    assert tags["POTIM"] == "0"

def test_parse_incar_magmom_list(tmp_path):
    inc = _w(str(tmp_path / "INCAR"), "MAGMOM = 3*0.0 2*5.0\n")
    assert P.parse_incar(inc)["MAGMOM"] == "3*0.0 2*5.0"


# --------------------------------------------------------------------------- #
# parse_poscar  (block-aware, VASP4, selective dynamics)
# --------------------------------------------------------------------------- #

def test_parse_poscar_vasp5(tmp_path):
    p = P.parse_poscar(_w(str(tmp_path / "POSCAR"), POSCAR_BASIC))
    assert p["species"] == ["Li", "O"]
    assert p["counts"] == [2, 1]
    assert p["natoms"] == 3
    assert p["selective"] is False
    assert p["coord_mode"].startswith("Direct")

def test_parse_poscar_afm_split_blocks(tmp_path):
    # Same element (Fe) split into two blocks -> must stay two blocks.
    txt = POSCAR_BASIC.replace(" Li O\n 2 1\n", " Fe Fe O\n 2 2 1\n").replace(
        " 0.25 0.25 0.25\n", " 0.25 0.25 0.25\n 0.6 0.6 0.6\n 0.7 0.7 0.7\n")
    p = P.parse_poscar(_w(str(tmp_path / "POSCAR"), txt))
    assert p["species"] == ["Fe", "Fe", "O"]
    assert p["counts"] == [2, 2, 1]
    assert len(p["counts"]) == 3      # block-aware, NOT collapsed to {Fe,O}
    assert p["natoms"] == 5

def test_parse_poscar_vasp4_no_symbol_line(tmp_path):
    txt = POSCAR_BASIC.replace(" Li O\n 2 1\n", " 2 1\n")
    p = P.parse_poscar(_w(str(tmp_path / "POSCAR"), txt))
    assert p["species"] is None
    assert p["counts"] == [2, 1]
    assert p["natoms"] == 3

def test_parse_poscar_selective(tmp_path):
    txt = POSCAR_BASIC.replace(
        " Direct\n", " Selective dynamics\n Direct\n").replace(
        " 0.0 0.0 0.0\n", " 0.0 0.0 0.0 F F F\n").replace(
        " 0.5 0.5 0.5\n", " 0.5 0.5 0.5 T T T\n").replace(
        " 0.25 0.25 0.25\n", " 0.25 0.25 0.25 T T T\n")
    p = P.parse_poscar(_w(str(tmp_path / "POSCAR"), txt))
    assert p["selective"] is True
    assert p["coord_mode"].startswith("Direct")


# --------------------------------------------------------------------------- #
# parse_outcar_params  (THE critical one: resolved vs raw merge)
# --------------------------------------------------------------------------- #

def test_outcar_resolved_beats_raw_and_skips_incar_dump(tmp_path):
    # raw INCAR says ISPIN=2 but the resolved block (authoritative) says 1.
    oc = _outcar(
        "   ISPIN = 2\n   IVDW = 11\n",
        "   ISPIN  =      1    spin polarized calculation?\n"
        "   IALGO  =     38    algorithm\n")
    oc_path = _w(str(tmp_path / "OUTCAR"), oc)
    got = P.parse_outcar_params(oc_path, {"ISPIN", "IVDW", "IALGO"})
    assert got["ISPIN"] == ("1", "resolved")   # resolved wins over raw dump
    assert got["IVDW"] == ("11", "raw")         # raw-only tag still caught
    assert got["IALGO"] == ("38", "resolved")

def test_outcar_stops_before_iteration(tmp_path):
    # A tag re-printed in per-step output must NOT override the resolved value.
    oc = (" vasp\n Startparameter for this run:\n"
          "   ISPIN  =      1   x\n"
          "--------------- Iteration 1\n"
          "   ISPIN  =      9   bogus per-step\n")
    got = P.parse_outcar_params(_w(str(tmp_path / "OUTCAR"), oc), {"ISPIN"})
    assert got["ISPIN"] == ("1", "resolved")


# --------------------------------------------------------------------------- #
# settings consistency
# --------------------------------------------------------------------------- #

def _consistency_tree(tmp_path):
    """A 2-image NEB whose endpoints (00,02) used a different deck than the band
    (01): ISPIN 1 vs 2, ISYM 2 vs 0 (00 omits ISYM -> default), IALGO 38 vs 48
    (alias), PREC normal vs accura, IVDW 11 (endpoints, raw-only) vs none."""
    ep_incar = "   ISPIN = 1\n   IVDW = 11\n   IALGO = 38\n"
    ep_res = ("   ISPIN  =      1   x\n   ICHARG =      1   x\n"
              "   PREC   = normal   x\n   ISYM   =      2   x\n"
              "   IALGO  =     38   x\n")
    band_incar = "   ISPIN = 2\n   ISYM = 0\n   ALGO = VeryFast\n   PREC = Accurate\n"
    band_res = ("   ISPIN  =      2   x\n   ICHARG =      2   x\n"
                "   PREC   = accura   x\n   ISYM   =      0   x\n"
                "   IALGO  =     48   x\n")
    _w(str(tmp_path / "00" / "OUTCAR"), _outcar(ep_incar, ep_res))
    _w(str(tmp_path / "01" / "OUTCAR"), _outcar(band_incar, band_res))
    _w(str(tmp_path / "02" / "OUTCAR"), _outcar(ep_incar, ep_res))
    return P.discover(str(tmp_path))

def test_consistency_flags_real_diffs(tmp_path):
    found = _consistency_tree(tmp_path)
    findings, status = P.check_settings_consistency(
        found["OUTCAR"], found["INCAR"], str(tmp_path))
    flagged = {f.split(":")[0] for f in findings}
    for tag in ("ISPIN", "ICHARG", "PREC", "ISYM", "IALGO", "IVDW"):
        assert tag in flagged, f"{tag} should be flagged; got {findings}"
    assert "OUTCAR resolved block" in status

def test_gga_not_diffed_but_directive_emitted(tmp_path):
    # GGA differs (-- vs PE) but must NOT be flagged; the XC directive must show.
    _w(str(tmp_path / "00" / "OUTCAR"),
       _outcar("   ISPIN = 1\n",
               "   ISPIN  =  1  x\n   GGA     =    --    GGA type\n"))
    _w(str(tmp_path / "01" / "OUTCAR"),
       _outcar("   ISPIN = 1\n",
               "   ISPIN  =  1  x\n   GGA = PE\n"))
    assert "GGA" not in P.CONSISTENCY_TAGS
    report = P.run(str(tmp_path))
    cons_block = report.split("== settings_consistency")[1].split("==")[0]
    assert "GGA:" not in cons_block          # not mechanically diffed
    assert "XC functional" in report          # directive handed to the agent

def test_consistency_does_not_flag_identical(tmp_path):
    res = ("   ISPIN  =      2   x\n   ISYM   =      0   x\n"
           "   IALGO  =     48   x\n   PREC   = accura   x\n")
    inc = "   ISPIN = 2\n"
    _w(str(tmp_path / "00" / "OUTCAR"), _outcar(inc, res))
    _w(str(tmp_path / "01" / "OUTCAR"), _outcar(inc, res))
    found = P.discover(str(tmp_path))
    findings, _ = P.check_settings_consistency(
        found["OUTCAR"], found["INCAR"], str(tmp_path))
    assert findings == []

def test_consistency_incar_fallback_has_caveat(tmp_path):
    # No OUTCARs -> falls back to raw INCAR diff WITH the unresolved-defaults caveat.
    _w(str(tmp_path / "ep" / "INCAR"), "ISPIN = 1\n")
    _w(str(tmp_path / "band" / "INCAR"), "ISPIN = 2\n")
    found = P.discover(str(tmp_path))
    findings, status = P.check_settings_consistency(
        found["OUTCAR"], found["INCAR"], str(tmp_path))
    assert any(f.startswith("ISPIN:") for f in findings)
    assert "CAVEAT" in status and "raw INCAR text" in status

def test_consistency_na_when_single_run(tmp_path):
    _w(str(tmp_path / "00" / "OUTCAR"),
       _outcar("   ISPIN = 1\n", "   ISPIN  =  1  x\n"))
    found = P.discover(str(tmp_path))
    findings, status = P.check_settings_consistency(
        found["OUTCAR"], found["INCAR"], str(tmp_path))
    assert findings == []
    assert status.startswith("N/A")


# --------------------------------------------------------------------------- #
# vtst linkage (raw-fact surfacer; absence made explicit)
# --------------------------------------------------------------------------- #

def test_vtst_absent_made_explicit(tmp_path):
    # No VTST banner in either OUTCAR -> must say "ABSENT ... (ALL 2)", never blank.
    _w(str(tmp_path / "00" / "OUTCAR"), " vasp.6.2.0\n Startparameter\n")
    _w(str(tmp_path / "01" / "OUTCAR"), " vasp.6.2.0\n Startparameter\n")
    _w(str(tmp_path / "INCAR"), "IMAGES = 4\nIOPT = 3\nSPRING = -5\n")
    out = P.check_vtst_linkage(
        P.discover(str(tmp_path))["OUTCAR"],
        P.discover(str(tmp_path))["INCAR"], str(tmp_path))
    text = "\n".join(out)
    assert "FOUND  in: (none)" in text
    assert "ABSENT in: 00,01" in text and "(ALL 2)" in text
    assert "IMAGES=4" in text and "IOPT=3" in text   # juxtaposed VTST request

def test_vtst_found(tmp_path):
    _w(str(tmp_path / "00" / "OUTCAR"),
       " vasp.6.2.0\n VTST: version 3.2 (03/28/14)\n")
    out = P.check_vtst_linkage(
        P.discover(str(tmp_path))["OUTCAR"], [], str(tmp_path))
    assert any("FOUND  in: 00" in o for o in out)

def test_vtst_mixed(tmp_path):
    # Endpoints linked, band not -> both sets reported, no (ALL n) suffix.
    _w(str(tmp_path / "00" / "OUTCAR"), " VTST: version 3.2\n")
    _w(str(tmp_path / "01" / "OUTCAR"), " no banner here\n")
    out = "\n".join(P.check_vtst_linkage(
        P.discover(str(tmp_path))["OUTCAR"], [], str(tmp_path)))
    assert "FOUND  in: 00" in out
    assert "ABSENT in: 01" in out
    assert "(ALL" not in out

def test_vtst_no_outcar_returns_empty(tmp_path):
    assert P.check_vtst_linkage([], [], str(tmp_path)) == []

def test_vtst_absent_but_no_vtst_tags_disambiguated(tmp_path):
    # Plain relaxation: banner absent AND no VTST tags -> the tags line must say
    # "(none of ...)" so the agent doesn't anchor on a non-issue.
    _w(str(tmp_path / "OUTCAR"), " vasp.6.2.0\n no banner\n")
    _w(str(tmp_path / "INCAR"), "IBRION = 2\nNSW = 100\nENCUT = 400\n")
    out = "\n".join(P.check_vtst_linkage(
        P.discover(str(tmp_path))["OUTCAR"],
        P.discover(str(tmp_path))["INCAR"], str(tmp_path)))
    assert "ABSENT in:" in out
    assert "none of IMAGES/SPRING" in out      # disambiguation present


# --------------------------------------------------------------------------- #
# binary / version, convergence, scf, analysis files, notable flags
# --------------------------------------------------------------------------- #

def test_binary_version_diff_flagged(tmp_path):
    _w(str(tmp_path / "00" / "OUTCAR"),
       " vasp.5.4.4 18Apr17 (build) complex\n VTST: version 3.2\n")
    _w(str(tmp_path / "01" / "OUTCAR"),
       " vasp.6.4.1 20Jul23 (build) gamma-only\n")
    out = "\n".join(P.check_binary_version(
        P.discover(str(tmp_path))["OUTCAR"], str(tmp_path)))
    assert "vasp.5.4.4" in out and "vasp.6.4.1" in out
    assert "gamma-only" in out and "complex" in out
    assert "DIFFER" in out                       # cross-OUTCAR version mismatch

def test_binary_version_serial(tmp_path):
    _w(str(tmp_path / "OUTCAR"),
       " vasp.5.4.4 serial version\n more\n running on 1 cores\n")
    out = "\n".join(P.check_binary_version(
        P.discover(str(tmp_path))["OUTCAR"], str(tmp_path)))
    assert "serial" in out

def test_binary_version_same_no_diff(tmp_path):
    for d in ("00", "01"):
        _w(str(tmp_path / d / "OUTCAR"), " vasp.6.2.0 18Jan21 (build) gamma-only\n")
    out = "\n".join(P.check_binary_version(
        P.discover(str(tmp_path))["OUTCAR"], str(tmp_path)))
    assert "DIFFER" not in out

def test_convergence_absence_explicit(tmp_path):
    _w(str(tmp_path / "00" / "OUTCAR"),
       " x\n reached required accuracy - stopping\n")
    _w(str(tmp_path / "01" / "OUTCAR"), " x\n (no convergence line)\n")
    out = "\n".join(P.check_convergence(
        P.discover(str(tmp_path))["OUTCAR"], str(tmp_path)))
    assert "PRESENT in: 00" in out
    assert "ABSENT  in: 01" in out

def test_scf_nonconvergence_flagged(tmp_path):
    _w(str(tmp_path / "00" / "OUTCAR"),
       " aborting loop EDIFF was not reached (unconverged)\n")
    _w(str(tmp_path / "01" / "OUTCAR"),
       " aborting loop because EDIFF is reached\n")
    out = P.check_scf_convergence(P.discover(str(tmp_path))["OUTCAR"], str(tmp_path))
    text = "\n".join(out)
    assert "00" in text and "01" not in text     # only the failed one

def test_scf_clean_returns_empty(tmp_path):
    _w(str(tmp_path / "00" / "OUTCAR"), " aborting loop because EDIFF is reached\n")
    assert P.check_scf_convergence(
        P.discover(str(tmp_path))["OUTCAR"], str(tmp_path)) == []

def test_analysis_compressed_outcar_flagged(tmp_path):
    import gzip
    _w(str(tmp_path / "00" / "POSCAR"), POSCAR_BASIC)   # ensure dir exists
    with gzip.open(str(tmp_path / "00" / "OUTCAR"), "wb") as fh:
        fh.write(b"compressed outcar content")
    out = P.check_analysis_files(str(tmp_path))
    assert any("compressor magic bytes" in o for o in out)

def test_analysis_plain_outcar_clean(tmp_path):
    _w(str(tmp_path / "00" / "OUTCAR"), " vasp.6.2.0 plain text\n")
    assert P.check_analysis_files(str(tmp_path)) == []

def test_notable_flags_surfaced(tmp_path):
    _w(str(tmp_path / "INCAR"), "LDIPOL = .TRUE.\nIDIPOL = 3\nPSTRESS = 50\n")
    out = "\n".join(P.check_notable_incar_flags(
        P.discover(str(tmp_path))["INCAR"], str(tmp_path)))
    assert "LDIPOL=.TRUE." in out and "PSTRESS=50" in out

def test_notable_flags_none(tmp_path):
    _w(str(tmp_path / "INCAR"), "ISPIN = 2\nENCUT = 400\n")
    assert P.check_notable_incar_flags(
        P.discover(str(tmp_path))["INCAR"], str(tmp_path)) == []


# --------------------------------------------------------------------------- #
# incar hygiene
# --------------------------------------------------------------------------- #

def test_hygiene_tab(tmp_path):
    inc = str(tmp_path / "INCAR")
    with open(inc, "w") as fh:
        fh.write("IOPT = 1\t\nIBRION = 3\n")          # trailing tab
    out = P.check_incar_hygiene(inc)
    assert any("tab" in o for o in out)

def test_hygiene_tab_in_comment_not_flagged(tmp_path):
    # A tab inside a comment is harmless (VASP ignores post-# text) -> no flag.
    inc = str(tmp_path / "INCAR")
    with open(inc, "w") as fh:
        fh.write("ICHARG = 2     # Default: ICHARG\t= 2\n")
    assert P.check_incar_hygiene(inc) == []

def test_hygiene_float_in_int_tag(tmp_path):
    inc = _w(str(tmp_path / "INCAR"), "IOPT = 0.2\n")
    out = P.check_incar_hygiene(inc)
    assert any("IOPT" in o and "non-integer" in o for o in out)

def test_hygiene_integer_float_not_flagged(tmp_path):
    # 1.0 is integer-valued -> must NOT be flagged (no false positive panic,
    # but more importantly IBRION=-1 etc. must be clean).
    inc = _w(str(tmp_path / "INCAR"), "IBRION = -1\nISMEAR = 0\nIOPT = 3\n")
    assert P.check_incar_hygiene(inc) == []

def test_hygiene_clean(tmp_path):
    inc = _w(str(tmp_path / "INCAR"), "ISPIN = 2\nENCUT = 400\nEDIFF = 1E-6\n")
    assert P.check_incar_hygiene(inc) == []


# --------------------------------------------------------------------------- #
# ediffg sign  (raw fact, no verdict)
# --------------------------------------------------------------------------- #

def test_ediffg_negative(tmp_path):
    inc = _w(str(tmp_path / "INCAR"), "EDIFFG = -0.02\n")
    out = P.check_ediffg_sign(inc)
    assert "negative/force-based" in out[0]

def test_ediffg_positive(tmp_path):
    inc = _w(str(tmp_path / "INCAR"), "EDIFFG = 1E-5\n")
    assert "positive/energy-based" in P.check_ediffg_sign(inc)[0]

def test_ediffg_unset(tmp_path):
    inc = _w(str(tmp_path / "INCAR"), "ISPIN = 2\n")
    assert "not set" in P.check_ediffg_sign(inc)[0]


# --------------------------------------------------------------------------- #
# list lengths
# --------------------------------------------------------------------------- #

def test_list_length_per_species_afm_split(tmp_path):
    # Fe Fe O = 3 blocks; LDAUU with only 2 values -> flag (the AFM-split trap).
    txt = POSCAR_BASIC.replace(" Li O\n 2 1\n", " Fe Fe O\n 2 2 1\n").replace(
        " 0.25 0.25 0.25\n", " 0.25 0.25 0.25\n 0.6 0.6 0.6\n 0.7 0.7 0.7\n")
    pos = P.parse_poscar(_w(str(tmp_path / "POSCAR"), txt))
    inc = _w(str(tmp_path / "INCAR"), "LDAUU = 5.0 0.0\n")   # 2, need 3
    out = P.check_list_lengths(inc, pos)
    assert any("LDAUU" in o and "3 species block" in o for o in out)

def test_list_length_per_species_ok_not_flagged(tmp_path):
    txt = POSCAR_BASIC.replace(" Li O\n 2 1\n", " Fe Fe O\n 2 2 1\n").replace(
        " 0.25 0.25 0.25\n", " 0.25 0.25 0.25\n 0.6 0.6 0.6\n 0.7 0.7 0.7\n")
    pos = P.parse_poscar(_w(str(tmp_path / "POSCAR"), txt))
    inc = _w(str(tmp_path / "INCAR"), "LDAUU = 5.0 5.0 0.0\n")   # 3 == 3 blocks
    assert P.check_list_lengths(inc, pos) == []

def test_list_length_magmom_per_atom(tmp_path):
    pos = P.parse_poscar(_w(str(tmp_path / "POSCAR"), POSCAR_BASIC))  # 3 atoms
    inc = _w(str(tmp_path / "INCAR"), "MAGMOM = 2*1.0\n")            # 2, need 3
    out = P.check_list_lengths(inc, pos)
    assert any("MAGMOM" in o for o in out)

def test_list_length_magmom_repeat_ok(tmp_path):
    pos = P.parse_poscar(_w(str(tmp_path / "POSCAR"), POSCAR_BASIC))  # 3 atoms
    inc = _w(str(tmp_path / "INCAR"), "MAGMOM = 3*0.6\n")            # 3 == NIONS
    assert P.check_list_lengths(inc, pos) == []

def test_list_length_magmom_noncollinear(tmp_path):
    pos = P.parse_poscar(_w(str(tmp_path / "POSCAR"), POSCAR_BASIC))  # 3 atoms
    inc_ok = _w(str(tmp_path / "INCAR"),
                "LNONCOLLINEAR = .TRUE.\nMAGMOM = 9*0.0\n")          # 9 == 3*3
    assert P.check_list_lengths(inc_ok, pos) == []
    inc_bad = _w(str(tmp_path / "INCAR2"),
                 "LNONCOLLINEAR = .TRUE.\nMAGMOM = 3*0.0\n")         # 3 != 9
    assert any("MAGMOM" in o for o in P.check_list_lengths(inc_bad, pos))


# --------------------------------------------------------------------------- #
# poscar format anomalies
# --------------------------------------------------------------------------- #

def test_poscar_format_clean(tmp_path):
    assert P.check_poscar_format(
        P.parse_poscar(_w(str(tmp_path / "POSCAR"), POSCAR_BASIC))) == []

def test_poscar_format_element_label_on_coords(tmp_path):
    txt = POSCAR_BASIC.replace(" 0.0 0.0 0.0\n", " Li 0.0 0.0 0.0\n")
    out = P.check_poscar_format(P.parse_poscar(_w(str(tmp_path / "POSCAR"), txt)))
    assert any("non-numeric" in o for o in out)

def test_poscar_format_nan(tmp_path):
    txt = POSCAR_BASIC.replace(" 0.5 0.5 0.5\n", " NaN NaN NaN\n")
    out = P.check_poscar_format(P.parse_poscar(_w(str(tmp_path / "POSCAR"), txt)))
    assert any("NaN" in o for o in out)

def test_poscar_format_missing_coord_keyword(tmp_path):
    txt = POSCAR_BASIC.replace(" Direct\n", " \n")
    out = P.check_poscar_format(P.parse_poscar(_w(str(tmp_path / "POSCAR"), txt)))
    assert any("coordinate-mode" in o for o in out)

def test_poscar_format_species_count_mismatch(tmp_path):
    txt = POSCAR_BASIC.replace(" Li O\n 2 1\n", " Li O F\n 2 1\n")
    out = P.check_poscar_format(P.parse_poscar(_w(str(tmp_path / "POSCAR"), txt)))
    assert any("species-symbol count" in o for o in out)


# --------------------------------------------------------------------------- #
# atom order + selective dynamics (endpoint hybrids)
# --------------------------------------------------------------------------- #

def test_atom_order_mismatch_and_directive(tmp_path):
    a = P.parse_poscar(_w(str(tmp_path / "00" / "POSCAR"), POSCAR_BASIC))
    b_txt = POSCAR_BASIC.replace(" Li O\n 2 1\n", " O Li\n 1 2\n")
    b = P.parse_poscar(_w(str(tmp_path / "02" / "POSCAR"), b_txt))
    out = P.check_atom_order([("00", a), ("02", b)])
    assert any("element-block symbol sequence differs" in o for o in out)
    assert any("DIRECTIVE" in o for o in out)             # always emits directive

def test_atom_order_match_still_emits_directive(tmp_path):
    a = P.parse_poscar(_w(str(tmp_path / "00" / "POSCAR"), POSCAR_BASIC))
    b = P.parse_poscar(_w(str(tmp_path / "02" / "POSCAR"), POSCAR_BASIC))
    out = P.check_atom_order([("00", a), ("02", b)])
    # never blesses: even on a match, the ONLY output is the directive.
    assert len(out) == 1 and "DIRECTIVE" in out[0]

def test_seldyn_tally_order_invariant(tmp_path):
    # Same per-block frozen counts but permuted order -> tally must MATCH
    # (order-invariant) so it is not spuriously flagged.
    base = POSCAR_BASIC.replace(
        " Direct\n", " Selective dynamics\n Direct\n").replace(
        " 0.0 0.0 0.0\n", " 0.0 0.0 0.0 F F F\n").replace(
        " 0.5 0.5 0.5\n", " 0.5 0.5 0.5 T T T\n").replace(
        " 0.25 0.25 0.25\n", " 0.25 0.25 0.25 T T T\n")
    perm = POSCAR_BASIC.replace(
        " Direct\n", " Selective dynamics\n Direct\n").replace(
        " 0.0 0.0 0.0\n", " 0.0 0.0 0.0 T T T\n").replace(   # Li atoms swapped
        " 0.5 0.5 0.5\n", " 0.5 0.5 0.5 F F F\n").replace(
        " 0.25 0.25 0.25\n", " 0.25 0.25 0.25 T T T\n")
    a = P.parse_poscar(_w(str(tmp_path / "00" / "POSCAR"), base))
    b = P.parse_poscar(_w(str(tmp_path / "02" / "POSCAR"), perm))
    out = P.check_selective_dynamics([("00", a), ("02", b)])
    assert not any("tally differs" in o for o in out)   # 1 frozen Li in both
    assert any("DIRECTIVE" in o for o in out)

def test_seldyn_tally_real_difference_flagged(tmp_path):
    base = POSCAR_BASIC.replace(
        " Direct\n", " Selective dynamics\n Direct\n").replace(
        " 0.0 0.0 0.0\n", " 0.0 0.0 0.0 F F F\n").replace(
        " 0.5 0.5 0.5\n", " 0.5 0.5 0.5 T T T\n").replace(
        " 0.25 0.25 0.25\n", " 0.25 0.25 0.25 T T T\n")
    diff = POSCAR_BASIC.replace(
        " Direct\n", " Selective dynamics\n Direct\n").replace(
        " 0.0 0.0 0.0\n", " 0.0 0.0 0.0 T T T\n").replace(   # 0 frozen Li now
        " 0.5 0.5 0.5\n", " 0.5 0.5 0.5 T T T\n").replace(
        " 0.25 0.25 0.25\n", " 0.25 0.25 0.25 T T T\n")
    a = P.parse_poscar(_w(str(tmp_path / "00" / "POSCAR"), base))
    b = P.parse_poscar(_w(str(tmp_path / "02" / "POSCAR"), diff))
    out = P.check_selective_dynamics([("00", a), ("02", b)])
    assert any("tally differs" in o for o in out)


# --------------------------------------------------------------------------- #
# neb layout + endpoint identification + end-to-end runner
# --------------------------------------------------------------------------- #

def test_neb_layout_and_missing_files(tmp_path):
    root = str(tmp_path / "neb")
    _w(os.path.join(root, "INCAR"), "IMAGES = 2\nSPRING = -5\n")
    for d in ("00", "01", "02"):
        _w(os.path.join(root, d, "POSCAR"), POSCAR_BASIC)
    _w(os.path.join(root, "00", "OUTCAR"), "x\n")
    # 02 (endpoint) intentionally has no OUTCAR; 01 (interior) has none either.
    out = P.check_neb_layout(root)
    assert any("IMAGES tag value(s)=['2']" in o for o in out)
    assert any("endpoint dir(s) missing an OUTCAR" in o and "02" in o for o in out)

def test_runner_never_blesses(tmp_path):
    # Minimal tree: the report must never say "consistent/OK/valid"; absent
    # dimensions must say N/A.
    _w(str(tmp_path / "INCAR"), "ISPIN = 2\nEDIFFG = -0.02\n")
    report = P.run(str(tmp_path))
    low = report.lower()
    for banned in ("consistent", "looks good", "all clear", "is valid", "no problem"):
        assert banned not in low, f"never-bless violation: '{banned}'"
    assert "N/A" in report
    assert "EDIFFG = -0.02" in report


# --------------------------------------------------------------------------- #
# interatomic minimum distances (PBC minimum-image, triclinic-safe)
# --------------------------------------------------------------------------- #
import random
import numpy as _np


def _poscar_text(lattice, species, counts, coords, mode="Direct",
                 scale=1.0, selective=False):
    """Build a POSCAR string. `lattice` 3x3, `coords` list of [x,y,z] (+ flags
    appended by caller if selective)."""
    out = ["comment", f" {scale}"]
    for row in lattice:
        out.append("  " + "  ".join(f"{v:.12f}" for v in row))
    if species is not None:
        out.append(" " + " ".join(species))
    out.append(" " + " ".join(str(c) for c in counts))
    if selective:
        out.append("Selective dynamics")
    out.append(mode)
    for c in coords:
        out.append("  " + "  ".join(str(x) for x in c))
    return "\n".join(out) + "\n"


def _brute_min(frac, L, K=6):
    """Ground-truth nearest-pair min-image distance by a wide image search."""
    F = _np.asarray(frac, float); L = _np.asarray(L, float); n = len(F)
    D = F[:, None, :] - F[None, :, :]
    D -= _np.round(D)
    best = _np.full((n, n), _np.inf)
    for a in range(-K, K + 1):
        for b in range(-K, K + 1):
            for c in range(-K, K + 1):
                cart = (D + _np.array([a, b, c], float)) @ L
                best = _np.minimum(best, _np.einsum("ijk,ijk->ij", cart, cart))
    _np.fill_diagonal(best, _np.inf)
    return float(_np.sqrt(best.min()))


def test_minimage_cubic_crosses_boundary():
    # Two atoms near opposite faces -> nearest image is across the boundary.
    L = [[5.0, 0, 0], [0, 5.0, 0], [0, 0, 5.0]]
    frac = [[0.02, 0.0, 0.0], [0.98, 0.0, 0.0]]   # 0.2 Å apart across the face
    d, i, j, exact = P._min_image_nearest(frac, L)
    assert exact and abs(d - 0.2) < 1e-6
    assert {i, j} == {0, 1}


def test_minimage_matches_bruteforce_random_cells():
    rng = random.Random(0)
    for trial in range(40):
        # random, sometimes strongly skewed, triclinic cell
        L = [[4 + rng.random() * 4, 0, 0],
             [rng.uniform(-3, 3), 4 + rng.random() * 3, 0],
             [rng.uniform(-3, 3), rng.uniform(-3, 3), 4 + rng.random() * 3]]
        frac = [[rng.random(), rng.random(), rng.random()] for _ in range(8)]
        d, i, j, exact = P._min_image_nearest(frac, L)
        ref = _brute_min(frac, L)
        assert exact, f"trial {trial}: bounded search did not converge"
        assert abs(d - ref) < 1e-6, f"trial {trial}: {d} vs brute {ref}"


def test_minimage_cartesian_equals_direct(tmp_path):
    L = [[6.0, 0, 0], [1.0, 6.0, 0], [0.5, 0.5, 6.0]]
    frac = [[0.1, 0.2, 0.3], [0.4, 0.45, 0.5], [0.9, 0.1, 0.7]]
    cart = (_np.asarray(frac) @ _np.asarray(L)).tolist()
    pd = _w(str(tmp_path / "d" / "POSCAR"),
            _poscar_text(L, ["Li", "F"], [2, 1], frac, mode="Direct"))
    pc = _w(str(tmp_path / "c" / "POSCAR"),
            _poscar_text(L, ["Li", "F"], [2, 1], cart, mode="Cartesian"))
    rd = P._mindist_rec(pd); rc = P._mindist_rec(pc)
    assert rd[0] == rc[0] == "ok"
    assert abs(rd[1] - rc[1]) < 1e-6


def test_minimage_negative_scale_is_volume():
    # scale = -V means "lattice scaled so the cell volume == V".
    L = [[2.0, 0, 0], [0, 2.0, 0], [0, 0, 2.0]]   # det = 8
    frac = [[0.0, 0, 0], [0.5, 0, 0]]
    import textwrap as _tw
    txt = _poscar_text(L, ["H"], [2], frac, scale=-64.0)   # V=64 -> a=4 -> d=2.0
    p = "/tmp/claude_negscale_POSCAR"
    with open(p, "w") as fh:
        fh.write(txt)
    rec = P._mindist_rec(p)
    assert rec[0] == "ok" and abs(rec[1] - 2.0) < 1e-6


def test_minimage_vasp4_no_species_indices_only():
    L = [[5.0, 0, 0], [0, 5.0, 0], [0, 0, 5.0]]
    frac = [[0.0, 0, 0], [0.1, 0, 0]]
    p = _w("/tmp/claude_v4_dir/POSCAR",
           _poscar_text(L, None, [2], frac))     # VASP4: no species line
    rec = P._mindist_rec(p)
    assert rec[0] == "ok" and rec[5] is None     # no per-atom species
    assert P._pair_str(rec[2], rec[3], rec[5]) == "1-2"


def test_minimage_too_few_atoms_not_scanned():
    L = [[5.0, 0, 0], [0, 5.0, 0], [0, 0, 5.0]]
    p = _w("/tmp/claude_oneatom/POSCAR", _poscar_text(L, ["H"], [1], [[0, 0, 0]]))
    assert P._mindist_rec(p)[0] == "few"


def test_check_min_distances_neb_band_flags_outlier(tmp_path):
    # 7-image band; image 03 has a planted 0.4 Å overlap, the rest are clean.
    L = [[10.0, 0, 0], [0, 10.0, 0], [0, 0, 10.0]]
    root = str(tmp_path / "neb")
    paths = []
    for n in range(7):
        if n == 3:
            coords = [[0.0, 0, 0], [0.04, 0, 0], [0.5, 0.5, 0.5]]  # 0.4 Å pair
        else:
            coords = [[0.0, 0, 0], [0.3, 0, 0], [0.6, 0.6, 0.6]]   # ~3 Å min
        paths.append(_w(os.path.join(root, "band", f"{n:02d}", "POSCAR"),
                        _poscar_text(L, ["Li", "F"], [2, 1], coords)))
    out = P.check_min_distances(paths, root)
    body = "\n".join(out)
    assert "NEB band" in body
    assert "FLAG 03=0.40A" in body            # planted overlap flagged on image 03
    assert "smallest 03=0.40A" in body        # identified as the band outlier
    # the clean images are NOT flagged
    assert "FLAG 00" not in body and "FLAG 06" not in body


def test_check_min_distances_never_bless_reports_raw_clean(tmp_path):
    # A clean structure must still surface its raw distance (silence != fine).
    L = [[8.0, 0, 0], [0, 8.0, 0], [0, 0, 8.0]]
    p = _w(str(tmp_path / "POSCAR"),
           _poscar_text(L, ["Li", "F"], [1, 1], [[0.0, 0, 0], [0.5, 0.5, 0.5]]))
    out = P.check_min_distances([p], str(tmp_path))
    body = "\n".join(out)
    assert "6.93" in body                      # sqrt(48)=6.928: raw min still reported
    low = body.lower()
    for banned in ("looks fine", "no close contact", "all clear", "consistent",
                   "no problem", "is fine"):
        assert banned not in low, f"never-bless violation: {banned}"


def test_run_includes_distance_block(tmp_path):
    L = [[5.0, 0, 0], [0, 5.0, 0], [0, 0, 5.0]]
    _w(str(tmp_path / "00" / "POSCAR"),
       _poscar_text(L, ["Li", "F"], [1, 1], [[0, 0, 0], [0.5, 0.5, 0.5]]))
    _w(str(tmp_path / "01" / "POSCAR"),
       _poscar_text(L, ["Li", "F"], [1, 1], [[0, 0, 0], [0.02, 0, 0]]))  # 0.1 Å
    report = P.run(str(tmp_path))
    assert "interatomic_min_distance" in report
    assert "FLAG" in report
