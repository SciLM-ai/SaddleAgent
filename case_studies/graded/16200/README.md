# Topic 16200 — Neb under external stress

Graeme Henkelman (the expert who answered the original thread) reviewed SaddleAgent's answer to this question and left a grader note. This example pairs that note with the exact answer it grades, the original question, the true expert answer, and the user's files.

- **Graded answer:** `SaddleAgent (with Opus 4.8)`  ·  generated 2026-06-17
- **Grader:** Graeme Henkelman

## Graeme's grader note

> wow, just wow.  AI can sound so confident and be really stupid.  There is no averaging of the stress in a vasp calculation, unless you have some ISIF setting that relaxes the volume with the ratio of cell vectors constrained.  Also, the question is asking about a lateral stress, not a normal stress.  The AI is correct this can be done with ASE, but if the AI could learn from my answer, there is a variable in VTST which allows for the application of an external pressure.  And again, doubling down on the problem of a normal stress in the AI explanation does not make any sense when the stress can be input as a matrix.  Again, it is unfortunate that the AI sounds very confident while at the same time getting fundamental concepts wrong.

## Files

No files were uploaded on this forum topic (text-only question).

## Original question

**yudeng** (2025-12-30 02:09):

Dear graeme,

I would like to simulate the sliding energy barrier of an interface system with a vacuum layer under constant stress. Could you please let me know if tsase or vtst has relevant functionalities for this? I noticed that ssneb seems to apply stress by changing the cell, but in my case, since there is a vacuum layer along the z-axis, the stress needs to be applied by adjusting the atomic distances.

Thank you very much!

Best wishes

Yu

## Expert answer (forum ground truth)

**graeme** (2025-12-30 11:00):

I'm a little puzzled by the question because it seems to imply two incongruous desires.  If you want to shift a layer of atoms based upon atomic positions, of course, you can do that.  But if you want to apply a constant stress, to me, that nessecarily means that it is applied in the cell degrees of freedom.  I'm not sure that the vacuum in the z-direction is a problem.  You should be able to calculate a barrier for a sliding layer under an an-isotropic constant stress in tsase without causing a change in the z-direction.  This would be defined by the 'express' variable which is the external pressure matrix in the ssneb in tsase.

## The graded AI answer (SaddleAgent (with Opus 4.8))

**Bottom line:** Neither tool does what you want out of the box, and SS‑NEB is the wrong instrument here. SS‑NEB (`LNEBCELL`) applies stress *only* through the cell vectors, so with a vacuum layer along z it just strains the vacuum and averages the stress over the whole supercell — it never imposes a real normal traction on the interface. What you want is a **constant‑load (force‑controlled) calculation**: apply the normal stress as a constant external force on a rigid "grip" layer of atoms and run an ordinary CI‑NEB on that loaded surface. There's no turnkey flag for this in VTST, but you can build it cleanly in tsase/ASE with an external‑force constraint + NEB, and that's the route I'd recommend.

**Why SS‑NEB doesn't apply here.** SS‑NEB (the GSSNEB method, Sheppard, Xiao, Chemelewski, Johnson, Henkelman, *JCP* **136**, 074103, 2012) treats the lattice vectors as extra degrees of freedom, weights them against the atomic motion through the `JACOBIAN`, and is meant to be run with `ISIF=3, IOPT=3` (per `docs/vtst/neb.md`). The applied stress couples to the cell. For a bulk solid that's exactly right. For a slab the cell volume is mostly vacuum, so (i) σ·V work and the strain energy are spread over vacuum that carries no load, and (ii) deforming the z lattice vector changes the vacuum gap, not the interfacial spacing. The "stress" you'd impose is not the interface normal stress. Your instinct — apply the load via atomic distances, not the cell — is correct.

**The right picture: constant separation vs. constant load.**

- *Constant separation (displacement‑controlled):* freeze the outer layer z's, fix the gap, slide. This is the usual γ‑surface / generalized stacking‑fault setup — but it's **constant strain, not constant stress**.

- *Constant load (force‑controlled):* push the slab together with a fixed external force F = σ·A (A = the in‑plane cell area, *excluding* vacuum), let the interface gap relax to whatever spacing balances that load, and slide. **This is your "constant stress."** The proper potential each image minimizes is the loaded enthalpy H = E_DFT − F·z_grip (equivalently E_DFT + σ·A·d), and that's what you read the barrier off.

**How to do it (tsase/ASE driving VASP):**

1. Designate a rigid grip: the top 1–2 atomic layers as the loading platen; fix the bottom layer with `FixAtoms` (ASE constraints, used the same way as in `docs/ase/dimer.md`).

2. Add a constant force F_z per grip atom with F_z = σ_zz·A / N_grip. The energy‑consistent way is a thin calculator wrapper so E and forces stay consistent for the NEB projection:

```
import numpy as np
from ase.calculators.calculator import Calculator, all_changes

class ConstantLoad(Calculator):
    implemented_properties = ['energy', 'forces']
    def __init__(self, calc, grip, f):      # f = per-grip-atom force, e.g. [0,0,-Fz]
        super().__init__(); self.calc, self.grip, self.f = calc, grip, np.asarray(f)
    def calculate(self, atoms, properties, system_changes=all_changes):
        super().calculate(atoms, properties, system_changes)
        F = self.calc.get_forces(atoms).copy()
        E = self.calc.get_potential_energy(atoms)
        F[self.grip] += self.f
        E -= (atoms.positions[self.grip] * self.f).sum()   # -F·x ⇒ -dE/dx = +F
        self.results = {'energy': E, 'forces': F}
```

Wrap the ASE `Vasp` calculator (`docs/ase/vasp_calculator.md`) with this, attach it to every image, and run a CI‑NEB (`ase.mep.neb`, IDPP interpolation between the two lateral registries — `docs/ase/neb.md`). Each image relaxes its own interface spacing under the same load, so the whole MEP sits at constant normal stress.

**If you'd rather stay in pure VASP/VTST:** there's no INCAR tag for a per‑atom mechanical load, so you can't impose constant stress directly. Your only native option is displacement control — freeze the grip‑layer z via selective dynamics, run a standard CI‑NEB, and read σ_zz back from the OUTCAR stress / the reaction force on the frozen layer — then iterate the gap per image to hit a target stress. That's clumsy and only approximate. The tsase route above is much cleaner and is what I'd use.

**Confidence:** High on the diagnosis (SS‑NEB's stress is cell‑based and ill‑defined across vacuum — grounded in `docs/vtst/neb.md` and the GSSNEB paper) and on the constant‑load construction being the correct physics. Medium only on the exact tsase API surface, since the constant‑load wrapper is something you assemble from ASE primitives rather than a packaged tsase command.

If you can tell me whether you want a **normal** load (most likely, for a sliding/friction barrier) or a constant **shear** load, and roughly the target stress and slab geometry (cell area, # layers), I'll give you the exact F_z and a ready‑to‑run NEB script.

Best,
Graeme
