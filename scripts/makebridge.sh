#!/bin/bash
cd ~/bridge/manager
git describe > cb_version
cd ~/
rm -rf bridge_clone
rm bridge_clone.tar.gz
cp -r bridge bridge_clone
cd bridge_clone
rm -rf .git*
rm -rf */.git*
rm -rf lxc-scripts
rm */*_a.py
cd ~/
tar cfz bridge_clone.tar.gz bridge_clone
echo 'bridge cloned as bridge_clone'
