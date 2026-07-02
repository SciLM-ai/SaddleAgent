# POTCAR

> Source: <https://www.vasp.at/wiki/index.php/POTCAR>

The pseudopotential / PAW file. It is the **concatenation of one block per atomic species, in the SAME ORDER as the species appear in the POSCAR**.

**Key data per species:**
- `TITEL` — potential type, element, functional, date. Suffixes mark valence: `_sv` (semicore s+p in valence), `_pv` (p in valence), `_d` (d in valence), `_h` (harder, higher cutoff).
- `ZVAL` — number of valence electrons.
- `POMASS` — atomic mass.
- `ENMAX` / `ENMIN` — recommended / minimum plane-wave cutoff (eV) — these set the default [`ENCUT`](encut.md).
- `EAUG` — augmentation-charge cutoff (eV).
- `LEXCH` — the exchange-correlation functional the potential was generated with.

**Critical rules:**
- **Order must match POSCAR.** Build it with `cat`: `cat Al/POTCAR C/POTCAR > POTCAR`.
- Don't mix XC functionals across species; set XC/`GGA`/`METAGGA` in the **INCAR**, not by editing the POTCAR (never edit `LEXCH`).
- Multi-species runs use the maximum `ENMAX`/`ENMIN`.
- METAGGA needs kinetic-energy-density core data — verify the POTCAR provides it.

**Related:** POSCAR, ENCUT, ENAUG, GGA/METAGGA.
