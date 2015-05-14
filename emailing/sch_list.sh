#!/bin/bash
#
# Used with the following line in /etc/crontab:
# 15 12   * * *   bridge  /home/bridge/bridge_admin/emailing/sch_list.sh >> /home/bridge/bridge_admin/emailing/sch_mail.log 2>&1
#

cd /home/ubuntu/bridge_admin/ifx_utils/CBr_mailing

# CBr

# Stopped BID66 02/04
#date
#./ifx_CBr_mail.py --user bridges@continuumbridge.com --password Mucht00f@r --bid BID66 --db "Bridges" --template "CBr_table_template.htm" --to "martin.sotheran@continuumbridge.com, peter.claydon@continuumbridge.com, Praminda.Caleb-solly@uwe.ac.uk, Amalia.Tsanaka@uwe.ac.uk"

date
./ifx_CBr_mail.py --user bridges@continuumbridge.com --password Mucht00f@r --bid BID12 --db "Bridges" --template "CBr_table_template.htm" --to "martin.sotheran@continuumbridge.com, carson.bradbury@continuumbridge.com, peter.claydon@continuumbridge.com"

date
./ifx_CBr_mail.py --user bridges@continuumbridge.com --password Mucht00f@r --bid BID11 --db "Bridges" --template "CBr_table_template.htm" --to "martin.sotheran@continuumbridge.com"

# Sirona
date
./ifx_CBr_mail.py --user bridges@continuumbridge.com --password Mucht00f@r --bid BID36 --db "SCH" --template "Sirona_table_template.htm" --to "martin.sotheran@continuumbridge.com, peter.claydon@continuumbridge.com, martyn.price@sirona-cic.org.uk"
#date
#./ifx_CBr_mail.py --user bridges@continuumbridge.com --password Mucht00f@r --bid BID45 --db "SCH" --template "Sirona_table_template.htm" --to "martin.sotheran@continuumbridge.com, peter.claydon@continuumbridge.com, Mandy.Miles@sirona-cic.org.uk"
date
./ifx_CBr_mail.py --user bridges@continuumbridge.com --password Mucht00f@r --bid BID67 --db "SCH" --template "Sirona_table_template.htm" --to "martin.sotheran@continuumbridge.com, peter.claydon@continuumbridge.com, richard.tarring@sirona-cic.org.uk"

