#!/bin/bash

export ENV_HOME="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export PATH=${ENV_HOME}/conda/bin:$PATH

export HDF5_USE_FILE_LOCKING=FALSE

eval "$(${ENV_HOME}/conda/bin/conda shell.bash hook)"
conda activate default


export PYTHONPATH=$(pwd)

#MODULES_HOME=/mnt/appsource/modules/current/
#source ${MODULES_HOME}/init/bash
#module load slurm

