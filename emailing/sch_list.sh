#!/bin/bash
#
# Used with the following line in /etc/crontab:
# 15 12   * * *   bridge  /home/bridge/bridge_admin/emailing/sch_list.sh >> /home/bridge/bridge_admin/emailing/sch_mail.log 2>&1
#
cd /home/bridge/bridge_admin/emailing
# Sirona
date
./sch_mail.py --user bridges@continuumbridge.com --password Mucht00f@r --key b9b0c3fea6308127164de1616cb97723 --bid BID36 --to "peter.claydon@continuumbridge.com, martin.sotheran@continuumbridge.com, martyn.price@sirona-cic.org.uk"
date
./sch_mail.py --user bridges@continuumbridge.com --password Mucht00f@r --key b9b0c3fea6308127164de1616cb97723 --bid BID45 --to "peter.claydon@continuumbridge.com, martin.sotheran@continuumbridge.com, Mandy.Miles@sirona-cic.org.uk"
date
./sch_mail.py --user bridges@continuumbridge.com --password Mucht00f@r --key c685297d8c0f710e3bd1c8e771eb8d3d --bid BID59 --to "peter.claydon@continuumbridge.com, martin.sotheran@continuumbridge.com"
#, richard.tarring@sirona-cic.org.uk" just whilst we make sure it's ok
# CBr
cd /home/bridge/bridge_admin/emailing/CBr_mailing
date
./CBr_mail.py --user bridges@continuumbridge.com --password Mucht00f@r --key c685297d8c0f710e3bd1c8e771eb8d3d --bid BID11 --to martin.sotheran@continuumbridge.com
date
./CBr_mailBW.py --user bridges@continuumbridge.com --password Mucht00f@r --key c685297d8c0f710e3bd1c8e771eb8d3d --bid BID12 --to "carson.bradbury@continuumbridge.com, martin.sotheran@continuumbridge.com, peter.claydon@continuumbridge.com"
date
./CBr_mailBW.py --user bridges@continuumbridge.com --password Mucht00f@r --key c685297d8c0f710e3bd1c8e771eb8d3d --bid BID66 --to "martin.sotheran@continuumbridge.com, peter.claydon@continuumbridge.com, Praminda.Caleb-solly@uwe.ac.uk, Amalia.Tsanaka@uwe.ac.uk"

