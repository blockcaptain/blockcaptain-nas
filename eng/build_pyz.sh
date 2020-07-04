#!/bin/bash
set -ex

DEST_DIR="build/pyz"
rm -rf "${DEST_DIR}"
mkdir -p "${DEST_DIR}"
pip install -r requirements.txt --no-deps . --target "${DEST_DIR}"
tar -cv --exclude="__pycache__" --exclude=".vscode" --exclude-from=".gitignore" \
    -f ${DEST_DIR}/paranoidnas/media/media_content.tar \
    -C ${DEST_DIR}/paranoidnas/media/media_content .
rm -rf ${DEST_DIR}/paranoidnas/media/media_content
python3 -m zipapp -c -m "paranoidnas.media.__main__:main" -p "/usr/bin/env python3" -o build/builder.pyz $DEST_DIR 
chmod +x build/builder.pyz
