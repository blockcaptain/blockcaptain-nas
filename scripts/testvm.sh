#!/bin/bash

vmStateDir=build/testvm
isoFile=build/paranoidNAS.iso
mkdir -p ${vmStateDir}

if [[ $1 == '-i' ]]; then
    mediaDrive="-cdrom ${isoFile}"
    rm -f ${vmStateDir}/diska.img
    ssh-keygen -f "${HOME}/.ssh/known_hosts" -R "[localhost]:9022"
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
    -drive file=${vmStateDir}/diska.img,format=raw,index=0,cache=none,if=virtio \
    -drive file=${vmStateDir}/diskb.img,format=raw,index=1,cache=none,if=virtio \
    -drive file=${vmStateDir}/diskc.img,format=raw,index=2,cache=none,if=virtio \
    -drive file=${vmStateDir}/diskd.img,format=raw,index=3,cache=none,if=virtio \
    ${mediaDrive} \
    -global isa-fdc.driveA= \
    -net user,hostfwd=tcp::9022-:22,hostfwd=tcp::9999-:9999 -net nic
