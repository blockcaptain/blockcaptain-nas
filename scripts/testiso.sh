#!/bin/bash

./pnasmedia.pyz \
    -u testadm \
    -h testnas \
    -b efi \
    -s "$(cat ${HOME}/.ssh/id_rsa.pub)"
