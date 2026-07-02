# Expert answer (ground truth) — forum topic 16198

The real answer from the Henkelman Group forum expert.

**graeme** (expert, 2025-12-09 12:18):

There are two problems with the calculation.  First, you have a fairly long path.  Most of the path involves CO2 moving away from the surface.  With only 4 images, only 1 is really involved in the reaction step.

Second, for CO2, you will need a smaller timestep.  This is because CO2 has high frequency modes.  In your endpoints you used CG, which is why they converged.  Note, you can used the default CG from vasp with NEB.

In the attached I used 8 images and a time step of 0.05 with quickmin (IOPT=3) and the convergence is smooth.  I didn't quite finish it because I wanted to write back, but if you do continue it will converge.  That said, notice that there is a lower initial state.  Putting it another way, the CO would prefer to first hop along the surface and then combine with O to form CO2.  If you do a similar band, I recommend minimizing image 02 to get a new (lower energy) initial state.
