#!/bin/bash
set -ex

if [[ $# -eq 2 ]]; then
    DATA_MODE=raid1
    META_MODE=raid1
elif [[ $# -eq 1 ]]; then
    DATA_MODE=single
    META_MODE=dup
else
    echo Need 1 or 2 devs.
    exit 1
fi

echo Destroying all data on $@...
read -p "Are you sure? " -n 1 -r
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

mkfs.btrfs -f -d $DATA_MODE -m $META_MODE -L backup_fs "$@"

eval "$(blkid -o export "$1" | grep UUID=)"
echo "/dev/disk/by-uuid/$UUID /mnt/backup_fs btrfs defaults,noatime 0 0" >> /etc/fstab
mount /mnt/backup_fs

btrfs subvolume create /mnt/backup_fs/home_snapshots
btrfs subvolume create /mnt/backup_fs/root_snapshots
btrfs subvolume create /mnt/backup_fs/usr_local_snapshots
btrfs subvolume create /mnt/backup_fs/var_local_snapshots
btrfs subvolume create /mnt/backup_fs/etc_snapshots
btrfs subvolume create /mnt/backup_fs/main_snapshots
btrfs subvolume create /mnt/backup_fs/archive_snapshots