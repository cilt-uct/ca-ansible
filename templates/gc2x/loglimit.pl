#! /usr/bin/perl

## Log a limited number of lines (to avoid running out of disk space)

use strict;
my $linelimit = $ARGV[0];

my $logging = 1;
my $logged = 1;

# Command buffering
$| = 1;

while (<STDIN>) {
	if ($logging) {
		print $_;
		$logged++;
	}

	if ($logging && ($logged > $linelimit)) {
		$logging = 0;
		print "Logging suspended: limit of $linelimit log lines exceeded\n";
	}
}

