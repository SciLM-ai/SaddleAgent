#!/bin/bash
#
#SBATCH --job-name=CuP
#SBATCH --output=jobname_%J_stdout.txt
#SBATCH --error=jobname_%J_stderr.txt
#SBATCH --partition=normal
#SBATCH -n 20
#SBATCH --ntasks-per-node=20
#SBATCH --exclusive   
#SBATCH --exclude=c160
#SBATCH --time=48:00:00      
#SBATCH --mail-user=chenjiao.bu-1@ou.edu
#SBATCH --mail-type=ALL


# debug: 30 min for maximum nodes=1 ntasks=20 ntasks-per-node=20
# normal: 48 hours as maximum request nodes=2/6 ntasks=20 ntasks-per-node=40/120
# huang: unlimited nodes=4 ntasks=96 ntasks-per-node=24
# large_mem：
# longjobs  --ntasks-per-node=20  
# by specifying "exclusive" and "ntasks-per-node"
# we request to use only those nodes with 20 cores per node 
# and we use those nodes exclusively.


# Add the path of your compiled VASP version
export PATH=$PATH:~/bin/vasp.6.4.1/bin
#export PATH=$PATH:~/.local/bin/ase

module purge
module load intel/2023a
module load HDF5/1.14.0-iimpi-2023a



# VASP_time
start_time=$(date +%s)
mpirun vasp_std > out.log
end_time=$(date +%s)
echo "单节点20核运行时间：$((end_time - start_time)) 秒" >> benchmark.log
echo "使用的VASP路径: $(which vasp_std)" >> benchmark.log



