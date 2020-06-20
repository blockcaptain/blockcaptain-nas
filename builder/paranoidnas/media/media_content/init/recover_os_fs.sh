#!/bin/bash
set -ex

mount "$1" /mnt/backup_fs
LATEST_HOME=$(ls -1 -r /mnt/backup_fs/home_snapshots | head -n 1)
LATEST_USR=$(ls -1 -r /mnt/backup_fs/usr_local_snapshots | head -n 1)
LATEST_VAR=$(ls -1 -r /mnt/backup_fs/var_local_snapshots | head -n 1)
LATEST_ETC=$(ls -1 -r /mnt/backup_fs/etc_snapshots | head -n 1)

echo Destroying all data on OS user subvols...
read -p "Are you sure? " -n 1 -r
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

cd /

btrfs subvol delete /mnt/os_fs/root_subvol/home
btrfs subvol delete /mnt/os_fs/root_subvol/usr/local
btrfs subvol delete /mnt/os_fs/root_subvol/var/local
btrfs subvol delete /mnt/os_fs/root_subvol/etc

btrfs send /mnt/backup_fs/home_snapshots/$LATEST_HOME | btrfs receive /mnt/os_fs
mv /mnt/os_fs/$LATEST_HOME /mnt/os_fs/home

btrfs send /mnt/backup_fs/usr_local_snapshots/$LATEST_USR | btrfs receive /mnt/os_fs
mv /mnt/os_fs/$LATEST_USR /mnt/os_fs/usr/local

btrfs send /mnt/backup_fs/var_local_snapshots/$LATEST_VAR | btrfs receive /mnt/os_fs
mv /mnt/os_fs/$LATEST_VAR /mnt/os_fs/var/local

btrfs send /mnt/backup_fs/etc_snapshots/$LATEST_ETC | btrfs receive /mnt/os_fs
mv /mnt/os_fs/$LATEST_ETC /mnt/os_fs/etc

btrfs property set -ts /mnt/os_fs/home ro false
btrfs property set -ts /mnt/os_fs/usr/local ro false
btrfs property set -ts /mnt/os_fs/var/local ro false
btrfs property set -ts /mnt/os_fs/etc ro false

# how to reenable btrfs-sxbackup while keeping old backups??