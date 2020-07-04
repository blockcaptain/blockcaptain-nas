#!/bin/bash
set -ex

RETENTION="2d:1/d,1w:1/w,4w:none"

btrfs-sxbackup init -sc ../../home_snapshots -sr "$RETENTION" -dr "$RETENTION" /mnt/os_fs/root_subvol/home /mnt/backup_fs/home_snapshots
btrfs-sxbackup init -sc ../../../usr_local_snapshots -sr "$RETENTION" -dr "$RETENTION" /mnt/os_fs/root_subvol/usr/local /mnt/backup_fs/usr_local_snapshots
btrfs-sxbackup init -sc ../../../var_local_snapshots -sr "$RETENTION" -dr "$RETENTION" /mnt/os_fs/root_subvol/var/local /mnt/backup_fs/var_local_snapshots
btrfs-sxbackup init -sc ../../etc_snapshots -sr "$RETENTION" -dr "$RETENTION" /mnt/os_fs/root_subvol/etc /mnt/backup_fs/etc_snapshots