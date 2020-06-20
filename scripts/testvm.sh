#!/bin/bash

vmStateDir=testvm
isoFile=paranoidNAS.iso
mkdir -p ${vmStateDir}

if [[ $1 == '-i' ]]; then
    mediaDrive="-cdrom ${isoFile}"
    rm -f ${vmStateDir}/diska.img
else
    mediaDrive=""
fi

for i in a b c d; do
    [[ ${i} -eq a ]] && size=10G || size=1G
    if [ ! -f ${vmStateDir}/disk${i}.img ]; then
        truncate -s ${size} ${vmStateDir}/disk${i}.img
    fi
done

kvm -no-reboot -m 2048 -smp 2 --bios /usr/share/qemu/OVMF.fd \
    -drive file=testvm/diska.img,format=raw,index=0,cache=none,if=virtio \
    -drive file=testvm/diskb.img,format=raw,index=1,cache=none,if=virtio \
    -drive file=testvm/diskc.img,format=raw,index=2,cache=none,if=virtio \
    -drive file=testvm/diskd.img,format=raw,index=3,cache=none,if=virtio \
    ${mediaDrive} \
    -global isa-fdc.driveA= 