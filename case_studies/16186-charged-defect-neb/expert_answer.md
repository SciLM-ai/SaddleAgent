# Expert answer (ground truth) — forum topic 16186

The real answer from the Henkelman Group forum expert.

**graeme** (expert, 2025-06-06 12:52):

If you post the calculation, I can take a look, but I expect that you need to remove and CHG* and WAV* files.  It will read those files by default and if you have changed the number of electrons in your INCAR file, vasp will complain.

---

**graeme** (expert, 2025-06-06 17:34):

The problem is that in your initial band, you have atoms running into each other.  Take a look at the initial movie in a viewer and you will see the problem.  Also, there is a warning in each ??/OUTCAR that atoms are too close - you can see it in the neighborlists.

The problem is a result of atom ordering; make sure that each atom in your initial structure corresponds to the same atom in the final structure.
