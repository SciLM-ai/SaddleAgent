# Question — forum topic 16189

*Negative transition state energies along reaction coordinates*

**jordanchapman** (user, 2025-06-30 15:33):

Hi all,

I'm trying to calculate the energy barrier associated with the dislocation of a F ion to an interstitial position in LiF. I've located what I think are two stable end points and generate intermediate images while keeping the atomic ordering in the POSCAR files consistent. When I do the NEB calculation, I find that VASP will calculate the intermediate configurations to have energies nearly 10 eV lower than either endpoint configuration, but was still able to locate an energy maximum along the band. 

I've doublechecked that the INCAR settings (in particular, the ENCUT and k-points mesh) are consistent for the endpoint and intermediate steps. I've also run geometry optimizations for both endpoints with symmetry turned off (ISYM = 0) to make sure that the endpoints aren't getting caught at high-symmetry points. The geometries of the POSCAR files also look to be reasonable, i.e., no close contacts between neighboring atoms.

Any input as to what could be causing this downward shift in the intermediate energies would be appreciated. I attached the POSCAR and OUTCAR files for the run.

Jordan

VT Postdoc
