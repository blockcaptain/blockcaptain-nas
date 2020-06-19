from doit.tools import run_once, LongRunning, Interactive
from doit.exceptions import TaskFailed
from doit import get_initial_workdir
from pathlib import Path
import hashlib
import itertools
import re


DOIT_CONFIG = {'default_tasks': ['create_paranoid_iso']}

ubuntu_iso_filename = 'ubuntu-20.04-live-server-amd64.iso'
source_path = Path(get_initial_workdir())
paranoid_source = source_path / 'paranoid'
paranoid_files = [x for x in paranoid_source.rglob('*') if paranoid_source.is_file()]

def task_download_ubuntu_iso():
    """Download the Ubuntu Server ISO."""

    return {
        'actions': [
            Interactive(['wget', '--progress=bar:force', f'https://releases.ubuntu.com/20.04/{ubuntu_iso_filename}'], shell=False)
        ],
        'targets': [ubuntu_iso_filename],
        'uptodate': [True]
    }


def task_extract_ubuntu_iso():
    """Extract the ISO."""

    return {
        'actions': [['7z', '-y', '-oiso', 'x', ubuntu_iso_filename]],
        'targets': ['iso/README.diskdefines'],
        'file_dep': [ubuntu_iso_filename]
    }


def task_add_nocloud_datasource():
    """Injects the cloud-init nocloud data source."""



    return {
        'actions': [
            ['mkdir', '-p', 'iso/nocloud'],
            ['cp', source_path / 'user-data', 'iso/nocloud/user-data'],
            ['touch', 'iso/nocloud/meta-data'],
        ],
        'targets': ['iso/nocloud/user-data'],
        'file_dep': [source_path / 'user-data', 'iso/README.diskdefines']
    }


def task_add_paranoid_data():
    """Injects the Paranoid NAS installation files."""

    paranoid_source = source_path / 'paranoid'
    paranoid_files = [x for x in paranoid_source.rglob('*') if paranoid_source.is_file()]

    return {
        'actions': [
            ['mkdir', '-p', 'iso/paranoid'],
            ['cp', '-r', paranoid_source, 'iso']
        ],
        'targets': ['iso/paranoid/init_btrfs.sh'],
        'file_dep': [*paranoid_files, 'iso/README.diskdefines']
    }


def task_modify_grub_config():
    """Update grub for autoinstall."""

    grub_cfg_path = Path('iso/boot/grub/grub.cfg')
    stamp = '(ParanoidNAS Autoinstall)'

    def update():
        data = grub_cfg_path.read_text()
        data = re.sub('Install Ubuntu Server', f'\\g<0> {stamp}', data)
        data = re.sub(r'/vmlinuz\s+quiet', r'\g<0> autoinstall ds=nocloud\\;s=/cdrom/nocloud/ ', data)
        grub_cfg_path.write_text(data)

    return {
        'actions': [update],
        'file_dep': ['iso/README.diskdefines'],
        'targets': [grub_cfg_path],
        'uptodate': [f'grep "{stamp}" "{grub_cfg_path}"']
    }


def task_update_md5_list():
    """Update the md5sum list."""

    iso_dir = Path('iso')
    hash_file = Path('iso/md5sum.txt')
    hash_file_orig = hash_file.with_suffix('.orig')
    files_to_hash = {'./boot/grub/grub.cfg', './nocloud/user-data'}

    def update():
        with hash_file_orig.open() as f: 
            hashes = [rec for rec in (l.strip().split(maxsplit=1) for l in f.readlines()) if rec[1] not in files_to_hash]

        hashes += [[hashlib.md5((iso_dir / p).read_bytes()).hexdigest(), p] for p in files_to_hash]

        with hash_file.open('w') as f:
            f.writelines(" ".join(rec) + "\n" for rec in hashes)

    return {
        'actions': [
            ['cp', '-n', hash_file, hash_file_orig],
            update
        ],
        'targets': [hash_file, hash_file_orig],
        'file_dep': list(f.replace('./', 'iso/') for f in files_to_hash) + ['iso/paranoid/init_btrfs.sh'],
    }


def task_create_paranoid_iso():
    """Build the Paranoid NAS ISO."""

    return {
        'actions': [['xorriso', '-as', 'mkisofs', '-r', 
            '-V', 'Ubuntu custom amd64', 
            '-o', 'paranoidnas.iso', 
            '-J', '-l', '-b', 'isolinux/isolinux.bin', '-c', 'isolinux/boot.cat', '-no-emul-boot', 
            '-boot-load-size', '4', '-boot-info-table', 
            '-eltorito-alt-boot', '-e', 'boot/grub/efi.img', '-no-emul-boot', 
            '-isohybrid-gpt-basdat', '-isohybrid-apm-hfsplus', 
            '-isohybrid-mbr', '/usr/lib/ISOLINUX/isohdpfx.bin', 
            'iso/boot', 'iso']],
        'targets': ['paranoidnas.iso'],
        'file_dep': ['iso/md5sum.txt'],
        'uptodate': [run_once],
        'clean': True
    }


def task_init_test_vm():
    """Build a testing vm."""

    targets = [Path(f'test_vm/disk{i}.img') for i in range(4)]

    def ensure_non_existent():
        if any(p.exists() for p in targets):
            return TaskFailed('A test VM already exists. Manually clean with "clean init_test_vm" command before running this task.')

    return {
        'actions': [
            'mkdir -p test_vm',
            ensure_non_existent,
            'truncate -s 10G test_vm/disk0.img',
            'truncate -s 1G test_vm/disk1.img test_vm/disk2.img test_vm/disk3.img',
            LongRunning('''kvm -no-reboot -m 2048 -smp 2 --bios /usr/share/qemu/OVMF.fd \
               -drive file=test_vm/disk0.img,format=raw,cache=none,if=virtio \
               -drive file=test_vm/disk1.img,format=raw,cache=none,if=virtio \
               -drive file=test_vm/disk2.img,format=raw,cache=none,if=virtio \
               -drive file=test_vm/disk3.img,format=raw,cache=none,if=virtio \
               -drive file=paranoidnas.iso,format=raw,cache=none,if=virtio \
               -global isa-fdc.driveA= ''')
        ],
        'targets': targets,
        'file_dep': ['paranoidnas.iso'],
        'clean': True
    }


def task_run_test_vm():
    """Build a testing vm."""
    return {
        'actions': [
            LongRunning('''kvm -no-reboot -m 2048 -smp 2 --bios /usr/share/qemu/OVMF.fd \
               -drive file=test_vm/disk0.img,format=raw,cache=none,if=virtio \
               -drive file=test_vm/disk1.img,format=raw,cache=none,if=virtio \
               -drive file=test_vm/disk2.img,format=raw,cache=none,if=virtio \
               -drive file=test_vm/disk3.img,format=raw,cache=none,if=virtio \
               -global isa-fdc.driveA= \
               -net user,hostfwd=tcp::9022-:22,hostfwd=tcp::9999-:9999 -net nic''')
        ]
    }