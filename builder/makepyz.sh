#!/bin/bash
set -ex
DEST_DIR=build/pyz
mkdir -p $DEST_DIR
cp -r paranoidnas isomodder $DEST_DIR
tar -cv --exclude="__pycache__" --exclude=".vscode" -f $DEST_DIR/paranoidnas/media/media_content.tar -C $DEST_DIR/paranoidnas/media/media_content .
rm -rf $DEST_DIR/paranoidnas/media/media_content
python3 -m pip install -r requirements.txt --target $DEST_DIR
python3 -m zipapp -c -m "paranoidnas.media.__main__:main" -p "/usr/bin/env python3" -o build/builder.pyz $DEST_DIR 
chmod +x build/builder.pyz