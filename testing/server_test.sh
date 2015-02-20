#!/bin/bash

USER=peter.claydon@continuumbridge.com
PASSWORD=dev14
cp testthisbridge.sh /opt/cbridge/thisbridge/thisbridge.sh
cd /opt/cbridge/thisbridge
~/bridge_admin/testing/cb --bridge post --user $USER --password $PASSWORD
~/bridge_admin/testing/cb --bridge get --user $USER --password $PASSWORD
~/bridge_admin/testing/cb --bridge patch --name NewName --user $USER --password $PASSWORD
~/bridge_admin/testing/cb --bridge get  --user $USER --password $PASSWORD
#
cd ~/apps_dev/adaptor_test_app
git pull
~/bridge_admin/testing/cb --app post config.json --user $USER --password $PASSWORD
~/bridge_admin/testing/cb --app get config.json --user $USER --password $PASSWORD
~/bridge_admin/testing/cb --app patch config.json --user $USER --password $PASSWORD
~/bridge_admin/testing/cb --app get config.json --user $USER --password $PASSWORD
~/bridge_admin/testing/cb --app delete config.json --user $USER --password $PASSWORD
#
cd ~/adaptors_dev/test_adaptor
git pull
~/bridge_admin/testing/cb --device post config.json --user $USER --password $PASSWORD
~/bridge_admin/testing/cb --device get config.json --user $USER --password $PASSWORD
~/bridge_admin/testing/cb --device patch config.json --user $USER --password $PASSWORD
~/bridge_admin/testing/cb --device get config.json --user $USER --password $PASSWORD
~/bridge_admin/testing/cb --device delete config.json --user $USER --password $PASSWORD
#
cd ~/bridge_admin/testing
cp testthisbridge.sh /opt/cbridge/thisbridge/thisbridge.sh
USER=bridges@continuumbridge.com
PASSWORD=Mucht00f@r
cd /opt/cbridge/thisbridge
cp testthisbridge.sh thisbridge.sh
~/bridge_admin/testing/cb --bridge post --user $USER --password $PASSWORD
~/bridge_admin/testing/cb --bridge get --user $USER --password $PASSWORD
~/bridge_admin/testing/cb --bridge patch --name NewName --user $USER --password $PASSWORD
~/bridge_admin/testing/cb --bridge get  --user $USER --password $PASSWORD
#
cd ~/apps_dev/adaptor_test_app
git pull
~/bridge_admin/testing/cb --app post config.json --user $USER --password $PASSWORD
~/bridge_admin/testing/cb --app get config.json --user $USER --password $PASSWORD
~/bridge_admin/testing/cb --app patch config.json --user $USER --password $PASSWORD
~/bridge_admin/testing/cb --app get config.json --user $USER --password $PASSWORD
~/bridge_admin/testing/cb --app delete config.json --user $USER --password $PASSWORD
#
cd ~/adaptors_dev/test_adaptor
git pull
~/bridge_admin/testing/cb --device post config.json --user $USER --password $PASSWORD
~/bridge_admin/testing/cb --device get config.json --user $USER --password $PASSWORD
~/bridge_admin/testing/cb --device patch config.json --user $USER --password $PASSWORD
~/bridge_admin/testing/cb --device get config.json --user $USER --password $PASSWORD
~/bridge_admin/testing/cb --device delete config.json --user $USER --password $PASSWORD
