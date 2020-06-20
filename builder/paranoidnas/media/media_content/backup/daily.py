#!/usr/bin/python3
from paranoidnas import get_deadman
from sh import btrfs_sxbackup
from typing import List


def backup_subvol(source_container_path: str) -> None:
    try:
        btrfs_sxbackup("run", path)
    except:
        # log it
        pass


def backup_group(group_name: str, source_container_paths: List[str]) -> None:
    try:
        with get_deadman(group_name):
            for path in source_container_paths:
                backup_subvol(path)
    except:
        # log it
        pass


backup_group("local_os_backup", ["/mnt/data_fs/main_snapshots", "/mnt/data_fs/archive_snapshots"])

backup_group(
    "local_data_backup",
    [
        "/mnt/os_fs/home_snapshots",
        "/mnt/os_fs/usr_local_snapshots",
        "/mnt/os_fs/var_local_snapshots",
        "/mnt/os_fs/etc_snapshots",
    ],
)

# test

