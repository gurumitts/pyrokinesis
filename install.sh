#!/bin/sh

PYRO_HOME=/opt/pyrokinesis
PYRO_BIN=${PYRO_HOME}/bin
PYRO_LOGS_DIR=/var/log/pyro

if [ -d ${PYRO_HOME} ]; then
    cd ${PYRO_HOME}
    git pull
else
    cd /opt
    git clone https://github.com/gurumitts/pyrokinesis.git
    cd ${PYRO_HOME}
    git pull
fi

if [ ! -d ${PYRO_LOGS_DIR} ]; then
    mkdir ${PYRO_LOGS_DIR}
fi

cp -f ${PYRO_BIN}/pyro /etc/init.d/

update-rc.d pyro defaults



