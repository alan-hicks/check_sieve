check_sieve
===========

Check SIEVE connections as per rfc 5804 for Nagios

check_sieve.py and check_sieve.pl

Example::

	check_sieve.py -H localhost -P 4190 -w 5 -c 10

Returns a warning if the response is greater than 5 seconds,
or a critical error if it is greater than 10.

Dual licence: FreeBSD License/GPL

Copyright (c) 2014, 2015 Persistent Objects Ltd - http://p-o.co.uk
All rights reserved.
