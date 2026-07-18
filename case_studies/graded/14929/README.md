# Topic 14929 — Convergence issue with cation migration in bulk tio2

Graeme Henkelman (the expert who answered the original thread) reviewed SaddleAgent's answer to this question and left a grader note. This example pairs that note with the exact answer it grades, the original question, the true expert answer, and the user's files.

- **Graded answer:** `SaddleAgent (with Opus 4.8)`  ·  generated 2026-06-17
- **Grader:** Graeme Henkelman

## Graeme's grader note

> The AI response is remarkably good!

## Files

No files were uploaded on this forum topic (text-only question).

## Original question

**ipcxj1** (2022-07-25 08:10):

Dear Prof. Henkelman,

I am new to using CINEB calculations. I am trying to study the pathway of Ti atom from 1 site to the adjacent  interstitial site in Ti73O143. (The original structure is supercell composed of 3*3*2  anatase tio2 . I have created 1 O vacancy and relaxed the structure. IS was also relaxed with the same INCAR). In the past few weeks,  I have read most of the posts about speeding up convergence （using conservative optimizer of iopt=3, cheap setup). But I failed and I don't know why.

I noticed that you mentioned the problem of image translation. I checked my images and nothing seems to be happening. Can you please confirm it for me? Also, I noticed your comment about freezing an atom for slab model, but not for the bulk materials. Therefore, I would like to ask you to confirm whether this method is suitable for the bulk materials. Although I have tried frozen an atom, it still failed to converge.

Another question, when constructing the bulk model with a vacancy, is there a difference between the O vacancy constructed in the center of the supercell and the area near the surface  of the supercell?

Could you please help me understand why this is happening and what I must do to correct this ? I have attached the files here.

Thanks for your help and support.

Jing Xia

---

**ipcxj1** (2022-07-25 09:47):

Dear Prof. Henkelman:

   I didn't expect to receive your reply so quickly, thank you very much.

   I haven't slept well for weeks because of this problem. I have tried almost all the methods mentioned in the forum.

    In fact, in order to get most stable structure （IS and FS）, I have already tried to relax the cell without a vacancy (ISIF=3 or 2) and then leave the cell fixed for IS and FS optimizations (ISIF=2 or 3), but I got the same result failed.

    " I don't get what is going on in the HIGH calculation; it is not using our vtstcode. I guess you are trying to optimize the NEB with more kpoints, which is fine, but you will need to link in our vtstcode in your vasp binary as you did with vasp_gam..". Yes ,I am trying to optimize the CINEB with more kpoints  using the CONTCAR results from  MIDDLE. I don't understand why you said I didn't link the two programs. How did you come to this conclusion. In fact, I have linked the vtstcode to our vasp5.4, no matter vasp_gam or vasp_std. Maybe my problem just comes from the linking bewteen the vasp_std (I renamed it as vasp) and vtstcode. But I don't know how to judge whether the linking is successful.

   

Thanks for your help and support.

Jing

Below is the script I used for cineb.

#!/bin/sh

##job1-LOW_cineb

cd LOW

pwd

rm cineb_time1

time mpirun -np 64 vasp_gam

T=$(grep "CPU"  01/OUTCAR | tail -1 | awk '{printf "%-12.6f \n", $6}')

T1=$(echo "scale=2; $T/3600" | bc)

echo cineb_time1=$T1 h >> cineb_time1

cd ..

##job2 MIDDLE_cineb

cd MIDDLE

pwd

rm cineb_time2

cp ../LOW/cineb_time1   cineb_time2

for i in {0..9};

do

rm -rf  0$i

cp  -rf ../LOW/0$i   0$i

cd 0$i

mv  CONTCAR POSCAR

cd ..

done

time mpirun -np 64 vasp_gam

T=$(grep "CPU" 01/OUTCAR | tail -1 | awk '{printf "%-12.6f \n", $6}')

T2=$(echo "scale=2; $T/3600" | bc)

echo cineb_time2=$T2 h >> cineb_time2

cd ..

##job3 HIGH cineb

cd HIGH

pwd

rm cineb_time3

cp ../MIDDLE/cineb_time2 cineb_time3

for i in {0..9};

