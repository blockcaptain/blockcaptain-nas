#!/bin/bash
set -ex

if [[ $# -eq 3 ]]; then
    RAID_MODE=raid1c3
elif [[ $# -eq 2 ]]; then
    RAID_MODE=raid1
else
    echo Need 2 or 3 devs.
    exit 1
fi

echo Destroying all data on $@...
read -p "Are you sure? " -n 1 -r
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

mkfs.btrfs -f -d $RAID_MODE -m $RAID_MODE -L data_fs "$@"

eval "$(blkid -o export "$1" | grep UUID=)"
echo "/dev/disk/by-uuid/$UUID /mnt/data_fs btrfs defaults,noatime 0 0" >> /etc/fstab
mount /mnt/data_fs

btrfs subvolume create /mnt/data_fs/main_subvol
btrfs subvolume create /mnt/data_fs/archive_subvol
btrfs subvolume create /mnt/data_fs/main_snapshots
btrfs subvolume create /mnt/data_fs/archive_snapshots

echo "/mnt/data_fs/main_subvol /srv/main none bind 0 0" >> /etc/fstab
echo "/mnt/data_fs/archive_subvol /srv/archive none bind 0 0" >> /etc/fstab
mount /srv/main
mount /srv/archive