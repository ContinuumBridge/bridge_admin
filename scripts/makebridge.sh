#!/bin/bash
cd ~/
rm -rf bridge_clone
rm bridge_clone.tgz
cp -r bridge bridge_clone
cd bridge_clone
rm -rf .git*
rm -rf */.git*
rm -rf lxc-scripts
cd ~/
tar cfz bridge_clone.tgz bridge_clone
echo 'bridge cloned as bridge_clone'
