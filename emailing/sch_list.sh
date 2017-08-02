#!/bin/bash
#
# Used with the following line in /etc/crontab:
# 15 12   * * *   bridge  /home/bridge/bridge_admin/emailing/sch_list.sh >> /home/bridge/bridge_admin/emailing/sch_mail.log 2>&1
#



cd /home/ubuntu/bridge_admin/ifx_utils/CBr_mailing

# CBr
#date
#./ifx_CBr_mail.py --user bridges@continuumbridge.com --password Mucht00f@r --bid BID66 --db "Bridges" --template "2016-12-05_CBr_table_template.htm" --to "martin.sotheran@continuumbridge.com, peter.claydon@continuumbridge.com, Praminda.Caleb-solly@uwe.ac.uk"

#date
#./friendly_CBr_mail.py --user bridges@continuumbridge.com --password Mucht00f@r --bid BID241 --db "Bridges" --template "2016-12-05_CBr_table_template.htm" --to "martin.sotheran@continuumbridge.com, peter.claydon@continuumbridge.com, steve.barraclough@continuumbridge.com"

#date
#./friendly_CBr_mail.py --user bridges@continuumbridge.com --password Mucht00f@r --bid BID11 --db "Bridges" --template "2016-12-05_CBr_table_template.htm" --to "martin.sotheran@continuumbridge.com"

# Sirona
#date
#./friendly_CBr_mail.py --user bridges@continuumbridge.com --password Mucht00f@r --bid BID36 --db "SCH" --template Sirona_table_template.htm --to "martin.sotheran@continuumbridge.com, peter.claydon@continuumbridge.com"
#date
#./friendly_CBr_mail.py --user bridges@continuumbridge.com --password Mucht00f@r --bid BID45 --db "SCH" --template Sirona_table_template.htm --to "simon.allen@sirona-cic.org.uk, martin.sotheran@continuumbridge.com"
#date
#./friendly_CBr_mail.py --user bridges@continuumbridge.com --password Mucht00f@r --bid BID67 --db "SCH" --template Sirona_table_template.htm --to "christopher.burfield@sirona-cic.org.uk, martin.sotheran@continuumbridge.com, peter.claydon@continuumbridge.com"

# Generate Sirona data warehouse CSV file
#cd /home/ubuntu/bridge_admin/ifx_utils
#date
#./warehouse_ifx.py --db "SCH" --bids "BID36" "BID67" "BID45" --daysago 1
