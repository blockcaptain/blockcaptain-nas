#!/bin/bash

TARGET_HOSTNAME=$1

# Setup hostname. Autoinstall clobbers the users cloud-init if an identity section
# is provided. So we need to do this manually.
cat > /target/root_subvol/etc/hosts << EOF
127.0.0.1 localhost
127.0.1.1 ${TARGET_HOSTNAME}
::1     ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
EOF

cat > /target/root_subvol/etc/hostname << EOF
${TARGET_HOSTNAME}
EOF

# Restrict default home directory permissions.
echo "HOME_MODE   0700" >> /target/root_subvol/etc/login.defs