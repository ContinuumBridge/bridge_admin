#!/bin/bash
cd ~/bridge/manager
git describe > cb_version
cd ~/
rm -rf bridge_clone
rm bridge_clone.tar.gz
rm bridge_clone_inc.tar.gz
cp -r bridge bridge_clone
cd bridge_clone
rm -rf .git*
rm -rf */.git*
rm -rf lxc-scripts
#rm */*_a.py
rm */*.pyc
#rm lib/cbcommslib.py
# Create checksum
cd ~/bridge/manager
find ../../bridge_clone -type f -print0 | sort -z | xargs -r0 md5sum | md5sum > md5
mv md5 ../../bridge_clone/md5
cd ~/
tar cfz bridge_clone.tar.gz bridge_clone
echo 'Full release: bridge_clone.tar.gz'
#
cd bridge_clone
rm md5
rm -rf node_modules
cd ~/
# Create checksum
cd ~/bridge/manager
find ../../bridge_clone -type f -print0 | sort -z | xargs -r0 md5sum | md5sum > md5
mv md5 ../../bridge_clone/md5
cd ~/
tar cfz bridge_clone_inc.tar.gz bridge_clone
echo 'Incremental release: bridge_clone_inc.tar.gz'