do

rm -rf  0$i

cp -rf ../MIDDLE/0$i   0$i

cd 0$i

mv  CONTCAR POSCAR

cd ..

done

time mpirun -np 64 vasp

T=$(grep "CPU" 01/OUTCAR | tail -1 | awk '{printf "%-12.6f \n", $6}')

T3=$(echo "scale=2; $T/3600" | bc)

echo cineb_time3=$T3 h >> cineb_time3

total_time=$(echo "scale=2; $T1+$T2+$T3" | bc)

echo total_time=$total_time h >> cineb_time3

cat cineb_time3

---

**ipcxj1** (2022-07-25 18:13):

Dear Professor Graeme,

Thanks a lot for your reply and help. It did work!

This morning, I checked VTST in the OUTCAR of HIGH. You are right, there is no link bewteen the vasp and the vtst code. 

So I try to ran CINEB in HIGH alone and get a new OUTCAR. Interestingly, I can find ' "VTST: version 3.2.." in the new OUTCAR. I tried several times and I can find the VTST characters in the new OUTCAR.  I don't know why this happens, but I know the source of the problem and I think I can fix it.

Once again, I would like to express my sincerest thanks for your help.

Jing

---

**ipcxj1** (2022-07-27 19:55):

Dear Prof. Henkelman,

      Following your suggestion, I rebuilt the supercells（tio2,4*4*1 and 3*3*1）. In the supercell 4*4*1, a Ti atom is frozen and no atom is fixed in supercell 3*3*1. I check the vtst, it is linked to vasp. Unfortunately， both cases can not converge. 

     

     Do you think the reason for not converging is because there are only shoulders? For the case where only the shoulder exists, and no transition state, the calculations are meaningless?

   Could you please help me ? I have attached the files her.

   Thanks  very much for your help.

Jing

---

**ipcxj1** (2022-07-28 17:24):

Dear Professor Graeme,

Thank you  very much  for your reply. In my experience,  I think  200  is  enough  for  cineb.  If not , the mode, path   or setup  may be not good. However, I will  continue the 

calculation  and  tell  you the results. 

 Thanks again. 

Jing

---

**ipcxj1** (2022-07-29 01:06):

Dear Professor Graeme,

I got it. Thank you for your reply.

Have a good day。

Jing

## Expert answer (forum ground truth)

**graeme** (2022-07-25 09:06):

These calculations are generally looking ok.  I have just a few suggestions:

1. relax the cell without a vacancy (ISIF=3) and then leave the cell fixed for your IS and FS optimizations (ISIF=2) so that the cell does not change over the NEB.

2. I see a small shift in the structures, which is not really a problem, but could be avoided by freezing an atom.

3. These are periodic calculations, so it doesn't matter where the vacancy is in the cell.

4. Your MIDDLE calculation looks reasonable.  The max forces are below 0.1 eV/Ang, and with some additional iterations there will be tighter convergence.  To speed things up, you can try IOPT=1 or IOPT=2.  But what you are doing (IOPT=3) is a nice slow and steady optimizer.

5. I don't get what is going on in the HIGH calculation; it is not using our vtstcode.  I guess you are trying to optimize the NEB with more kpoints, which is fine, but you will need to link in our vtstcode in your vasp binary as you did with vasp_gam.

---

**graeme** (2022-07-25 10:18):

Oh goodness, you shouldn't lose sleep over the calculation of vacancy diffusion!  This is not a difficult calculation - it is just a matter of making a few adjustments.

First, you can check if the vtstcode is linked in by greping for VTST in any OUTCAR file and look for a line such as: "VTST: version 3.2, (02/03/18)".  You can find it in your MIDDLE calculation, using the vasp_gam binary, but not the HIGH calculation, using the vasp binary.

