#!/usr/bin/env python
"""
check SIEVE connections as per rfc 5804

check_sieve.py
Nagios check sieve

Example:
check_sieve -H localhost -P 4190 -w 5 -c 10

Returns a warning if the response is greater than 5 seconds,
or a critical error if it is greater than 10.

Dual licence: FreeBSD License/GPL

Copyright (c) 2014 Persistent Objects Ltd - http://p-o.co.uk
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those
of the authors and should not be interpreted as representing official policies,
either expressed or implied, of Persistent Objects Ltd.
"""

from __future__ import print_function

__author__ = "Alan Hicks <ahicks@p-o.co.uk>"
__version__ = "1.00"

import datetime, re, socket, sys
from optparse import OptionParser


def pass_args(args):
    """Parse command line args"""
    usage = "usage: %prog [options] device"
    version = "%%prog %s" % (__version__)

    parser = OptionParser(usage=usage, version=version)

    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose", default=False,
                      help="Verbose output", metavar="VERBOSITY")
    parser.add_option("-H", "--host", default="localhost",
                      help="Host where the running daemon can be found, defaults to localhost.")
    parser.add_option("-P", "--port", type="int", default=4190,
                      help="Port number for the running daemon, default 4190.")
    parser.add_option("-4", "--ipv4",
                      action="store_true", dest="ipv4", default=False,
                      help="Use ip version 4")
    parser.add_option("-6", "--ipv6",
                      action="store_true", dest="ipv6", default=False,
                      help="Use ip version 6")
    parser.add_option("-t", "--timeout", type="int",
                      default=10,
                      help="Timout", metavar="TIMEOUT")
    parser.add_option("-c", "--critical", type="int",
                      default=10,
                      help="Number of seconds for a Critical error")
    parser.add_option("-w", "--warning", type="int",
                      default=5,
                      help="Number of seconds for a Warning")
    parser.add_option("-r", "--result",
                      help="Supplied result for testing.")
    return parser.parse_args(args)


class SIEVE:

    """SIEVE class to manage a sieve connection"""

    def get_sieve_info(self):
        """Get sieve service information"""
        ret_error = None
        capability = None
        implementation = None
        keyword = ''
        time_start = datetime.datetime.now()

        if options.ipv6:
            self.sock = socket.socket(socket.AF_INET6)
        if options.ipv4:
            self.sock = socket.socket(socket.AF_INET)
        else:
            self.sock = socket.socket()

        if options.timeout:
            self.sock.settimeout(options.timeout)

        try:
            self.sock.connect((options.host, options.port))
            self.file = self.sock.makefile("rb")
        except socket.error as e:
            if self.sock:
                self.sock.close()
            self.sock = None
            ret_error = str(e)

        count = 0
        if self.sock:
            while count < 10:
                # SIEVE capability should be within the first ten lines
                count += 1
                line = ''
                try:
                    line = self.file.readline().decode("utf-8")
                except socket.error as e:
                    self.sock.close()
                if line == '':
                    self.sock.close()
                if 'IMPLEMENTATION' in line.upper():
                    implementation = ''.join(re.findall('([a-zA-Z0-9., ])', line))
                    (keyword, implementation) = implementation.split(' ', 1)
                if 'SIEVE' in line.upper():
                    capability = ''.join(re.findall('([a-zA-Z0-9., ])', line))
                    (keyword, capability) = capability.split(' ', 1)
                if line.startswith('OK'):
                    break

        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
                self.sock.close()
            except socket.error as e:
                ret_error = "Error shutting down socket: " + str(e)
        time_end = datetime.datetime.now()
        time_diff = time_end - time_start

        return {
            'capability': capability,
            'implementation': implementation,
            'timing': time_diff,
            'error': ret_error
        }


(options, args) = pass_args(sys.argv)

ret_value = None
if options.warning > options.critical:
    # Invalid warning and critical values
    time_end = datetime.datetime.now()
    ret_value = 3
    ret_message = "UNKNOWN: Warning is greater than Critical"
    sieve_result = {
        'capability': '',
        'implementation': '',
        'timing': time_end - time_end,
        'error': ''
    }
elif options.result:
    # User provided result
    time_end = datetime.datetime.now()
    sieve_result = {
        'capability': options.result,
        'implementation': 'Test result',
        'timing': time_end - time_end,
        'error': ''
    }
else:
    sieve = SIEVE()
    sieve_result = sieve.get_sieve_info()

# Assess status if not already defined
if not ret_value:
    if sieve_result['error']:
        ret_value = 2
        ret_message = "SIEVE CRITICAL: Service is not available: " + sieve_result['error']
    if sieve_result['capability']:
        resp_time = "%s.%s second response time;" % (
            sieve_result['timing'].seconds,
            sieve_result['timing'].microseconds
        )
        if sieve_result['timing'].seconds >= options.critical:
            ret_value = 2
            ret_message = "SIEVE CRITICAL: Service is functional " + resp_time
        elif sieve_result['timing'].seconds >= options.warning:
            ret_value = 1
            ret_message = "SIEVE WARNING: Service is functional " + resp_time
        else:
            ret_value = 0
            ret_message = "SIEVE OK: Service is functional " + resp_time
    else:
        ret_value = 2
        ret_message = "SIEVE CRITICAL: Service is not available;"

if options.verbose:
    if options.result:
        ret_message1 = " Host test result;"
    else:
        ret_message1 = " Host " + options.host + ':' + str(options.port) + ';'
    if sieve_result['capability']:
        ret_message2 = " [" + sieve_result['capability'] + '];'
    else:
        ret_message2 = ''
    if sieve_result['error']:
        ret_message2 = ret_message2 + " " + sieve_result['error'] + ';'
    print(ret_message + ret_message1 + ret_message2)
else:
    print(ret_message)
sys.exit(ret_value)
