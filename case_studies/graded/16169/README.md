# Topic 16169 — NEB Job Stuck at 84th Iteration Without Error - Assistance Needed

Graeme Henkelman (the expert who answered the original thread) reviewed SaddleAgent's answer to this question and left a grader note. This example pairs that note with the exact answer it grades, the original question, the true expert answer, and the user's files.

- **Graded answer:** `SaddleAgent (with Opus 4.8)`  ·  generated 2026-06-17
- **Grader:** Graeme Henkelman

## Graeme's grader note

> This is a very reasonable AI response.  The question is too vague and there is no data provided to determine the actual problem, but the AI suggestions are reasonable.

## Files

No files were uploaded on this forum topic (text-only question).

## Original question

**Trivanni Yadav** (2024-10-06 13:21):

Hello Dr. Henkelman, 

I’m running NEB calculations using VASP for interstitial diffusion, but my job seems to be stuck at the 84th iteration. There are no error messages or issues in the output files, and the job is still running, but it’s not progressing. I am using 2 nodes with a total of 60 cores. Another job using the same resources with the climbing method ran perfectly fine, so I’m unsure why this one is stuck. 

Additionally, another job for vacancy diffusion got stuck at the 869th iteration, with the climbing method turned on. The strange thing is, I previously studied vacancy diffusion with the same INCAR parameters and the same number of nodes and cores, and that job ran perfectly fine. However, something seems to be going wrong with this particular job.

Here are the relevant details from my INCAR file:

Global Parameters

ISTART = 0           

ISPIN  = 2            # Spin-polarized DFT

ICHARG = 2            # Self-consistent, GGA/LDA band structure

LREAL  = A            # Projection operators: automatic

ENCUT  = 300          # Cut-off energy (eV)

PREC   = Normal       # Precision level

Electronic Relaxation

ISMEAR = 0            # Gaussian smearing

SIGMA  = 0.05         # Smearing value (eV)

NELMIN = 5            # Minimum SCF steps

EDIFF  = 1.0E-05      # SCF energy convergence (eV)

EDIFFG = -0.05        # Force convergence

Ionic Relaxation

NSW = 1800           # Max ionic steps

ISIF = 2             # Stress/relaxation

ICHAIN = 0           # NEB flag (VTST)

IMAGES = 5           # Number of intermediate images

SPRINGS = -5         # Spring constant

LCLIMB = .FALSE.     # No climbing method

IOPT = 3             # Optimization flag

IBRION = 3           # NEB optimization method

POTIM = 0            # Step size

ALGO = Normal

NCORE = 10

Any insights on why the jobs are stuck or how to address this issue would be greatly appreciated!

Thanks in advance!

---

**Trivanni Yadav** (2024-10-06 14:24):

Can I email it to you? I need to maintain the confidentiality of my data.

Thank you!

---

**Trivanni Yadav** (2024-10-07 11:34):

Thank you so much for the reply. I have already emailed it to you; however, I can also share it through the other option you provided.

---

**Trivanni Yadav** (2024-10-07 11:44):

I can only upload one file on the link you provide (90086.tar.gz- Interstitial Diffusion), which is 456 MB in size. The other file is 4.26 GB, and I believe I cannot upload it due to the storage limitation (maximum limit of 500 MB). However, I have already emailed that file (90232.tar.gz-Vacancy Diffusion) to you (from my try0933@utulsa.edu account), and I shared it via a OneDrive link.

---

**Trivanni Yadav** (2024-10-07 19:13):

Just did it. I have uploaded the other one as well. Thank you so much for your help :)

---

**Trivanni Yadav** (2024-10-07 20:55):

Can I upload those stdout files for your review?

---

**Trivanni Yadav** (2024-10-07 21:03):

The issue is that the job is still running, but it is not updating the stdout file. I have just uploaded the stderr and stdout files to the link you provided.

---

**Trivanni Yadav** (2024-10-08 07:52):

Indeed, it’s puzzling. I’m just wondering, since it’s been three days and the job is still running without any new updates, should I just let it continue or do something else? Thank you for the help :)

---

**Trivanni Yadav** (2024-10-08 13:44):

Dr. Henkelman,

I restarted the calculation by copying the CONTCAR of all images (from the 869th iteration) as the new POSCAR files for each image and the job successfully finished in about an hour. However, this is what I got in the neb.dat file:

  0     0.000000     0.000000     0.000000   0

  1     2.256204     0.075494    -0.173653   1

  2     4.512633     0.346478     0.039494   2

  3     6.770738     0.242105    -0.061570   3

  4     9.028678     0.481803    -0.004409   4

  5    13.806147     0.217415    -0.239191   5

  6    18.588887     0.487806     0.000000   6

I can see that the forces are converged, and the first transition state is observed at image 4. However, I noticed that the final structure (image 6) has a higher energy than the transition state, which seems unusual, right?. Is it possible for the final structure to have a higher energy than the transition state in NEB calculations, or could this indicate some other issue?

Thank you for your guidance! I really appreciate all your help :)

## Expert answer (forum ground truth)

**graeme** (2024-10-06 14:20):

if you post your calculation, I will take a look at it.

---

**graeme** (2024-10-07 04:20):

You can get it to me in any way that works for you.  If the files are too large for email, I'll provide an option.

---

**graeme** (2024-10-07 19:04):

just for others: you can remove all CHG* / WAV* files before uploading; these files are the largest and do not help for debugging problems with NEB / dimer issues.

---

