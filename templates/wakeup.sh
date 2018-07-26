#! /bin/sh
echo 0 > /sys/class/rtc/rtc0/wakealarm
echo `date '+%s' -d 'tomorrow 06:00'` > /sys/class/rtc/rtc0/wakealarm
cat /sys/class/rtc/rtc0/wakealarm > /var/log/last_known_wakeup_time

