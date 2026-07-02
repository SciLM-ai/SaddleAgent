#!/bin/bash

# queue request
#$ -q all.q

# pe request
#$ -pe mpi_24 24

# Job name 
#$ -N Mpi_Job

#$ -S /bin/bash

#$ -V

#$ -cwd

# needs in 
#   $NSLOTS          
#       the number of tasks to be used
#   $TMPDIR/machines 
#       a valid machiche file to be passed to mpirun 
#   enables $TMPDIR/rsh to catch rsh calls if available

echo "Got $NSLOTS slots."
cat $TMPDIR/machines



#######################################################
### MPI JOB
#######################################################
#
#
 MPI_HOME=/opt/mpi/intel-14.0/openmpi-2.1.6
 MPI_EXEC=$MPI_HOME/bin/mpirun

 cd $SGE_O_WORKDIR

 $MPI_EXEC -machinefile $TMPDIR/machines -n $NSLOTS vasp_std > vasp.out
