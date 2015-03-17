#!/bin/bash
#
echo "Staff user"
USER=peter.claydon@continuumbridge.com
PASSWORD=dev14
cp testthisbridge.sh /opt/cbridge/thisbridge/thisbridge.sh
cd /opt/cbridge/thisbridge
echo "Posting bridge"
~/bridge_admin/testing/cb --bridge post --user $USER --password $PASSWORD
echo "Getting bridge"
~/bridge_admin/testing/cb --bridge get --user $USER --password $PASSWORD
echo "Patching bridge"
~/bridge_admin/testing/cb --bridge patch --name NewName --user $USER --password $PASSWORD
echo "Deleting bridge"
~/bridge_admin/testing/cb --bridge get  --user $USER --password $PASSWORD
#
cd ~/apps_dev/adaptor_test_app
git pull
echo "Posting app"
~/bridge_admin/testing/cb --app post config_staging.json --user $USER --password $PASSWORD
echo "Getting app"
~/bridge_admin/testing/cb --app get config_staging.json --user $USER --password $PASSWORD
echo "Patching app"
~/bridge_admin/testing/cb --app patch config_staging.json --user $USER --password $PASSWORD
echo "Getting app"
~/bridge_admin/testing/cb --app get config_staging.json --user $USER --password $PASSWORD
echo "Deleting app"
~/bridge_admin/testing/cb --app delete config_staging.json --user $USER --password $PASSWORD
#
cd ~/adaptors_dev/test_adaptor
git pull
echo "Posting device"
~/bridge_admin/testing/cb --device post config.json --user $USER --password $PASSWORD
echo "Getting device"
~/bridge_admin/testing/cb --device get config.json --user $USER --password $PASSWORD
echo "Patching device"
~/bridge_admin/testing/cb --device patch config.json --user $USER --password $PASSWORD
echo "Getting device"
~/bridge_admin/testing/cb --device get config.json --user $USER --password $PASSWORD
echo "Deleting device"
~/bridge_admin/testing/cb --device delete config.json --user $USER --password $PASSWORD
#
cd ~/bridge_admin/testing
cp testthisbridge.sh /opt/cbridge/thisbridge/thisbridge.sh

echo "bridge (non-staff) user"
USER=bridges@continuumbridge.com
PASSWORD=Mucht00f@r
cd /opt/cbridge/thisbridge
echo "Posting bridge"
~/bridge_admin/testing/cb --bridge post --user $USER --password $PASSWORD
echo "Getting bridge"
~/bridge_admin/testing/cb --bridge get --user $USER --password $PASSWORD
echo "Patching bridge"
~/bridge_admin/testing/cb --bridge patch --name NewName --user $USER --password $PASSWORD
echo "Deleting bridge"
~/bridge_admin/testing/cb --bridge get  --user $USER --password $PASSWORD
#
cd ~/apps_dev/adaptor_test_app
git pull
echo "Posting app"
~/bridge_admin/testing/cb --app post config_staging.json --user $USER --password $PASSWORD
echo "Getting app"
~/bridge_admin/testing/cb --app get config_staging.json --user $USER --password $PASSWORD
echo "Patching app"
~/bridge_admin/testing/cb --app patch config_staging.json --user $USER --password $PASSWORD
echo "Getting app"
~/bridge_admin/testing/cb --app get config_staging.json --user $USER --password $PASSWORD
echo "Deleting app"
~/bridge_admin/testing/cb --app delete config_staging.json --user $USER --password $PASSWORD
#
#cd ~/adaptors_dev/test_adaptor
#git pull
#echo "Posting device"
#~/bridge_admin/testing/cb --device post config.json --user $USER --password $PASSWORD
#echo "Getting device"
#~/bridge_admin/testing/cb --device get config.json --user $USER --password $PASSWORD
#echo "Patching device"
#~/bridge_admin/testing/cb --device patch config.json --user $USER --password $PASSWORD
#echo "Getting device"
#~/bridge_admin/testing/cb --device get config.json --user $USER --password $PASSWORD
#echo "Deleting device"
#~/bridge_admin/testing/cb --device delete config.json --user $USER --password $PASSWORD
#
