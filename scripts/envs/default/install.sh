#!/bin/bash

export SRC_HOME="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
#export BLD_HOME="$( cd "${SRC_HOME}/../../build/" && pwd )"
#export INSTALL_HOME="${BLD_HOME}/pyenv/"

#if [ -d "${INSTALL_HOME}" ]; then
#	echo "wrf-cmaq python env directory already present, bailing out (${INSTALL_HOME})"
#	exit 1;
#fi

#mkdir ${INSTALL_HOME}
#cd ${INSTALL_HOME}

#cp ${SRC_HOME}/activate.sh .

MCVER=Miniconda3-py313_26.7.1-1-Linux-x86_64.sh

#wget https://repo.anaconda.com/miniconda/Miniconda3-py39_4.9.2-Linux-x86_64.sh && \
curl "https://repo.anaconda.com/miniconda/${MCVER}" -o "${MCVER}"
sh "${MCVER}" -b -p $(pwd)/conda && \

export PATH=$(pwd)/conda/bin:$PATH
#./env/bin/conda install -y mamba -c conda-forge && \
#./env/bin/mamba env create --file conda_env.yaml && \

conda config --set channel_priority strict

#./env/bin/conda env create --file ${SRC_HOME}/conda_env.yaml
./conda/bin/conda env create --file conda_env.yaml

rm "${MCVER}"

