#!/bin/bash
cd ~/
rm -rf bridge_clone
rm bridge_clone.tar
cp -r bridge bridge_clone
cd bridge_clone
rm -rf .git*
rm -rf */.git*
rm -rf lxc-scripts
cd ~/
tar cf bridge_clone.tar bridge_clone
echo 'bridge cloned as bridge_clone'
