#!/bin/sh

echo 'Copying source code...'
cp -f ./gui.py ./dist/win32/dat/gui.py
echo 'Entering dist directory...'
cd dist/

echo 'Populating IP file with' $1
echo -n $1 > win32/dat/ip
echo 'Zipping to win32.zip'
zip -r win32.zip win32 > /dev/null
echo 'Done!\n'
echo 'Leaving dist directory...'
cd ..
