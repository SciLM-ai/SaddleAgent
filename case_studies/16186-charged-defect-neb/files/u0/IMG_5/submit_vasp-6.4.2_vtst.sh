#! /bin/bash
#
#SBATCH -t 10:00:00
#SBATCH --job-name=LiF_NEB_GPU
#SBATCH --partition=v100_normal_q
#SBATCH --nodes=5
#SBATCH --gres=gpu:1
#SBATCH --ntasks-per-node=1
### SBATCH --gres-flags=enforce-binding
### SBATCH --cpus-per-task=8
#SBATCH --account=vtqm
### SBATCH --ntasks=5
#
module reset
module load OpenMPI/5.0.3-NVHPC-24.9-CUDA-12.6.0 imkl/2024.2.0
LD_LIBRARY_PATH=/apps/arch/software/NVHPC/24.9-CUDA-12.6.0/Linux_x86_64/24.9/compilers/extras/qd/lib:$LD_LIBRARY_PATH
export PATH=$PATH:/home/jordanchapman/vasp.6.4.2_vtst/bin
#
echo "VASP_TINKERCLIFFS ROME: Normal beginning of execution."
#
# which vasp_std
# log gpu usage
nvidia-smi --query-gpu=timestamp,name,pci.bus_id,driver_version,temperature.gpu,utilization.gpu,utilization.memory,memory.total,memory.free,memory.used --format=csv -l 3 > $SLURM_JOBID.gpu.log & 
#
mpirun /home/jordanchapman/vasp.6.4.2_vtst/bin/vasp_std
#
if [ $? -ne 0 ]; then
  echo "VASP_TINKERCLIFFS ROME: Run error!"
  exit 1
fi
#
echo "VASP_TINKERCLIFFS ROME: Normal end of execution."
exit 0
