#!/bin/bash

./build/pnasmedia.pyz build \
    -u testadm \
    -h testnas \
    -b efi \
    --no-prompt \
    -a "$(cat ${HOME}/.ssh/id_rsa.pub)"
