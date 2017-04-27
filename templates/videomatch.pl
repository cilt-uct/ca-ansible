#! /usr/bin/perl

use strict;
use Getopt::Long;

my $version;
my $debug = 0;

my $ffmpeg  = "ffmpeg-3.3-static";
my $ffprobe = "ffprobe-3.3-static";
my $tmpdir  = "/tmp";

GetOptions ('version' => \$version, 'debug' => \$debug);

if (defined($version)) {
  print "videomatch.pl version 1.0 using $ffmpeg and $ffprobe\n";
  exit;
}

my $in1 = $ARGV[0];
my $in2 = $ARGV[1];

if (!defined($in1) || !defined($in2)) {
  die "Must specify 2 input videos\n";
}

if ($debug) { print "in: $in1 $in2\n"; }

my $timestamp=`date +%s%N`;
chomp($timestamp);

my $v1 = "$tmpdir/video1.$timestamp.avi";
my $v2 = "$tmpdir/video2.$timestamp.avi";

if ($debug) { print "Downscaling videos to v1=$v1 v2=$v2\n"; }

# Downscale and compare videos

system("$ffmpeg -nostats -loglevel 0 -i $in1 -vf scale=256:-1 -r 1 $v1");
system("$ffmpeg -nostats -loglevel 0 -i $in2 -vf scale=256:-1 -r 1 $v2");

if ($debug) { print "Comparing videos\n"; }

my $match = `ulimit -c 0; $ffmpeg -i $v1 -i $v2 -filter_complex "[0:v][1:v] signature=nb_inputs=2:detectmode=full" -map :v -f null - 2>&1 | grep Parsed_signature_0`;

# Possible outputs
# [Parsed_signature_0 @ 0x3f4aee0] no matching of video 0 and 1
# [Parsed_signature_0 @ 0x47d6380] matching of video 0 at 12.000000 and 1 at 1.000000, 108 frames matching
# [Parsed_signature_0 @ 0x47d6380] whole video matching
# or segfault - https://trac.ffmpeg.org/ticket/6354

my $frames_match = 0;

# print "Match: $match\n";
if ($match =~ /matching of video 0 at [0-9.]+ and 1 at [0-9.]+, ([0-9]+) frames matching/) {
  $frames_match = $1;
  if ($debug) { print "Frames: $frames_match\n"; }
}

if ($frames_match > 0) {
  # Framecount of V1
  my $framecount=`$ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of default=nokey=1:noprint_wrappers=1 $v1`;
  chomp($framecount);
  if ($debug) { print "Framecount: $framecount\n"; }
  my $partial_match = ($frames_match / $framecount) * 100;
  print int($partial_match) . "\n";
} else {
  # No match (or segfault or other failure)
  print "0\n";
}

if (!$debug) {
  unlink($v1);
  unlink($v2);
}

