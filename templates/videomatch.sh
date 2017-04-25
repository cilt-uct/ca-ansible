#! /bin/bash

TMPDIR=/tmp
FFMPEG=/home/galicaster/ffmpeg-3.3-64bit-static/ffmpeg

TIMESTAMP=`date +%s%N`

V1=$TMPDIR/video1.$TIMESTAMP.avi
V2=$TMPDIR/video2.$TIMESTAMP.avi

FFMPEG=/home/galicaster/ffmpeg-3.3-64bit-static/ffmpeg

# Downscale and compare videos
$FFMPEG -nostats -loglevel 0 -i $1 -vf scale=160:-1 -r 1 $V1
$FFMPEG -nostats -loglevel 0 -i $2 -vf scale=160:-1 -r 1 $V2
MATCH=`$FFMPEG -i $V1 -i $V2 -filter_complex "[0:v][1:v] signature=nb_inputs=2:detectmode=full" -map :v -f null - 2>&1 | grep -c "whole video matching"`

rm -f $V1 $V2

echo "match:$MATCH"

