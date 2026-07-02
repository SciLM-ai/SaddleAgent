# Nudged Elastic Band (NEB)

> VTST Tools method page. Converted from VTST `neb.html`. See also: [optimizers.md](optimizers.md), [scripts.md](scripts.md), [dimer.md](dimer.md).

The nudged elastic band (NEB) finds saddle points and minimum energy paths (MEPs) between a **known** reactant and product. It optimizes a chain of intermediate **images** along the path; each image lowers its energy while staying equally spaced from its neighbours. Spacing is held by spring forces *along* the band, and the potential force *perpendicular* to the band is projected out, so the chain relaxes onto the MEP.

## Difference from the NEB built into VASP
VASP ships with its **own** elastic-band NEB (in `chain.F`, since v4.6), which runs **without
VTST at all**: it builds the band, applies the spring force along the path and the projected
perpendicular potential force, couples the images, and optimizes a genuine MEP. VTST does not
*enable* NEB — it **improves** it, adding:

- **Climbing image** — the highest-energy image is driven exactly onto the saddle (`LCLIMB`).
- **Improved tangent** — a better tangent definition, giving more accurate saddles with fewer images.
- **External optimizers** — the `IOPT` methods (`docs/vtst/optimizers.md`), engaged by `IBRION=3, POTIM=0`.

Setup is otherwise identical to the VASP manual's elastic-band section. The improved tangent is **on by default**; turn on the climbing image with `LCLIMB = .TRUE.`.

### Is VTST actually linked? (do not guess from NEB output)
This is the single most-confused linkage question, so read carefully. **The stock VASP elastic
band prints the *same* per-image force output a VTST run does:** the
`TANGENT … CHAIN-FORCE (eV/Angst)` block, the `CHAIN + TOTAL (eV/Angst)` block, the spring
forces, and a perfectly sensible coupled barrier all appear **with or without VTST**. They are
therefore **neutral on linkage** — seeing them proves only that *some* NEB ran, not that VTST ran.
Inferring "VTST is linked" from a coupled barrier, `TANGENT`, `CHAIN-FORCE`, or `CHAIN + TOTAL`
is a **non-sequitur**; native VASP produces every one of them.

The discriminators (what only a VTST-linked binary prints):

| Signal in OUTCAR | Meaning |
|---|---|
| `VTST: version X.Y.Z` startup banner | **The only positive proof of linkage.** Printed for *any* calc type by every patched build; it is a fixed string, not build-dependent. |
| `NEB:` verbose projection lines (`NEB: projections`, `NEB: distance …`) | VTST-only; `nebbarrier.pl` parses them. Their presence corroborates linkage; **absence** alongside `CHAIN + TOTAL` ⇒ native VASP NEB. |
| `OPT:` optimizer lines | VTST-only (the `IOPT` optimizers). Present ⇒ linked. **Absent is inconclusive** — a VTST binary with `IBRION≠3` runs VASP's native optimizer and prints no `OPT:` line. |

**Rule:** decide linkage from the `VTST: version` banner (corroborate with `NEB:`/`OPT:` lines), never
from the presence of `TANGENT`/`CHAIN-FORCE`/`CHAIN + TOTAL`/springs. **NEB force output present +
`VTST: version` banner absent = VASP's own elastic-band NEB ran = VTST is NOT linked**, and every
VTST tag (`LCLIMB`/`IOPT`/`ICHAIN`/`LNEBCELL`/…) was silently ignored — the classic cause of a
kinked/over-wiggly MEP or interior forces that won't drop. Do not explain an absent banner away as a
"this build's format" difference; the banner is absent because the code is not there.

## Climbing image (cNEB)
The climbing image does **not** feel the spring forces. Instead its true force *along the tangent is inverted*, so it maximizes energy along the band and minimizes in every perpendicular direction; on convergence it sits at the exact saddle. Because that image is exempt from springs, the image spacing on the two sides of the saddle generally differs.

Run plain NEB **first**, before enabling the climbing image, so that (a) the reaction coordinate near the saddle is well estimated and (b) the highest image is already close to the saddle. Starting climbing from the outset, with the maximum image far from the saddle, can produce very uneven spacing on the two sides.

## INCAR parameters
| Variable | Default | Type | Description |
|---|---|---|---|
| `ICHAIN` | `0` | int | Method selector. **0 = NEB** (default). |
| `IMAGES` | none | int | Number of NEB images **between** the two fixed endpoints. |
| `SPRING` | `-5.0` | float | Spring constant (eV/Å²) between images. A **negative** value turns on nudging (standard NEB). |
| `LCLIMB` | `.TRUE.` | bool | Turn on the climbing-image algorithm. |
| `LTANGENTOLD` | `.FALSE.` | bool | Use the old central-difference tangent. |
| `LDNEB` | `.FALSE.` | bool | Turn on modified double-nudging. |
| `LNEBCELL` | `.FALSE.` | bool | Turn on solid-state NEB (SS-NEB). Use with `ISIF=3` and `IOPT=3`. |
| `JACOBIAN` | (Ω/N)^{1/3}·N^{1/2} | real | Weight of lattice vs atomic motion (Ω = cell volume, N = number of atoms). Used by SS-NEB. |

**Don't forget the [optimizer](optimizers.md) parameters** — a force-projected method requires a force-based optimizer: set `IBRION=3`, `POTIM=0`, and choose an `IOPT`. Step count and force convergence are set by [`NSW`](../vasp/nsw.md) and [`EDIFFG`](../vasp/ediffg.md) (must be negative).

## Run layout
A NEB runs in two-digit image directories `00, 01, …, NN`. `00` and `NN` hold the fixed endpoint structures (reactant / product); the `IMAGES` intermediate folders hold the moving images, each with its own `POSCAR`. Build the band with `nebmake.pl`; monitor with `nebef.pl`/`nebbarrier.pl`; collect and spline the finished MEP with `nebresults.pl`/`nebspline.pl` (see [scripts.md](scripts.md)).

## References
- G. Henkelman, B. P. Uberuaga, H. Jónsson, *J. Chem. Phys.* **113**, 9901 (2000) — climbing-image NEB. [DOI](http://dx.doi.org/10.1063/1.1329672)
- G. Henkelman, H. Jónsson, *J. Chem. Phys.* **113**, 9978 (2000) — improved tangent. [DOI](http://dx.doi.org/10.1063/1.1323224)
