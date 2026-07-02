# Question — forum topic 16186

*NEB with charged defect using vtstcode-205*

**jordanchapman** (user, 2025-06-06 12:39):

Hi all,

I'm attempting to find an energy barrier for the migration of an anionic vacancy in LiF. I've been able to run calculations with a neutral defect (i.e., the number of electrons matches the expected number from the POSCAR + POTCAR files), but I'm running into an issue when performing a similar calc with one fewer electron. Specifically, the electronic optimization initializes until NELM=5, when I get the following message from VASP:

BRMIX: very serious problems

 the old and the new charge density differ

 old charge density:  1073.00000 new 1072.00000

The end points were both geometry-relaxed with the following INCAR tags:

! initialization

System = LiF

ISTART = 1       

ICHARG = 2

NCORE = 8

ISPIN = 2

NELM = 200

ENCUT = 400

PREC = Accurate

ISMEAR = 0; SIGMA = 0.01

EDIFF = 1E-10

! ionic relaxation

NELECT = 1072 ! 1073 neutral

IBRION = 3

NSW = 500

POTIM = 0.1

ISIF = 0

IOPT = 1

EDIFFG = -0.010

And the NEB routine I'm trying to run uses the following INCAR tags:

! initialization

System = LiF

ISTART = 0       

ICHARG = 2

NCORE = 8

ISPIN = 2

NELM = 20

ENCUT = 400

PREC = Accurate

ISMEAR = 0; SIGMA = 0.01

EDIFF = 1E-10

ALGO = Normal

! ionic relaxation

NELECT = 1072 ! 1073 neutral

IBRION = 3

NSW = 500

POTIM = 0

ISIF = 0

IOPT = 1

EDIFFG = -0.010

! NEB

ICHAIN = 0

IMAGES = 5

SPRING = -5.0

LCLIMB = .FALSE.

I'm a bit perplexed by this error message. The endpoints were run with the same number of electrons, and converged to the above specs; I verified in the INCAR that there were 1072 electrons in the final electronic configuration. I tried running the NEB calc with ICHARG=0 + ISTART=0, but ran into the same error. I also tried changing the ALGO to Fast and VeryFast. If anyone could provide any insight as to why VASP isn't reading NELECT from the NEB INCAR file (or if there's an oversight I'm not seeing), I would greatly appreciate it.

Jordan Chapman

VTNSI

---

**jordanchapman** (user, 2025-06-06 14:24):

Thanks for getting back to me quickly. I've attached a zip file containing the parent directory for the NEB calcs. 

To your reply, the WAVECAR and CHGCAR files weren't generated at any point in the runs for the intermediate geometries. I included the OUTCAR files of the endpoints, too. I've linked the VTST source code with version 6.4.2 of VASP, FYI.
