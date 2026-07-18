#!/bin/bash
#SBATCH --nodes=3
#SBATCH --tasks-per-node=98
#SBATCH --cpus-per-task=1
#SBATCH --time=48:00:00
#SBATCH --output=out.%j.out
#SBATCH --error=err.%j.out

module load vasp/6.3.2_openMP 

srun vasp_std &> vasp_out
