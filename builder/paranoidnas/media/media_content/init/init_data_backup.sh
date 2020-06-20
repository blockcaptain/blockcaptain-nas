#!/bin/bash
set -ex

SRC_RETENTION="2d:1/d,1w:1/w,1m:none"
DEST_RETENTION="2d:1/d,1w:1/w,1m:1/m,4m:none"

btrfs-sxbackup init -sc ../main_snapshots -sr "$SRC_RETENTION" -dr "$DEST_RETENTION" /mnt/data_fs/main_subvol /mnt/backup_fs/main_snapshots
btrfs-sxbackup init -sc ../archive_snapshots -sr "$SRC_RETENTION" -dr "$DEST_RETENTION" /mnt/data_fs/archive_subvol /mnt/backup_fs/archive_snapshots
