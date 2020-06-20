#!/usr/bin/python3
from paranoidnas import get_deadman
from sh import btrfs
from typing import List


def scrub_fs(filesystem: str) -> None:
    try:
        btrfs('scrub', 'start', '-BdR', filesystem)
    except:
        # log it
        pass



scrub_fs('/mnt/backup_fs')
scrub_fs('/mnt/data_fs')
scrub_fs('/mnt/os_fs')

#test