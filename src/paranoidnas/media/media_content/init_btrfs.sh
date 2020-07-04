#!/bin/bash
set -ex

EFI_DEV=$(awk '$2 == "/target/boot/efi" { print $1 }' /proc/mounts)
ROOT_DEV=$(awk '$2 ~ "^/target$" { print $1 }' /proc/mounts)
ROOT_UUID=$(blkid -o value $ROOT_DEV | head -n 1)

awk '$2 ~ "^/target/" { print $2 }' /proc/mounts | xargs umount
btrfs subvolume snapshot /target /target/root_subvol
mkdir /mnt/root_subvol
mount -o subvol=root_subvol $ROOT_DEV /mnt/root_subvol
mount -o bind /dev  /mnt/root_subvol/dev
mount -o bind /sys  /mnt/root_subvol/sys
mount -o bind /proc /mnt/root_subvol/proc
sed -i "/$ROOT_UUID/s/defaults/defaults,noatime,subvol=root_subvol/" /mnt/root_subvol/etc/fstab
if [[ -n $EFI_DEV ]]; then
    mount $EFI_DEV /mnt/root_subvol/boot/efi
    GRUB_INSTALL_ARG="--efi-directory=/boot/efi"
else
    GRUB_INSTALL_ARG="/dev/$(lsblk -no pkname $ROOT_DEV)"
fi
chroot /mnt/root_subvol update-grub
chroot /mnt/root_subvol grub-install $GRUB_INSTALL_ARG

find /target -mindepth 1 -maxdepth 1 -not -name root_subvol -exec rm -rf '{}' \;

rm -rf /target/root_subvol/home
btrfs subvolume create /target/root_subvol/home

btrfs subvolume create /target/usr_local
btrfs subvolume create /target/var_local
btrfs subvolume create /target/etc

cp -a /target/root_subvol/usr/local/. /target/usr_local
cp -a /target/root_subvol/var/local/. /target/var_local
cp -a /target/root_subvol/etc/. /target/etc

rm -rf /target/root_subvol/usr/local
rm -rf /target/root_subvol/var/local
rm -rf /target/root_subvol/etc

mv /target/usr_local /target/root_subvol/usr/local
mv /target/var_local /target/root_subvol/var/local
mv /target/etc /target/root_subvol/etc

mkdir /target/root_subvol/mnt/os_fs
echo "/dev/disk/by-uuid/$ROOT_UUID /mnt/os_fs btrfs defaults,noatime 0 0" >> /mnt/root_subvol/etc/fstab
mkdir /target/root_subvol/mnt/data_fs
mkdir /target/root_subvol/mnt/backup_fs

btrfs subvolume create /target/home_snapshots
btrfs subvolume create /target/root_snapshots
btrfs subvolume create /target/usr_local_snapshots
btrfs subvolume create /target/var_local_snapshots
btrfs subvolume create /target/etc_snapshots

btrfs subvolume create /target/scratch_subvol
chattr +C /target/scratch_subvol

mkdir -p /target/root_subvol/srv
mkdir /target/root_subvol/srv/main
mkdir /target/root_subvol/srv/archive
mkdir /target/root_subvol/srv/scratch
echo "/mnt/os_fs/scratch_subvol /srv/scratch none bind 0 0" >> /mnt/root_subvol/etc/fstab