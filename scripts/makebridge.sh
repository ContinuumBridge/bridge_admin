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
cd ~/
tar cfz bridge_clone.tar.gz bridge_clone
md5sum bridge_clone.tar.gz > bridge_clone.md5 
echo 'Full release: bridge_clone.tar.gz'
#
cd bridge_clone
rm -rf node_modules
cd ~/
tar cfz bridge_clone_inc.tar.gz bridge_clone
md5sum bridge_clone_inc.tar.gz > bridge_clone_inc.md5 
echo 'Incremental release: bridge_clone_inc.tar.gz'
