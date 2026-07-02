# Question — forum topic 16196

*Poor convergence near shallow energy minima*

**jordanchapman** (user, 2025-11-13 12:41):

Hi all,

I'm interested in calculating the energy barriers of defect formation processes in LiF. While doing these calcs, I'm consistently running into convergence issues. My thinking is that the convergence is sketchy because the energies of the defect geometries I'm using as endpoints are only different on the order of ~0.01 eV. When I run the NEB calcs, I'm finding that the endpoint will not lie at a local energy minimum, for instance, or that there are lower-energy configurations along the MEP that I calculate. 

I've been using the LFBGS optimizer for many of these NEB calcs without issue, especially when the energy differences between the initial and final configurations are >1eV. So, I attempted using the first-order QM optimizer around these shallow energy minima to try to improve the convergence. I'm finding that the convergence is similarly poor using the QM opt, only taking longer than LFBGS. 

I'm wondering if this poor convergence is possibly related to one of several INCAR tags. I've been using the default 0.1 TIMESTEP value, but I worry that dropping the TIMESTEP value wouldn't improve convergence, it would only further increase the calculation time (the early steps of the NEB calcs don't show any high energy barrier). I'm also considering the sensitivity of these calcs to the number of images and the ionic relaxation criteria. I've been using -0.01 eV/A; is it possible that more stringent convergence criteria of the endpoints and along the MEP could resolve some of the issues?

I've attached my OUTCAR, POSCAR, intermediate CONTCAR, and INCAR files for reference. Any advice on resolving this issue is greatly appreciated!

Jordan Chapman

---

**jordanchapman** (user, 2025-11-18 11:18):

This is indeed the case. I started these calculations using only GGA, which showed a PE surface without shallow, nearby minima. I don't think you need to look into these NEB calcs any further, but I do have some general questions:

1. Do you expect that these shallow energy minima I'm finding with hybrid functional calcs are physical results, or are these shallow energy minima artefacts of an HSE-level calc? I'm unfamiliar with the problem you're describing where the shallow energy minima are related to exact exchange.

2. Do you recommend using pure DFT to identify ionic geometries that should be used as endpoints in an NEB calc? Or can you comment on the suitability of hybrid functionals in NEB calcs? For instance, when running a previous NEB calc (converged at PBE level) with HSE-level theory, I similarly find additional energy minima between the transition state and a shallow energy minimum.

3. If these shallow energy minima are physically relevant results, is there a way I can probe the MEPs separating similar ionic geometries without a fully converged NEB calculation. I.e., can I run an NEB calc with loose convergence criteria to get an idea of the atomic motions associated with small transition state?