I also can't help but make a few suggestions which everyone in my group has to repeatedly endure.  I strongly recommend starting with cheap computational settings and then reconverging to test your parameters.  In your case, starting from a gamma point calculation and then going to higher k-point sampling is exactly this idea.  But there are other such system parameters including the cell size, choice of pseudopotential and energy cutoff.  In your case, I would recommend starting with a regular Ti potential (not _sv), as well as O_s (not O) and a cutoff of about 274 eV.  I would also cut down your cell in the z-direction or find another way to find a smaller roughly cubic cell.  This changes would save you more than an order of magnitude in computational time, and make it so much faster to do your saddle calculations.  Once you have a nicely converged  NEB calculation, it is trivial to try a different pseudopotential or increase the cutoff or add kpoints or whatever parameters you are worried about, and also then learn if those parameters are important to the quantity that you care about, such as the diffusion barrier.  Starting with the most expensive parameters that you can afford, on the other hand, makes all the calculation slow so that you might not be able to converge things, and you don't have any sense for which settings are important for the precision/accuracy that you have.  Putting this simply: start cheap and get quick convergence and then test your settings in terms of the quantity that you care about.

Also, in terms of the science, it appears to me that you are moving a vacancy to a site that is ~2eV less stable in the FS as compared to the IS and there is just a small reverse barrier.  So thinking about what is important here, it may be primarily the energy difference between the IS and FS.

---

**graeme** (2022-07-28 10:17):

I think there may be a misunderstanding about convergence.  Take, for example, your 331/CINEB_NO_FIX/LOW , you can see a single barrier around 4.9 eV.  It is true that this is not converged in the sense that the forces are around 0.4 eV/Ang and you have requested maximum forces of 0.05 eV/Ang.  But that is because you are using a conservative optimizer (IOPT=3) and allowed only 200 iterations.  So you just need to continue the calculation.  You copy the CONTCAR files to POSCAR and restart vasp.  You might use one of our scripts: "vfin.pl dir" , which will move the calculation to dir and have the main directory set for a new calculation.

Then, once your LOW calculation is converged, then you can go to MIDDLE.  Since LOW will be closer to the minimum energy path, MIDDLE should converge faster.  But again, if it does not in 200 iterations, start it again until it does.  Then you can move on to HIGH.  Of course, you can also increase NSW, but the point is that you can't demand that the calculation converge in a fixed number of iterations; instead you need to check that the calculation is reasonable and converging and then continue them until they do converge.

---

**graeme** (2022-07-28 18:20):

No, it really depends upon the path, and in particularly how linear it is or how close your initial path is.  I have seen calculations of hundreds of paths and some range of simple one which converge in a few iterations with one image, and ones that require 10-00 images and many more iterations with a careful optimizer to converge.  A lot depends upon the ratio of soft to stiff modes, i.e. the stiffness of the problem.  But anyway, the bottom line is that you have to check for convergence - you can just run a fixed number of iterations and conclude that things are not working if you don't get to a force that you are looking for.

## The graded AI answer (SaddleAgent (with Opus 4.8))

**Bottom line: your most likely problem isn't the optimizer, the image translation, or the frozen atom — it's the electronics.** Ti₇₃O₁₄₃ is a *reduced* anatase cell (perfect 3×3×2 = Ti₇₂O₁₄₄; you have +1 Ti, −1 O), so it carries excess electrons that localize as Ti³⁺ polarons. If you're running without spin polarization + Hubbard U + a consistent `MAGMOM`, different NEB images settle onto *different* electronic/magnetic minima, and the band can never converge no matter what `IOPT` you pick or which atom you freeze. That fully explains why every "convergence speed-up" you tried failed. I need your files to confirm, but let me answer your three questions first, then tell you exactly what to send.

**1. "Is image translation happening?" — you're checking it the wrong way.** Translation of the band is not something you see by eyeballing the images for motion. The tell is in the *energies and forces*: when a fully periodic cell with no anchored atom drifts, the whole band rigid-translates by a lattice vector, inter-image spacing collapses, **and every image's final energy collapses to nearly the same value (the barrier disappears)**, while forces *oscillate* instead of dropping. Check it with one line:

```
grep E0 0[0-9]/OSZICAR | tail
```

across your image directories (`01/`…`0N/`). If the image energies are spreading into a sensible profile with a hump, you do *not* have a translation problem. If they're all sliding toward one value and forces won't settle, you do. "Nothing seems to be happening" when you look at the images doesn't distinguish these — send me the per-image energy/force trend (`nebef.pl` output) and I'll tell you definitively.

