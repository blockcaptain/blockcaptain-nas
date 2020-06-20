#!/bin/bash
set -ex

useradd -m -s /bin/bash -u 2002 cloudpusher
chmod 700 /home/*

export PATH=$HOME/.local/bin:$PATH
export PIPX_HOME=/usr/share/pipx/venvs
export PIPX_BIN_DIR=/usr/bin
pip3 install --user pipx

PKG=$(curl https://api.github.com/repos/wpbrown/btrfs-sxbackup/releases/latest | jq -r '.assets[].browser_download_url' | grep .whl)
pipx install "$PKG"