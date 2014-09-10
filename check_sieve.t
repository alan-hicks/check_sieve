#!/usr/local/bin/perl
# 
# $Id: check_sieve.t 182 2013-03-25 16:35:03Z alan $
#
# check SIEVE connections as per rfc 5804
#
# Copyright (c) 2013 Persistent Objects Ltd - http://p-o.co.uk
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

use strict; use warnings;
use Test::More tests => 17;

my ($r,$args);
my $s = 'check_sieve.pl';
$s = "$^X -Ilib $s";

my $n = 'SIEVE';

# Nagios status strings and exit codes
my %e  = qw(
			 OK           0
			 WARNING      1
			 CRITICAL     2
			 UNKNOWN      3
			 );

$r = `$s`;
is 	$?>>8 , 	$e{OK}, 			"exits($e{OK}) with no args";
like 	$r,		qr/^$n OK/,			"OK with no args";

$r = `$s -V`;
is 	$?>>8 , 	$e{UNKNOWN}, 		"exits($e{UNKNOWN}) with -V arg";
like 	$r,		qr/^[\w\.]+ \d+/i,	"looks like there's a version";

$r = `$s -h`;
is 	$?>>8 , 	$e{UNKNOWN}, 		"exits($e{UNKNOWN}) with -h arg";
like 	$r,		qr/usage/i,	"looks like there's something helpful";  # broken

$args = " -r 99 ";
diag "running `$s $args`" if $ENV{TEST_VERBOSE};
$r = `$s $args`;
diag "output:  '$r'" if $ENV{TEST_VERBOSE};
is 	$?>>8 , 	$e{UNKNOWN}, 		"exits($e{UNKNOWN}) with $args";
like 	$r,		qr/UNKNOWN.+invalid/i,	"UNKNOWN (warning: invalid -r) with $args";

$r = `$s -v`;
is 	$?>>8 , 	$e{OK}, 		"exits($e{OK}) with -v arg";
like 	$r,		qr/fileinto/i,	"capabilities include fileinto";  # broken
like 	$r,		qr/connected to/i,	"includes connection info";  # broken

my $expected = {
	" -w 2 -c5 -r 3 -P 4190"     =>  'WARNING',
	" -w 10 -c15 -r 5 -P 4190"     =>  'OK',
	" -w 10 -c15 -r 20 -P 4190"   =>  'CRITICAL',
};

test_expected( $s, $expected );

sub test_expected {
	my $s = shift;
    my $expected = shift;
    foreach ( keys %$expected ) {
		diag "running `$s $_`" if $ENV{TEST_VERBOSE};
		$r = `$s $_`;
		diag "output:  '$r'" if $ENV{TEST_VERBOSE};
		is 	$?>>8 , 	$e{$expected->{$_}}, 		"exits($e{$expected->{$_}}) with $_";
		like 	$r,		qr/^$n $expected->{$_}/i,	"looks $expected->{$_} with $_";
	}
}