**graeme** (2024-10-07 20:52):

I don't see any problems with your calculations, but I also don't see the stdout (what it prints to the screen or a file that you specify in our submit script).  My guess is that the calculation is running out of the allocated time and is being killed by the scheduler.

You can always continue these calculations.  We have the 'vfin.pl subdir' which will move the important files to subdir and leave it ready to restart.

---

**graeme** (2024-10-07 21:36):

Ok, I see what you mean and it is puzzling.  It's like vasp has quit internally, but not terminated.  It is at the end of a set of electronic iterations, so it's not stalling at a random place.  My advice is to continue the calculation when you see this.  I will also think about this some more - I just don't have a good idea about what is going on at the moment.

---

**graeme** (2024-10-08 07:56):

I would kill it and restart (continue).  My guess is that the mpi communicator is not passing along the kill message to the process.  I don't have a solution - if you want to dig into this, I would look for things like 'stop processes on exit' in the queue settings.  I do think this is unrelated to our vtst code, and hopefully the jobs are finishing properly, just not exiting.

---

**graeme** (2024-10-08 13:58):

Yes, but that is not a fault of the method.  There can be an intermediate minimum (or minima) along a path that you chose and that could lead to a saddle with a higher energy than an endpoint.

## The graded AI answer (SaddleAgent (with Opus 4.8))

**Bottom line: your INCAR is not the problem — `IBRION=3 / POTIM=0 / IOPT=3` is the correct, robust VTST QuickMin setup, and the same deck ran fine before. A "still running, no errors, ionic counter frozen" NEB is almost always one of two things: (A) the normal NEB lockstep where one slow image is holding the whole band, or (B) an environmental MPI/node stall on this particular allocation. The single check that tells them apart is whether the per-image `OSZICAR`/`OUTCAR` files are still being written.** Do that check first — everything else follows from it.

Why I'm confident it's not the input: NEB advances **all images together** every ionic step — there is no serial-image mode, so the global ionic step only fires after *every* image has finished its SCF (verified in the VTST NEB docs). One image that lands in a hard electronic state stalls the counter for the entire band, with **no error**. And since you said both the interstitial deck and a previously-working vacancy deck (identical INCAR, same nodes/cores) are now hanging mid-run, the common factor is the run environment, not the tags.

## Step 1 — Is it actually frozen, or just slow? (run these in the NEB directory)

```
ls -lrt 0[1-5]/OSZICAR 0[1-5]/OUTCAR     # are any mtimes within the last minute?
tail -n 3 0[1-5]/OSZICAR                  # is any image still emitting DAV/RMM electronic steps?
```

Watch for ~60 s. Then find the lagging image's SCF behavior:

```
grep -c 'DAV\|RMM' 0[1-5]/OSZICAR         # the image with way more SCF lines is the culprit
```

(Default `NELM=60` — you didn't set it — so SCF caps at 60 per ionic step and shouldn't hang *forever* on its own. That's the discriminator below.)

## Branch A — files ARE still updating (one image grinding SCF each step)

This is the **by-design lockstep**, not a bug. At iteration 84 (interstitial squeezing through) and 869 (CI image sitting on the saddle), the converging image is exactly where the electronic structure gets hard. Options, cheapest first:

- **Be patient** — it self-resolves once that image converges.

- If it's chronically hitting `NELM=60` every step: the fix is SCF convergence, not raising NELM blindly. Try `ALGO=Fast` (or `All` if you see charge sloshing); `NELMIN=5` is already fine.

- Check that image's geometry: `grep -m1 'DAV\|RMM' 0[1-5]/OSZICAR` to find the outlier, then look at its `POSCAR`/`CONTCAR` for any **sub-1 Å atom pair** — linear interpolation can drag the diffusing atom too close to an occupied site, which makes SCF brutal. If so, rebuild the band with `nebmake.py` (IDPP interpolation). *(Less likely here, since that would stall from step 1, not step 84.)*

## Branch B — files are NOT updating (all mtimes stale, job still "running") ← my leading suspicion

That's a genuine **MPI/interconnect or node stall** — a rank deadlocked on the collective barrier, no crash, so VASP prints nothing. This fits your strongest clue: *same inputs + same requested resources ran fine before* → the requested resources are identical but the **physical nodes this time differ**, and one is flaky. Fix:

```
# in each image dir, seed the restart from the latest geometry
for d in 0[1-5]; do cp $d/CONTCAR $d/POSCAR; done
```

Then **kill and resubmit**, ideally onto a fresh allocation/node. NEB restarts cleanly from the per-image `CONTCAR`s and self-recovers; you lose only the current unfinished step. If it stalls again at a similar wall-clock point, ask your cluster admins to check that node/interconnect, and confirm your job script isn't set to "wait/hold on exit."

## On sending me files

You don't need to expose anything confidential — no atomic coordinates are involved in this diagnosis. What pins it down is text-only and structure-free:

1. `tail -n 5 0[1-5]/OSZICAR` (electronic steps/timestamps),

2. the `ls -lrt` mtimes above,

3. the first ~40 lines of one `OUTCAR` (so I can confirm the `vasp.6.x`/`vasp.5.x` and `VTST: version` banners — a quick build sanity check), and

4. the scheduler stdout/stderr for the job.

Paste those here and I'll tell you definitively whether it's the slow-image lockstep (A) or a node stall (B), and exactly what to change. My confidence the INCAR is innocent is high; A-vs-B I can only call once I see whether the files are still ticking.