**2. Freezing one atom in a bulk cell — yes, it's appropriate, and it's the *correct* fix, but for a different reason than in a slab.** The distinction Henkelman draws:

- In a **slab**, the frozen bottom layers already anchor the cell, so you don't need a separate pin.

- In a **fully periodic bulk cell** there is nothing pinning the lattice, so it carries a near-zero-curvature rigid-body translational mode the saddle optimizer cannot damp. Freezing **exactly one atom** removes that single zero mode. This is purely a *numerical* anchor — so:

  - Freeze **one** atom only — pick one far from the migrating Ti (a corner Ti or O that barely moves). **Do not** freeze the host lattice broadly: for a bulk hop, the lattice relaxation *around* the migrating Ti is part of the MEP and the barrier — freezing it out is a bad approximation, not a safe speed-up.

  - Put that atom at the **same fractional coordinate (`F F F`) in every interior image** — an endpoint-only freeze leaves the interior images free to drift and does nothing. This is the most common reason "I tried freezing an atom and it still failed."

  - Keep the cell fixed: **`ISIF=2`**.

If your freeze was endpoint-only, or you froze a large region, that's likely why it didn't help.

**3. Center vs. near-surface vacancy — there is no surface.** A true bulk 3×3×2 anatase supercell is periodic in all three directions: it has no surface, no center, no edge. Wherever you "draw" the vacancy in the box, the structure is identical up to a translation — the physics is exactly the same. (You'd only get a real center-vs-surface difference if you had built a **slab** with a vacuum gap, which from your description you did not.) What *does* matter is the **supercell size**: the vacancy and the interstitial Ti each interact with their own periodic images, so the only placement question worth asking is whether the cell is large enough that those self-images don't overlap — not where inside the box the defect sits.

**What I think is actually going on (ranked), and what I need to see**

You said you attached files, but **nothing came through on my end** — I have no INCAR, OSZICAR, OUTCAR, or POSCAR to grep. So the following is from the system description; send the files and I'll confirm in one pass.

1.

**Electronic-state inconsistency across images (my top suspicion for reduced TiO₂).** Excess electrons from the O vacancy + Ti interstitial localize as Ti³⁺ polarons. Without `ISPIN=2`, a Hubbard `U` on Ti-d, and an explicit consistent `MAGMOM`, VASP starts each image from a huge default moment and relaxes images into *different* magnetic minima → one image's force stuck far above its neighbors → the band never converges, independent of optimizer or frozen atom. Two greps decide it:

```
grep 'aborting loop' 0[0-9]/OUTCAR      # any "EDIFF was not reached (unconverged)" = wrong forces
grep magnetization 0[0-9]/OUTCAR        # one image off the smooth IS→FS trend = split electronic states
```

Fix: `ISPIN=2`, `LDAU`/`LDAUU` on Ti-d (DFT+U is standard for reduced TiO₂), `LMAXMIX=4`, and an explicit `MAGMOM` interpolated from your relaxed endpoints' moments — not the default.

2.

**The translational drift / freeze-done-wrong** from Q1–Q2 above — confirmed by the `E0`-collapse check.

3.

**You may simply be hitting NSW / walltime.** A 216-atom band needs hundreds–thousands of ionic steps. "Failed to converge" often means "stopped at NSW," not "diverged." Check:

```
grep 'reached required accuracy' 0[0-9]/OUTCAR   # absent = NSW/walltime stopped it, not failure
```

If the force *trend* over the last steps is still descending, just continue from `CONTCAR`s with more steps.

**Please send:** the band `INCAR`, your two endpoint `INCAR`s, `KPOINTS`, the endpoint + image `POSCAR`s (so I can check the freeze mask, cell consistency, and atom ordering), the per-image OSZICARs or `nebef.pl`/`neb.dat` output, and the tail of a couple of image `OUTCAR`s. Also confirm your VASP and VTST versions (`grep 'vasp.[56]' OUTCAR` and `grep 'VTST' OUTCAR`) — I don't trust a version-specific fix until I see the build.

My confidence: ~70% the root cause is electronic (point 1) given this is reduced TiO₂; the frozen-atom/translation issue is real but secondary. The files will settle it quickly.
