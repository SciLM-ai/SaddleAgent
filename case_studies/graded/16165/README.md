# Topic 16165 — VASP aborting ... with vasp.6.4.2+vtstcode6.4

Graeme Henkelman (the expert who answered the original thread) reviewed SaddleAgent's answer to this question and left a grader note. This example pairs that note with the exact answer it grades, the original question, the true expert answer, and the user's files.

- **Graded answer:** `SaddleAgent (with Opus 4.8)`  ·  generated 2026-06-17
- **Grader:** Graeme Henkelman
- **Trace:** [`trace.md`](trace.md) — the graded run's step-by-step thinking and full tool-call log

## Graeme's grader note

> AI is completely wrong and is just spewing bullshit.  I identified the problem of a misspelling of EDIFFG, which is the correct answer.

## Files

`files/` — the complete upload (11 files; `POTCAR` excepted, for licensing).

## Original question

**MCV** (2024-07-01 08:30):

Dear VTST developpers,

I have compiled vasp.6.4.2 with vtstcode6.4 according to instructions in your group (https://theory.cm.utexas.edu/vtsttools/installation.html). I have done that in two HPC clusters with the help of my institue's computer engineer. Although plain vasp calculations work perfectly, we don't manage run VTST and this is what we get in the standard ouput:

 

running   36 mpi-ranks, on    1 nodes

 distrk:  each k-point on    9 cores,    4 groups

 distr:  one band on    9 cores,    1 groups

 vasp.6.4.2 20Jul23 (build Jul  1 2024 14:43:42) complex

 POSCAR found :  3 types and      43 ions

 scaLAPACK will be used

 LDA part: xc-table for Pade appr. of Perdew

 VASP aborting ...

 VASP aborting ...

 VASP aborting ...

 VASP aborting ...

 VASP aborting ...

 VASP aborting ...

 VASP aborting ...

 VASP aborting ...

 VASP aborting ...

Do you have a hint on why this happens? Could you please help us to solve this issue?

Thank you very much.

Kind regards,

MCV

---

**MCV** (2024-07-02 01:03):

P.S.: I forgot to mention one additional comment. Below there are the last lines writtent in the OUTCAR file. There is a message from the VTST script that makes no sense.

"

 VTST: version 4.1, (05/19/21)

 CHAIN: initializing optimizer

 OPT: Using Conjugate-Gradient optimizer

 OPT: CG, Init

 OPT: CG, FDSTEP      0.005000

 OPT: CG, MAXMOVE      0.200000

 Must set  EDIFFG < 0 when using IOPT > 0"

EDIFFG is defenitely <0 in my INCAR file.

Regards,

MCV

---

**MCV** (2024-07-04 06:36):

Hello,

There it is.

Thanks.

MCV

---

**MCV** (2024-07-05 01:52):

Dear Graeme,

Oops, my bad! Sorry for such an improductive thread in the forum.

Despite many years working with VASP, I'm afraid I can still produce this kind of typos... 

Thanks a lot,

MCV

## Expert answer (forum ground truth)

**graeme** (2024-07-03 20:28):

If you post a .tar.gz of your calculation, I can take a look.

---

**graeme** (2024-07-04 10:15):

change:

   EDDIFG = -0.01 

to

   EDIFFG = -0.01

---

**graeme** (2024-07-05 04:18):

I'm right there with you!

## The graded AI answer (SaddleAgent (with Opus 4.8))

**Your binary is almost certainly fine — this is an NEB *run-setup* problem, not a broken compile.** Plain VASP works and it fails *identically* on two independently built clusters, which is the opposite of what a bad compile looks like (those differ machine-to-machine). The abort fires exactly where VASP's VTST chain code initializes the images — right after the `LDA part: xc-table…` line, before the first SCF step. The usual trigger there is that your **total MPI rank count isn't an integer multiple of `IMAGES`**, or the `00…NN` image directories are inconsistent. First, go get the *real* error text — "VASP aborting ..." is just the generic tail.

### Why I land there

- `running 36 mpi-ranks … vasp.6.4.2 … complex` → you *are* running an MPI, full‑k‑point `vasp_std` build under a launcher. So this is **not** a serial binary and **not** a bare-launch-collapses-to-one-rank case (those are the other two common VTST launch failures). Good — that rules a lot out.

- `POSCAR found : 3 types and 43 ions` with a *single* banner → it's also **not** the "POSCARs only in `00/`,`01/`… , none in parent" crash (that prints a banner *per rank* plus `POSCAR does not exist`). Yours got past POSCAR read into chain init, then aborted.

- The crash point (immediately after the xc-table, before any electronic step) is the VTST chain/image setup: partitioning ranks across images and reading each image's POSCAR.

### Run these four checks (cheapest → most likely to be the bug)

1.

**Get the actual message.** `VASP aborting ...` is what every rank prints on the way out; VASP 6 writes the real cause separately. Look at:

```
tail -40 OUTCAR
```

plus your scheduler's **stderr** file and the stdout *just above* where you truncated. Paste that line — it usually names the cause outright.

2.

**`IMAGES` vs rank count (most likely culprit).**

```
grep -i images INCAR
```

The rule is hard: **`IMAGES` must divide the total MPI ranks**, ≥1 rank per image. With **36 ranks**, `IMAGES` must be one of `1,2,3,4,6,9,12,18,36` — **not 5, 7, 8, 10, 11…**. If you picked `IMAGES=8` (36/8=4.5) or `IMAGES=5` (36/5=7.2) → instant abort. Note your stdout shows `KPAR`/`NCORE` already eating all 36 ranks (`9 cores × 4 groups = 36`) for a *single* image group, so if you also set `IMAGES>1`, `IMAGES × KPAR × NCORE` can't reconcile with 36 either. Fix by matching ranks to `IMAGES` (e.g. 40 ranks for `IMAGES=8`/`5`) **or** changing `IMAGES`; and make sure `KPAR`/`NCORE` divide the *per-image* rank count, not the global one.

3.

**Directory layout.**

```
ls -d [0-9][0-9]/
```

You must see `00 01 … NN` with `NN = IMAGES+1`. `00` and `NN` are the **relaxed endpoints**; each interior folder holds its own `POSCAR`. INCAR/KPOINTS/POTCAR live only in the parent.

4.

**Per-image POSCAR consistency.** Every image's POSCAR must have the **same atom count and ordering** (your 43 ions / 3 types) — a mismatched count makes chain init abort right where yours does. Quick check:

```
for d in [0-9][0-9]; do echo -n "$d: "; sed -n '7p' $d/POSCAR; done
```

### Lower-probability (only if 1–4 are clean)

Since it's a fresh build, reproduce a **known-good VTST example** (the Henkelman group ships small NEB test cases) on the same nodes. If a canonical NEB *also* aborts identically, then suspect the build — diff your `makefile.include` against the reference (`OFLAG=-O2`, never `-fast`/`-ipo`; ScaLAPACK + the *matching* MPI's BLACS). But the two-clusters-fail-identically + plain-VASP-works pattern makes this unlikely.

### What I need to pin it exactly

You didn't attach files. Send me: your **INCAR**, the **tail of OUTCAR + the stderr file** (the real error), and `ls -d [0-9][0-9]/` from the run directory. My money (~70%) is on check **#2** (IMAGES not dividing 36, possibly compounded by KPAR/NCORE); ~20% on **#3/#4**; the rest on the build.
