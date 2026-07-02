#!/bin/sh
#PBS -V
#PBS -N NEB
#PBS -q normal
#PBS -A vasp
#PBS -l select=1:ncpus=68:mpiprocs=64:ompthreads=1
#PBS -l walltime=48:00:00

cd $PBS_O_WORKDIR

module purge
module load craype-mic-knl intel/19.1.2 impi/19.1.2


mpirun /home01/e1571a03/vasp.5.4.4/bin/vasp_std > stdout.txt

