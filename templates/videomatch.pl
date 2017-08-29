#! /usr/bin/perl

use strict;
use Getopt::Long;

my $version;
my $debug = 0;
my $empty = 0;

my $ffmpeg  = "ffmpeg-3.3-static";
my $ffprobe = "ffprobe-3.3-static";
my $tmpdir  = "/tmp";

GetOptions ('version' => \$version, 'debug' => \$debug, 'empty' => \$empty);

if (defined($version)) {
  print "videomatch.pl version 1.0 using $ffmpeg and $ffprobe\n";
  exit;
}

my $in1 = $ARGV[0];
my $in2 = $ARGV[1];

if (!$empty && (!defined($in1) || !defined($in2))) {
  die "Must specify 2 input videos\n";
}

if ($empty && !defined($in1)) {
  die "Must specify an input video\n";
}

if ($empty) {
  print check_empty($in1);
} else {
  print compare($in1, $in2);
}

print "\n";

exit;


######################

sub compare ($$) {

	my $in1 = shift;
	my $in2 = shift;

        my $p_compare = 0;

	if ($debug) { print "in: $in1 $in2\n"; }

	my $timestamp=`date +%s%N`;
	chomp($timestamp);

	my $v1 = "$tmpdir/video1.$timestamp.avi";
	my $v2 = "$tmpdir/video2.$timestamp.avi";

	if ($debug) { print "Downscaling videos to v1=$v1 v2=$v2\n"; }

	# Downscale and compare videos

	system("$ffmpeg -nostats -loglevel 0 -i $in1 -vf scale=256:-1 -r 1 $v1");
	system("$ffmpeg -nostats -loglevel 0 -i $in2 -vf scale=256:-1 -r 1 $v2");

        die "Unable to downscale $in1 to $v1\n" if ! -e $v1;
        die "Unable to downscale $in2 to $v2\n" if ! -e $v2;

	if ($debug) { print "Comparing videos\n"; }

	# First compare by md5sum of the downscaled versions

	my $md5_v1 = (split(' ', `md5sum $v1`))[0];
	my $md5_v2 = (split(' ', `md5sum $v2`))[0];
	if ($debug) { print "MD5: $md5_v1 $md5_v2\n"; }

	if ($md5_v1 eq $md5_v2) {
	   if ($debug) { print "MD5 signatures of scaled versions are identical\n"; }
           return 100;
	}

	my $match = `ulimit -c 0; $ffmpeg -i $v1 -i $v2 -filter_complex "[0:v][1:v] signature=nb_inputs=2:detectmode=full" -map :v -f null - 2>&1 | grep Parsed_signature_0`;

	# Possible outputs
	# [Parsed_signature_0 @ 0x3f4aee0] no matching of video 0 and 1
	# [Parsed_signature_0 @ 0x47d6380] matching of video 0 at 12.000000 and 1 at 1.000000, 108 frames matching
	# [Parsed_signature_0 @ 0x47d6380] whole video matching
	# or segfault - https://trac.ffmpeg.org/ticket/6354

	my $frames_match = 0;

	if ($debug) { print "Match: $match\n"; }

	if ($match =~ /matching of video 0 at [0-9.]+ and 1 at [0-9.]+, ([0-9]+) frames matching/) {
	  $frames_match = $1;
	  if ($debug) { print "Frames: $frames_match\n"; }
	}

	if ($frames_match > 0) {
	  # Framecount of V1
	  my $framecount=`$ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of default=nokey=1:noprint_wrappers=1 $v1`;
	  chomp($framecount);
	  if ($debug) { print "Framecount: $framecount\n"; }
	  $p_compare = int($frames_match / $framecount * 100);
	}

	if (!$debug) {
	  unlink($v1);
	  unlink($v2);
	}

        return $p_compare;
}

#################

sub check_empty ($) {

	my $in1 = shift;

        my $p_empty = 0;

        if ($debug) { print "in: $in1\n"; }

        my $timestamp=`date +%s%N`;
        chomp($timestamp);

        my $v1 = "$tmpdir/video1.$timestamp.avi";

        if ($debug) { print "Downscaling video to v1=$v1\n"; }

        # Downscale and compare videos - marginally faster than running blackdetect on the original
        # plus we are guaranteed correct duration information

        system("$ffmpeg -nostats -loglevel 0 -i $in1 -vf scale=160:-1 -r 1 $v1");

	die "Unable to downscale $in1 to $v1\n" if ! -e $v1;

        if ($debug) { print "Checking for blank content\n"; }

        my $duration = `$ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 $v1`;
        chomp($duration);

        my $black = `$ffprobe -f lavfi -i "movie=$v1,blackdetect[out0]" -show_entries tags=lavfi.black_start,lavfi.black_end -of default=nw=1 2>&1 | grep black_duration`;

        # Expect output like:
        # [blackdetect @ 0x49e5ca0] black_start:0 black_end:3300 black_duration:3300

	if ($debug) { print "duration: $duration\nblack: $black"; }

        my @lines = split('\n', $black);

	my $b_total_duration = 0;

        foreach my $line (@lines) {
		if ($line =~ /black_start:([0-9]+) black_end:([0-9]+) black_duration:([0-9]+)/) {
			my $b_start = $1;
			my $b_end = $2;
			my $b_duration = $3;
			$b_total_duration += $b_duration;
		}
        }

	$p_empty = int($b_total_duration / $duration * 100);

	if (!$debug) {
	  unlink($v1);
	}

        return $p_empty;
}
