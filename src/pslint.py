#!/usr/bin/env python
# -*- coding: utf-8 -*-#
#
# PSL linter written in python
#
# Copyright 2016 Tim Rühsen (tim dot ruehsen at gmx dot de). All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import sys

nline = 0
line = ""
warnings = 0
errors = 0

def warning(msg):
	global warnings, line, nline
	print('%d: warning: %s: \'%s\'' % (nline, msg, line))
	warnings += 1

def error(msg):
	global errors, line, nline
	print('%d: error: %s: \'%s\'' % (nline, msg, line))
	errors += 1

def lint_psl(infile):
	"""Parses PSL file and extract strings and return code"""
	global line, nline

	PSL_FLAG_EXCEPTION = (1<<0)
	PSL_FLAG_WILDCARD = (1<<1)
	PSL_FLAG_ICANN = (1<<2) # entry of ICANN section
	PSL_FLAG_PRIVATE = (1<<3) # entry of PRIVATE section
	PSL_FLAG_PLAIN = (1<<4) #just used for PSL syntax checking

	line2number = {}
	line2flag = {}
	section = 0

	lines = [line.strip('\r\n') for line in infile]

	for line in lines:
		nline += 1

		# check for leadind/trailing whitespace
		stripped = line.strip()
		if stripped != line:
			warning('Leading/Trailing whitespace')
		line = stripped

		# empty line
		if not line:
			continue

		# check for section begin/end
		if line[0:2] == "//":
			if section == 0:
				if line == "// ===BEGIN ICANN DOMAINS===":
					section = PSL_FLAG_ICANN
				elif line == "// ===BEGIN PRIVATE DOMAINS===":
					section = PSL_FLAG_PRIVATE
				elif line[3:8] == "===BEGIN":
					error('Unexpected begin of unknown section')
				elif line[3:6] == "===END":
					error('End of section without previous begin')
			elif section == PSL_FLAG_ICANN:
				if line == "// ===END ICANN DOMAINS===":
					section = 0
				elif line[3:8] == "===BEGIN":
					error('Unexpected begin of section: ')
				elif line[3:6] == "===END":
					error('Unexpected end of section')
			elif section == PSL_FLAG_PRIVATE:
				if line == "// ===END ICANN DOMAINS===":
					section = 0
				elif line[3:8] == "===BEGIN":
					error('Unexpected begin of section')
				elif line[3:6] == "===END":
					error('Unexpected end of section')

			continue # processing of comments ends here

		# No rule must be outside of a section
		if section == 0:
			error('Rule outside of section')

		# decode UTF-8 input into unicode, needed only for python 2.x
		if sys.version_info[0] < 3:
			line = line.decode('utf-8')

	 # each rule must be lowercase (or more exactly: not uppercase and not titlecase)
		if line != line.lower():
			error('Rule must be lowercase')

		# strip leading wildcards
		flags = section
		# while line[0:2] == '*.':
		if line[0:2] == '*.':
			flags |= PSL_FLAG_WILDCARD
			line = line[2:]

		if line[0] == '!':
			flags |= PSL_FLAG_EXCEPTION
			line = line[1:]
		else:
			flags |= PSL_FLAG_PLAIN

		# wildcard and exception must not combine
		if flags & PSL_FLAG_WILDCARD and flags & PSL_FLAG_EXCEPTION:
			error('Combination of wildcard and exception')

		labels = line.split('.')

		for label in labels:
			if not label:
				 error('Leading/trailing or multiple dot')
				 continue

			if label[0:4] == 'xn--':
				 error('Punycode found')
				 continue

			if '--' in label:
				 error('Double minus found')
				 continue

			# allowed are a-z,0-9,- and unicode >= 128 (maybe that can be finetuned a bit !?)
			for c in label:
				if not c.isalnum() and c != '-' and ord(c) < 128:
					error('Illegal character')
					break

		if line in line2number:
			"""Found existing entry:
			   Combination of exception and plain rule is ambiguous
			     !foo.bar
			      foo.bar

			   Allowed:
			     !foo.bar + *.foo.bar
			      foo.bar + *.foo.bar
			"""
			error('Found doublette/ambiguity (previous line was %d)' % line2number[line])
			continue

		line2number[line] = nline
		line2flag[line] = flags


def usage():
	"""Prints the usage"""
	print('usage: %s PSLfile' % sys.argv[0])
	print('or     %s -        # To read PSL from STDIN' % sys.argv[0])
	exit(1)


def main():
	"""Check syntax of a PSL file"""
	if len(sys.argv) < 2:
		usage()

	if sys.argv[-1] == '-':
		lint_psl(sys.stdin)
	else:
		with open(sys.argv[-1], 'r') as infile:
			lint_psl(infile)

	return errors != 0


if __name__ == '__main__':
	sys.exit(main())
