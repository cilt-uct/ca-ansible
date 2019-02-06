#! /bin/bash


/usr/bin/xrandr -d :0 --output VIRTUAL1 --primary --auto
/usr/bin/xrandr --newmode "1024x768_60.00" 63.50 1024 1072 1176 1328 768 771 775 798 -hsync +vsync
/usr/bin/xrandr --addmode VIRTUAL1 "1024x768_60.00"
/usr/bin/xrandr
