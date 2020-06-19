#!/bin/bash
set -ex

EFI_DEV=$(awk '$2 == "/target/boot/efi" { print $1 }' /proc/mounts)
ROOT_DEV=$(awk '$2 ~ "^/target$" { print $1 }' /proc/mounts)
ROOT_UUID=$(blkid -o value $ROOT_DEV | head -n 1)

awk '$2 ~ "^/target/" { print $2 }' /proc/mounts | xargs umount
btrfs subvolume snapshot /target /target/rootfs
mkdir /mnt/rootfs
mount -o subvol=rootfs $ROOT_DEV /mnt/rootfs
mount $EFI_DEV /mnt/rootfs/boot/efi
mount -o bind /dev  /mnt/rootfs/dev
mount -o bind /sys  /mnt/rootfs/sys
mount -o bind /proc /mnt/rootfs/proc
sed -i "/$ROOT_UUID/s/defaults/defaults,noatime,subvol=rootfs/" /mnt/rootfs/etc/fstab
chroot /mnt/rootfs update-grub
chroot /mnt/rootfs grub-install --efi-directory=/boot/efi
find /target -mindepth 1 -maxdepth 1 -not -name rootfs -exec rm -rf '{}' \;

btrfs subvolume create /target/home
btrfs subvolume create /target/usr_local
btrfs subvolume create /target/var_local
echo "/dev/disk/by-uuid/$ROOT_UUID /home btrfs defaults,noatime,subvol=home 0 0" >> /mnt/rootfs/etc/fstab
echo "/dev/disk/by-uuid/$ROOT_UUID /usr/local btrfs defaults,noatime,subvol=usr_local 0 0" >> /mnt/rootfs/etc/fstab
echo "/dev/disk/by-uuid/$ROOT_UUID /var/local btrfs defaults,noatime,subvol=var_local 0 0" >> /mnt/rootfs/etc/fstab
cp -a /target/rootfs/usr/local/. /target/usr_local
cp -a /target/rootfs/var/local/. /target/var_local
find /target/rootfs/usr/local -mindepth 1 -maxdepth 1 -exec rm -rf '{}' \;
find /target/rootfs/var/local -mindepth 1 -maxdepth 1 -exec rm -rf '{}' \;