#!/bin/bash

# This script does nothing useful if clock is not in sync
# Argo Ellisson 2015, BashPi.org, usage licence: GNU General Public License (GPL) Version 3
# version 1.0

# use ntp-wait to check if clock is in sync
sudo /usr/sbin/ntp-wait -n 5 -s 3
RETVAL=$?

if [ "$RETVAL" != "0" ];then
echo "Timesync not done, trying with hwclock... "
sudo hwclock -s
exit 1
else
echo "blah! Clock is in sync!, setting ntp-clock into hwclock"
sudo hwclock -w
fi
