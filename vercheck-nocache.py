#!/usr/bin/python3
import re
import sys, os, time
from threading import Thread
import urllib3, urllib
import json
import getopt
import signal
from distutils.version import LooseVersion
import string
import subprocess
#import socket
#from urllib3.connection import HTTPConnection
import pdb

### main class that deals with command lines, reports and everything else
class SCCVersion():

	# static product list (taken from RMT and other sources)
	# rmt-cli products list --name "SUSE Linux Enterprise Server" --all
	# rmt-cli products list --name "SUSE Linux Enterprise Desktop" --all
	# rmt-cli products list --name "openSUSE" --all
	product_list = {
		1115: { 'name': 'SUSE Linux Enterprise Server 12 s390x', 'arch': 's390x', 'identifier': 'cpe:/o:suse:sles:12' },
		1116: { 'name': 'SUSE Linux Enterprise Server 12 ppc64le', 'arch': 'ppc64le', 'identifier': 'cpe:/o:suse:sles:12' },
		1117: { 'name': 'SUSE Linux Enterprise Server 12 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles:12' },
		1118: { 'name': 'SUSE Linux Enterprise Desktop 12 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sled:12' },
		1322: { 'name': 'SUSE Linux Enterprise Server 12 SP1 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles:12:sp1' },
		1333: { 'name': 'SUSE Linux Enterprise Desktop 12 SP1 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sled:12:sp1' },
		1334: { 'name': 'SUSE Linux Enterprise Server 12 SP1 ppc64le', 'arch': 'ppc64le', 'identifier': 'cpe:/o:suse:sles:12:sp1' },
		1335: { 'name': 'SUSE Linux Enterprise Server 12 SP1 s390x', 'arch': 's390x', 'identifier': 'cpe:/o:suse:sles:12:sp1' },
		1355: { 'name': 'SUSE Linux Enterprise Server 12 SP2 ppc64le', 'arch': 'ppc64le', 'identifier': 'cpe:/o:suse:sles:12:sp2' },
		1356: { 'name': 'SUSE Linux Enterprise Server 12 SP2 s390x', 'arch': 's390x', 'identifier': 'cpe:/o:suse:sles:12:sp2' },
		1357: { 'name': 'SUSE Linux Enterprise Server 12 SP2 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles:12:sp2' },
		1375: { 'name': 'SUSE Linux Enterprise Server 12 SP2 aarch64', 'arch': 'aarch64', 'identifier': 'cpe:/o:suse:sles:12:sp2' },
		1358: { 'name': 'SUSE Linux Enterprise Desktop 12 SP2 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sled:12:sp2' },
		1421: { 'name': 'SUSE Linux Enterprise Server 12 SP3 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles:12:sp3' },
		1422: { 'name': 'SUSE Linux Enterprise Server 12 SP3 ppc64le', 'arch': 'ppc64le', 'identifier': 'cpe:/o:suse:sles:12:sp3' },
		1423: { 'name': 'SUSE Linux Enterprise Server 12 SP3 s390x', 'arch': 's390x', 'identifier': 'cpe:/o:suse:sles:12:sp3' },
		1424: { 'name': 'SUSE Linux Enterprise Server 12 SP3 aarch64', 'arch': 'aarch64', 'identifier': 'cpe:/o:suse:sles:12:sp3' },
		1425: { 'name': 'SUSE Linux Enterprise Desktop 12 SP3 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sled:12:sp3' },
		1625: { 'name': 'SUSE Linux Enterprise Server 12 SP4 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles:12:sp4' },
		1626: { 'name': 'SUSE Linux Enterprise Server 12 SP4 ppc64le', 'arch': 'ppc64le', 'identifier': 'cpe:/o:suse:sles:12:sp4' },
		1627: { 'name': 'SUSE Linux Enterprise Server 12 SP4 s390x', 'arch': 's390x', 'identifier': 'cpe:/o:suse:sles:12:sp4' },
		1628: { 'name': 'SUSE Linux Enterprise Server 12 SP4 aarch64', 'arch': 'aarch64', 'identifier': 'cpe:/o:suse:sles:12:sp4' },
		1629: { 'name': 'SUSE Linux Enterprise Desktop 12 SP4 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sled:12:sp4' },
		1875: { 'name': 'SUSE Linux Enterprise Server 12 SP5 aarch64', 'arch': 'aarch64', 'identifier': 'cpe:/o:suse:sles:12:sp5' },
		1876: { 'name': 'SUSE Linux Enterprise Server 12 SP5 ppc64le', 'arch': 'ppc64le', 'identifier': 'cpe:/o:suse:sles:12:sp5' },
		1877: { 'name': 'SUSE Linux Enterprise Server 12 SP5 s390x', 'arch': 's390x', 'identifier': 'cpe:/o:suse:sles:12:sp5' },
		1878: { 'name': 'SUSE Linux Enterprise Server 12 SP5 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles:12:sp5' },
		1319: { 'name': 'SUSE Linux Enterprise Server for SAP Applications 12 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles_sap:12' },
		1346: { 'name': 'SUSE Linux Enterprise Server for SAP Applications 12 SP1 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles_sap:12:sp1' },
		1414: { 'name': 'SUSE Linux Enterprise Server for SAP Applications 12 SP2 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles_sap:12:sp2' },
		1426: { 'name': 'SUSE Linux Enterprise Server for SAP Applications 12 SP3 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles_sap:12:sp3' },
		1437: { 'name': 'SUSE Linux Enterprise Server for SAP Applications 12 SP1 ppc64le', 'arch': 'ppc64le', 'identifier': 'cpe:/o:suse:sles_sap:12:sp1' },
		1521: { 'name': 'SUSE Linux Enterprise Server for SAP Applications 12 SP2 ppc64le', 'arch': 'ppc64le', 'identifier': 'cpe:/o:suse:sles_sap:12:sp2' },
		1572: { 'name': 'SUSE Linux Enterprise Server for SAP Applications 12 SP3 ppc64le', 'arch': 'ppc64le', 'identifier': 'cpe:/o:suse:sles_sap:12:sp3' },
		1754: { 'name': 'SUSE Linux Enterprise Server for SAP Applications 12 SP4 ppc64le', 'arch': 'ppc64le', 'identifier': 'cpe:/o:suse:sles_sap:12:sp4' },
		1755: { 'name': 'SUSE Linux Enterprise Server for SAP Applications 12 SP4 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles_sap:12:sp4' },
		1879: { 'name': 'SUSE Linux Enterprise Server for SAP Applications 12 SP5 ppc64le', 'arch': 'ppc64le', 'identifier': 'cpe:/o:suse:sles_sap:12:sp5' },
		1880: { 'name': 'SUSE Linux Enterprise Server for SAP Applications 12 SP5 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles_sap:12:sp5' },	
		1612: { 'name': 'SUSE Linux Enterprise Server for SAP Applications 15 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles_sap:15' },	
		1613: { 'name': 'SUSE Linux Enterprise Server for SAP Applications 15 ppc64le', 'arch': 'ppc64le', 'identifier': 'cpe:/o:suse:sles_sap:15' },
		1765: { 'name': 'SUSE Linux Enterprise Server for SAP Applications 15 SP1 ppc64le', 'arch': 'ppc64le', 'identifier': 'cpe:/o:suse:sles_sap:15:sp1' },	
		1766: { 'name': 'SUSE Linux Enterprise Server for SAP Applications 15 SP1 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles_sap:15:sp1' },
		1940: { 'name': 'SUSE Linux Enterprise Server for SAP Applications 15 SP2 ppc64le', 'arch': 'ppc64le', 'identifier': 'cpe:/o:suse:sles_sap:15:sp2' },	
		1941: { 'name': 'SUSE Linux Enterprise Server for SAP Applications 15 SP2 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles_sap:15:sp2' },  
  		2135: { 'name': 'SUSE Linux Enterprise Server for SAP Applications 15 SP3 ppc64le', 'arch': 'ppc64le', 'identifier': 'cpe:/o:suse:sles_sap:15:sp3' },
		2136: { 'name': 'SUSE Linux Enterprise Server for SAP Applications 15 SP3 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles_sap:15:sp3' },
		2293: { 'name': 'SUSE Linux Enterprise Server for SAP Applications 15 SP4 ppc64le', 'arch': 'ppc64le', 'identifier': 'cpe:/o:suse:sles_sap:15:sp4' },
		2294: { 'name': 'SUSE Linux Enterprise Server for SAP Applications 15 SP4 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles_sap:15:sp4' },
		2467: { 'name': 'SUSE Linux Enterprise Server for SAP Applications 15 SP5 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles_sap:15:sp5' },
		1575: { 'name': 'SUSE Linux Enterprise Server 15 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles:15' },
		1584: { 'name': 'SUSE Linux Enterprise Server 15 s390x', 'arch': 's390x', 'identifier': 'cpe:/o:suse:sles:15' },
		1585: { 'name': 'SUSE Linux Enterprise Server 15 ppc64le', 'arch': 'ppc64le', 'identifier': 'cpe:/o:suse:sles:15' },
		1586: { 'name': 'SUSE Linux Enterprise Server 15 aarch64', 'arch': 'aarch64', 'identifier': 'cpe:/o:suse:sles:15' },
		1609: { 'name': 'SUSE Linux Enterprise Desktop 15 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sled:15' },
		1760: { 'name': 'SUSE Linux Enterprise Server 15 SP1 aarch64', 'arch': 'aarch64', 'identifier': 'cpe:/o:suse:sles:15:sp1' },
		1761: { 'name': 'SUSE Linux Enterprise Server 15 SP1 ppc64le', 'arch': 'ppc64le', 'identifier': 'cpe:/o:suse:sles:15:sp1' },
		1762: { 'name': 'SUSE Linux Enterprise Server 15 SP1 s390x', 'arch': 's390x', 'identifier': 'cpe:/o:suse:sles:15:sp1' },
		1763: { 'name': 'SUSE Linux Enterprise Server 15 SP1 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles:15:sp1' },
		1764: { 'name': 'SUSE Linux Enterprise Desktop 15 SP1 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sled:15:sp1' },
		1936: { 'name': 'SUSE Linux Enterprise Server 15 SP2 aarch64', 'arch': 'aarch64', 'identifier': 'cpe:/o:suse:sles:15:sp2' },
		1937: { 'name': 'SUSE Linux Enterprise Server 15 SP2 ppc64le', 'arch': 'ppc64le', 'identifier': 'cpe:/o:suse:sles:15:sp2' },
		1938: { 'name': 'SUSE Linux Enterprise Server 15 SP2 s390x', 'arch': 's390x', 'identifier': 'cpe:/o:suse:sles:15:sp2' },
		1939: { 'name': 'SUSE Linux Enterprise Server 15 SP2 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles:15:sp2' },
		1935: { 'name': 'SUSE Linux Enterprise Desktop 15 SP2 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sled:15:sp2' },
  		2137: { 'name': 'SUSE Linux Enterprise Server 15 SP3 aarch64', 'arch': 'aarch64', 'identifier': 'cpe:/o:suse:sles:15:sp3' },
		2138: { 'name': 'SUSE Linux Enterprise Server 15 SP3 ppc64le', 'arch': 'ppc64le', 'identifier': 'cpe:/o:suse:sles:15:sp3' },
		2139: { 'name': 'SUSE Linux Enterprise Server 15 SP3 s390x', 'arch': 's390x', 'identifier': 'cpe:/o:suse:sles:15:sp3' },
  		2140: { 'name': 'SUSE Linux Enterprise Server 15 SP3 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles:15:sp3' },
		2134: { 'name': 'SUSE Linux Enterprise Desktop 15 SP3 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sled:15:sp3' }, 
   		2289: { 'name': 'SUSE Linux Enterprise Server 15 SP4 aarch64', 'arch': 'aarch64', 'identifier': 'cpe:/o:suse:sles:15:sp4' },
		2290: { 'name': 'SUSE Linux Enterprise Server 15 SP4 ppc64le', 'arch': 'ppc64le', 'identifier': 'cpe:/o:suse:sles:15:sp4' },
		2291: { 'name': 'SUSE Linux Enterprise Server 15 SP4 s390x', 'arch': 's390x', 'identifier': 'cpe:/o:suse:sles:15:sp4' },
  		2292: { 'name': 'SUSE Linux Enterprise Server 15 SP4 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles:15:sp4' },
		2295: { 'name': 'SUSE Linux Enterprise Desktop 15 SP4 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sled:15:sp4' },
		2462: { 'name': 'SUSE Linux Enterprise Server 15 SP5 aarch64', 'arch': 'aarch64', 'identifier': 'cpe:/o:suse:sles:15:sp5' },
		2463: { 'name': 'SUSE Linux Enterprise Server 15 SP5 ppc64le', 'arch': 'ppc64le', 'identifier': 'cpe:/o:suse:sles:15:sp5' },
		2464: { 'name': 'SUSE Linux Enterprise Server 15 SP5 s390x', 'arch': 's390x', 'identifier': 'cpe:/o:suse:sles:15:sp5' },
		2465: { 'name': 'SUSE Linux Enterprise Server 15 SP5 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles:15:sp5' },
		2468: { 'name': 'SUSE Linux Enterprise Desktop 15 SP5 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sled:15:sp5' },
		1929: { 'name': 'openSUSE Leap 15.1 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:opensuse:leap:15.1' },
		2001: { 'name': 'openSUSE Leap 15.2 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:opensuse:leap:15.2' },
		2233: { 'name': 'openSUSE Leap 15.3 aarch64', 'arch': 'aarch64', 'identifier': 'cpe:/o:opensuse:leap:15.3' },
		2234: { 'name': 'openSUSE Leap 15.3 ppc64le', 'arch': 'ppc64le', 'identifier': 'cpe:/o:opensuse:leap:15.3' },
		2235: { 'name': 'openSUSE Leap 15.3 s390x', 'arch': 's390x', 'identifier': 'cpe:/o:opensuse:leap:15.3' },
		2236: { 'name': 'openSUSE Leap 15.3 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:opensuse:leap:15.3' },
		2406: { 'name': 'openSUSE Leap 15.4 aarch64', 'arch': 'aarch64', 'identifier': 'cpe:/o:opensuse:leap:15.4' },
		2407: { 'name': 'openSUSE Leap 15.4 ppc64le', 'arch': 'ppc64le', 'identifier': 'cpe:/o:opensuse:leap:15.4' },
		2408: { 'name': 'openSUSE Leap 15.4 s390x', 'arch': 's390x', 'identifier': 'cpe:/o:opensuse:leap:15.4' },
		2409: { 'name': 'openSUSE Leap 15.4 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:opensuse:leap:15.4' },
		2520: { 'name': 'openSUSE Leap Micro 5.2 aarch64', 'arch': 'aarch64', 'identifier': 'cpe:/o:opensuse:leap-micro:5.2' },
		2521: { 'name': 'openSUSE Leap Micro 5.2 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:opensuse:leap-micro:5.2' },
	}

	# to get the list of product IDs:
	# rmt-cli products list --name "SUSE Manager Server" --all
	suma_product_list = {

		1899: { 'name': 'SUSE Manager Server 4.0', 'identifier': '4.0' },
		2012: { 'name': 'SUSE Manager Server 4.1', 'identifier': '4.1' },
		2222: { 'name': 'SUSE Manager Server 4.2', 'identifier': '4.2' },
		2378: { 'name': 'SUSE Manager Server 4.3', 'identifier': '4.3' },
	}
 
	# result lists
	uptodate = []
	notfound = []
	different = []
	unsupported = []
 
	# report flags
	show_unknown = False
	show_diff = False
	show_uptodate = False
	show_unsupported = False

	# verbose messages
	verbose = False

	# base name for the reports
	sc_name = ''

	# maximum number of running threads
	max_threads = 15

	# time to wait before starting each chunk of threads
	wait_time = 1

	# override architecture
	arch = None

	short_response = False

	# default output directory for the reports
	outputdir = os.getcwd()
 
	def set_outputdir(self, newdir):
		self.outputdir = newdir
 
	def set_verbose(self, verbose):
		self.verbose = verbose

	def cleanup(self, signalNumber, frame):
		print('\nokay, okay, I\'m leaving!')
		self.write_reports()
		sys.exit(0)
		return

	def find_suma(self, directory_name):
		regex_suma=r"SUSE Manager release (.*) .*"
		try:
			f = open(directory_name + '/basic-environment.txt', 'r')
			text = f.read()
			f.close()
			matches_suma = re.search(regex_suma, text)
			for p in self.suma_product_list:
				if matches_suma is not None and matches_suma.group(1) == self.suma_product_list[p]['identifier']:
					return p
		except Exception as e:
			print ('error: ' + str(e))
		return -1

     
	def find_cpe(self, directory_name, architecture):
		regex_os= r"CPE_NAME=\"(.*)\""
		regex_sap=r"SLES_SAP-release-([0-9]+)-|SLES_SAP-release-([0-9]+)\.([0-9]+)"
		regex_sap_cpe=r".*sles_sap\:([0-9]+)$|.*sles_sap\:([0-9]+)\:[a-z]+?([0-9]+)"
		
		try:
			with open(directory_name + '/basic-environment.txt', 'r') as f:
				text = f.read()
				f.close()

			with open(directory_name + '/rpm.txt', 'r') as f:
				text_rpms = f.read()
				f.close()

			matches_os = re.search(regex_os, text)
			matches_sap = re.search(regex_sap, text_rpms)
			for p in self.product_list:
				# first, we try matching the SLES_SAP-release RPM as CPE strings -- according to TID 7023490, the sles_sap string cannot always be trusted...
				if matches_sap is not None:
					matches_sap_cpe = re.search(regex_sap_cpe, self.product_list[p]['identifier'])
					# we match the CPE in the product table (just for our control, remember the TID) and the architecture
					if matches_sap_cpe is not None and architecture == self.product_list[p]['arch']:
						# the string version does not have a service pack
						if matches_sap.group(1) is not None and matches_sap.group(1) ==  matches_sap_cpe.group(1):
							return p

						# the string version contains a service pack (matches are on groups 2 and 3)
						if matches_sap.group(2) is not None and matches_sap.group(2) ==  matches_sap_cpe.group(2) and matches_sap.group(3) ==  matches_sap_cpe.group(3):
							return p

				# if a SLES_SAP-release package is not found, fall back to checking the CPE
				elif matches_os.group(1) == self.product_list[p]['identifier'] and architecture == self.product_list[p]['arch']:
					return p

		except Exception as e:
			print ('error: ' + str(e))
		return -1
		
	def find_arch(self, directory_name):
		regex = r"^Architecture:\s+(\w+)"
		
		try:
			f = open(directory_name + '/hardware.txt', 'r')
			text = f.read()
			f.close()
			matches = re.search(regex, text, re.MULTILINE)
			if matches != None:
				return matches.group(1)
		except Exception as e:
			print ('error opening hardware.txt, trying basic-environment.txt...')
			try:
				f = open(directory_name + '/basic-environment.txt', 'r')
				text = f.read()
				f.close()
				regex = r"^Linux.* (\w+) GNU\/Linux$"
				matches = re.search(regex, text, re.MULTILINE)
				if matches != None:
					return matches.group(1)
			except Exception as e:
				print ('could not determine architecture for the supportconfig directory. Please supply one with -a.')
				return 'unknown'
		return 'unknown'

	def read_rpmlist(self, directory_name):
		rpmlist = []
		regex_start = r"(^NAME.*VERSION)\n"
		regex_package = r"(\S*)\s{2,}(\S{2,}.*)\s{2,}(.*)"
		regex_end = r"(^$)\n"
		try:
			f = open(directory_name + '/rpm.txt', 'r')
			text = f.readlines()
			f.close()

			found_start = False
			for line in text:
				matches = re.search(regex_start, line)
				if matches != None:
					found_start=True
					continue
				if found_start:
					matches = re.search(regex_end, line)
					if matches:
						break

					matches = re.search(regex_package, line)
					if matches:	
						rpmname = matches.group(1)
						rpmdistro = matches.group(2).strip(' \t\n')
						rpmversion = matches.group(3)
						if rpmname.startswith('gpg-pubkey'):
							continue
						if rpmname != '' and rpmdistro != '' and rpmversion != '':
							rpmlist.append([rpmname, rpmdistro, rpmversion])
					else:
						continue
		except Exception as e:
			print('error: ' + str(e))

		return rpmlist

	def list_chunk(self, data, size):
		return (data[pos:pos + size] for pos in range(0, len(data), size))

	def list_products(self):
		print('Known products list')
		print('ID	Name')
		print('-----------------------------------------------------')
		for k, v in self.product_list.items():
			print(str(k) + '\t' + v['name'])

		print('total: ' + str(len(self.product_list)) +  ' products.')
		return

	def usage(self):
		print('Usage: ' + sys.argv[0] + ' [-l|--list-products] -p|--product product id -n|--name <package name> [-s|--short] [-v|--verbose] [-1|--show-unknown] [-2|--show-differences] [-3|--show-uptodate] [-4|--show-unsupported] [-o|--outputdir] [-d|--supportconfig]')
		return

	def show_help(self):
		self.usage()	
		print('\n')
		print('-l|--list-products\t\tLists all supported products. Use this to get a valid product ID for further queries.\n')
		print('-p|--product <product id>\tSpecifies a valid product ID for queries. Mandatory for searches.\n')
		print('-n|--name <package name>\tSpecifies a package name to search. Exact matches only for now. Mandatory for searches.\n')
		print('-s|--short\t\t\tOnly outputs the latest version, useful for scripts\n')
		print('-v|--verbose\t\t\tOutputs extra information about the search and results\n')
		print('-1|--show-unknown\t\tshows unknown packages as they are found.\n')
		print('-2|--show-differences)\t\tshows packages that have updates available as they are found.\n')
		print('-3|--show-uptodate)\t\tshows packages that are on par with the updated versions as they are found.\n')
		print('-4|--show-unsupported)\t\tshows packages that have a vendor that is different from the system it was collected from.\n')
		print('-o|--outputdir)\t\tspecify an output directory for the reports. Default: current directory.\n')
		print('-d|--supportconfig\t\tAnalyzes a supportconfig directory and generates CSV reports for up-to-date, not found and different packages.\n')
		print('-a|--arch\t\tSupply an architecture for the supportconfig analysis.')
		print('\n')
		return

	def test(self):
		threads = []
		package_name = 'glibc'
		instance_nr = 0

		for k, v in self.product_list.items():
			print('searching for package \"glibc\" in product id \"' + str(k) + '\" (' + v['name'] + ')')
			threads.insert(instance_nr, PackageSearchEngine(instance_nr, k, package_name, v['name'], '0'))
			threads[instance_nr].start()
			instance_nr = instance_nr + 1

		# fetch results for all threads
		for thread_number in range(instance_nr):
			threads[thread_number].join()
			refined_data = threads[thread_number].get_results()
			try:
				print('[thread ' +  str(thread_number) + ' ] latest version for ' + refined_data['query'] + ' on product ID ' + str(refined_data['product_id']) +  ' is ' + refined_data['results'][0]['version'] + '-' + refined_data['results'][0]['release'])
				if self.verbose:
					for item in refined_data['results']:
							print('[thread ' +  str(thread_number) + ' ] version ' + item['version'] + '-' + item['release'] + ' is available on repository [' + item['repository'] + ']')
			except IndexError:
				print('could not find any version for package ' + package_name)

		return

	def search_package(self, product_id, package_name):

		threads = []

		if product_id in self.suma_product_list:
			plist = self.suma_product_list
		else:
			plist = self.product_list

		print('searching for package \"' + package_name + '\" in product id \"' + str(product_id) + '\" (' + plist[product_id]['name'] + ')')
		threads.insert(0, PackageSearchEngine(0, product_id, package_name, plist[product_id]['name'], '0'))
		threads[0].start()

		# fetch results for the only thread
		threads[0].join()
		refined_data = threads[0].get_results()
		try:
			if self.short_response:
				print(refined_data['results'][0]['version'] + '-' + refined_data['results'][0]['release'])
			else:
				print('latest version for ' + refined_data['query'] + ' on product ID ' + str(refined_data['product_id']) +  ' is ' + refined_data['results'][0]['version'] + '-' + refined_data['results'][0]['release'])
			if self.verbose:
				for item in refined_data['results']:
					print('version ' + item['version'] + '-' + item['release'] + ' is available on repository [' + item['repository'] + ']')
		except IndexError:
			if self.short_response:
				print('none')
			else:
				print('could not find any version for package ' + package_name)
		return

	def ask_the_oracle(self, version_one, version_two):
		# we don't know how to parse this, let's ask zypper
		if self.verbose:
			print('don''t know how to compare: %s and %s, let''s ask the oracle' % (version_one, version_two))
		proc = subprocess.Popen(["/usr/bin/zypper", "vcmp", str(version_one), str(version_two)], env={"LANG": "C"}, stdout=subprocess.PIPE)
		output, err = proc.communicate()
		regex = r".*is newer than.*"
		if output is not None:
			matches = re.match(regex, output.decode('utf-8'))
			if matches is not None:
				if self.verbose:
					print('the oracle says: %s is newer' % str(version_one) )
				return True
			else:
				if self.verbose:
					print('the oracle says: %s is older' % str(version_one) )
				return False


	def is_newer(self, version_one, version_two):
		result = False
		ver_regex=r"(.*)-(.*)"
		try:
			matches_v1 = re.match(ver_regex, version_one)
			matches_v2 = re.match(ver_regex, version_two)

			v1 = LooseVersion(matches_v1.group(1) + '-' + matches_v1.group(2))
			v2 = LooseVersion(matches_v2.group(1) + '-' + matches_v2.group(2))
		except (IndexError, AttributeError):
			return self.ask_the_oracle(version_one, version_two)

		try:
			result = v1.__ge__(v2)
		except TypeError as e:
			return self.ask_the_oracle(version_one, version_two)

		return result

	def check_supportconfig(self, supportconfigdir):

		self.sc_name = supportconfigdir.rstrip(os.sep).split(os.sep)[-1]
		if self.sc_name == '.':
			self.sc_name = os.getcwd().split(os.sep)[-1]

		print('Analyzing supportconfig directory: ' + supportconfigdir)
		
		if self.arch:
			match_arch = self.arch
		else:
			match_arch = self.find_arch(supportconfigdir)
		match_os = self.find_cpe(supportconfigdir, match_arch)
		match_suma = self.find_suma(supportconfigdir)
		selected_product_id = -1
		if match_os != -1 and match_arch != "unknown":
			print('product name = ' + self.product_list[match_os]['name'] + ' (id ' + str(match_os) + ', ' + match_arch + ')')
			selected_product_id = match_os
			base_regex = r"(^SUSE Linux Enterprise.*|^Basesystem.*)"	# primary repositories for trusted updates should have this regex
			if match_suma != -1:
				print('found ' + self.suma_product_list[match_suma]['name'] + ', will use alternate id ' + str(match_suma))
				selected_product_id = match_suma
				base_regex = r"^SUSE Manager.*"	# primary repositories for trusted updates should have this regex

		else:
			print('error while determining CPE')
			return ([],[],[],[])

		rpmlist = self.read_rpmlist(supportconfigdir)
		total = len(rpmlist)
		print('found ' + str(total) + ' total packages to check')
		
		count=0
		threads=[]
		# fetch results for all threads
		for chunk in self.list_chunk(rpmlist, self.max_threads):
			for p in chunk:
				threads.insert(count, PackageSearchEngine(count, selected_product_id, p[0], p[1], p[2]))
				threads[count].start()
				count+=1
			progress = '[' + str(count) + '/' + str(total) + ']'
			sys.stdout.write('processing ' + progress)
			blank = ('\b' * (len(progress) + 11))
			sys.stdout.write(blank)
			sys.stdout.flush()
			time.sleep(self.wait_time)

		print('gathering results...    ')
		for thread_number in range(count):
			threads[thread_number].join()
			refined_data = threads[thread_number].get_results()
			# print('refined data = ' + str(refined_data))
			try:
				target = self.product_list[match_os]
				ver_regex = r"cpe:/o:suse:(sles|sled|sles_sap):(\d+)"
				target_version = 'SUSE Linux Enterprise ' + re.match(ver_regex, target['identifier']).group(2)
				#print("package does not exist, target_version is " + target_version)
				#print("supplied distro for package " + str(refined_data['query']) + ' is ' + str(refined_data['supplied_distro']))
				#print("target identifier is " + target_version)
				if ( ('suse:sle' in str(target['identifier'])) and (str(refined_data['supplied_distro']) not in target_version)):
					self.unsupported.append([refined_data['query'], refined_data['supplied_distro'], refined_data['supplied_version']])
     
				if len(refined_data['results']) == 0:
					self.notfound.append([refined_data['query'], refined_data['supplied_distro'], refined_data['supplied_version']])
				else:
					latest = None
					for item in refined_data['results']:
						latest = item['version'] + '-' + item['release']
						selected_repo = item['repository']
						if (re.match(base_regex, item['repository']) is not None) and (self.is_newer(item['version'] + '-' + item['release'], refined_data['supplied_version'])):
							if self.verbose:
								print('---> found version %s-%s for package %s in repository %s which is a base repository, ignoring the rest' % (item['version'], item['release'], refined_data['query'], item['repository']))
							break
					if latest is None:
						latest = refined_data['results'][0]['version'] + '-' + refined_data['results'][0]['release']
						selected_repo = refined_data['results'][0]['repository']
					if self.verbose:
						print('latest version for ' + refined_data['query'] + ' on product ID ' + str(refined_data['product_id']) +  ' is ' + refined_data['results'][0]['version'] + '-' + refined_data['results'][0]['release'] + ' in repository ' + refined_data['results'][0]['repository'])
					#print('latest = ' + latest)        		
					if self.is_newer(latest, refined_data['supplied_version']) and (latest != refined_data['supplied_version']) :
						self.different.append([refined_data['query'], refined_data['supplied_version'], latest, selected_repo]) 
					else:
						self.uptodate.append([refined_data['query'], refined_data['supplied_version']]) 
						
			except IndexError:
				#print('[thread ' + str(thread_number) + '] could not find any version for package ' + refined_data['query'])
				pass

		sys.stdout.write('\nDone.\n')
		sys.stdout.flush()
		
		return (self.uptodate, self.unsupported, self.notfound, self.different)

	def write_reports(self):
		if len(self.uptodate) == 0:
			print ('no reports will be written (unsupported product?)')
			return
		else:
			print ('writing CSV reports to ' + self.outputdir + '\n')
			try:
				os.makedirs(self.outputdir, exist_ok=True)
			except OSError as e:
				print('error creating output directory at %s: %s' %(self.outputdir, str(e)))

			try:
				with open(self.outputdir + '/vercheck-uptodate-' + self.sc_name + '.csv', 'w') as f:
					for p, c in self.uptodate:
						f.write(p + ',' + c + '\n')
					f.close()
			except Exception as e:
				print('Error writing file: ' + str(e))
				return

			try:
				with open(self.outputdir + '/vercheck-notfound-' + self.sc_name + '.csv', 'w') as f:
					for p, d, c in self.notfound:
						f.write(p + ',' + d + ',' + c + '\n')
					f.close()
			except Exception as e:
				print('Error writing file: ' + str(e))
				return

			try:
				with open(self.outputdir + '/vercheck-unsupported-' + self.sc_name + '.csv', 'w') as f:
					for p, d, c in self.unsupported:
						f.write(p + ',' + d + ',' + c + '\n')
					f.close()
			except Exception as e:
				print('Error writing file: ' + str(e))
				return

			try:
				with open(self.outputdir + '/vercheck-different-' + self.sc_name + '.csv', 'w') as f:
					for p, c, l, r  in self.different:
						f.write(p + ',' + c + ',' + l + ',' + r + '\n')
					f.close()
			except Exception as e:
				print('Error writing file: ' + str(e))
				return
   
		field_size = 30
		if self.show_uptodate:
			print('\n\t\t---  Up-to-date packages ---\n')
			print(str.ljust('Name', field_size) + '\t' + str.ljust('Current Version', field_size))
			print('=' * 80)
			for p, c in self.uptodate:
					print(str.ljust(p, field_size) + '\t' + c)
			print('\nTotal: ' + str(len(self.uptodate)) + ' packages')

		if self.show_diff:
			print('\n\t\t---  Different packages ---\n')
			print(str.ljust('Name', field_size) + '\t' + str.ljust('Current Version', field_size) + '\t' + str.ljust('Latest Version', field_size) + '\t' + str.ljust('Repository', field_size))
			print('=' * 132)
			for p, c, l, r  in self.different:
					print(str.ljust(p, field_size) + '\t' + str.ljust(c, field_size) + '\t' + str.ljust(l, field_size) + '\t' + str.ljust(r, field_size))
			print('\nTotal: ' + str(len(self.different)) + ' packages')

		if self.show_unsupported:
			print('\n\t\t---  Unsupported packages ---\n')
			print(str.ljust('Name', field_size) + '\t' + str.ljust('Vendor', field_size) + '\t' + str.ljust('Current Version', field_size))
			print('=' * 80)
			for p, c, l  in self.unsupported:
					print(str.ljust(p, field_size) + '\t' + str.ljust(c, field_size) + '\t' + str.ljust(l, field_size))
			print('\nTotal: ' + str(len(self.unsupported)) + ' packages')
   
		if self.show_unknown:
			print('\n\t\t--- Unknown packages ---\n')
			print(str.ljust('Name', field_size) + '\t' + str.ljust('Vendor', field_size) + '\t' + str.ljust('Current Version', field_size))
			print('=' * 80)
			for p, c, l  in self.notfound:
					print(str.ljust(p, field_size) + '\t' + str.ljust(c, field_size) + '\t' + str.ljust(l, field_size))
			print('\nTotal: ' + str(len(self.notfound)) + ' packages')

		return


### separate class instantiated by each thread, does a search and posts results
class PackageSearchEngine(Thread):

	# number of concurrent threads
	max_threads = 20

	# single instance for urllib3 pool
	http = urllib3.PoolManager(maxsize=max_threads)
  
	# set default socket options
	# HTTPConnection.default_socket_options += [ (socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) ]
	# HTTPConnection.debuglevel = 15
 
	# maximum retries for each thread
	max_tries = 5

	# server replies which are temporary errors (and can be retried)
	retry_states = [ 429, 502, 504 ]

	# server replies which are permanent errors (and cannot be retried)
	error_states = [ 400, 403, 404, 422, 500 ]

	results = {}

	def __init__(self, instance_nr, product_id, package_name, supplied_distro, supplied_version):
		super(PackageSearchEngine, self).__init__() 
		urllib3.disable_warnings()
		self.instance_nr = instance_nr
		self.product_id = product_id
		self.package_name = package_name
		self.supplied_distro = supplied_distro
		self.supplied_version = supplied_version

	def mySort(self, e):
     
		v = e['version']
		try:
			real_v = re.match(r"(.*)\+[a-zA-Z].*\-", v).group(1)
			v = real_v
		except (IndexError, AttributeError):
			pass

		if e['release'][0].isalpha():
			r = e['release'][e['release'].index('.')+1:]
		else:
			r = e['release']
		#print('release %s will be considered as %s' % (e['release'], release))
		return LooseVersion(v + '-' + r)

	def get_results(self):
		return { 'product_id': self.product_id, 'query': self.package_name, 'supplied_distro': self.supplied_distro, 'supplied_version': self.supplied_version, 'results': self.results }

	def run(self):
		#print('[Thread ' + str(self.instance_nr) + '] looking for ' + self.package_name + ' on product id ' + str(self.product_id))
		tries = 0
		valid_response = False
		return_data = []
		while not valid_response and tries < self.max_tries:
			try:
				r = self.http.request('GET', 'https://scc.suse.com/api/package_search/packages?product_id=' + str(self.product_id) + '&query=' + urllib.parse.quote(self.package_name), headers={'Accept-Encoding': 'gzip, deflate', 'Connection':'close'})
			except Exception as e:
				print('Error while connecting: ' + str(e))
				exit(1)

			return_data = {}

			if r.status == 200:
				if tries > 0:
					print('thread %d got a good reply after %d tries' % (self.instance_nr, tries))
				return_data = json.loads(r.data.decode('utf-8'))
				valid_response = True
			elif r.status in self.error_states:
				if r.data:
					json_data = json.loads(r.data.decode('utf-8'))
					print('cannot be processed due to error: [' + json_data['error'] + ']')
				print('thread %d got a fatal error (%d). Results will be incomplete!\nPlease contact the service administrators or try again later.' % (self.instance_nr, r.status))
				break
			elif r.status in self.retry_states:
				print('thread %d got non-fatal reply (%d) from server, trying again in 2 seconds ' % (self.instance_nr, r.status))
				time.sleep(2)
				tries = tries + 1
				continue
			else:
				print('got unknown error %d from the server!' % r.status)

		refined_data = []

		if return_data:
			for item in return_data['data']:
				# discard items that do not match exactly our query
				#print(str(item))
				if item['name'] != self.package_name:
					continue
				else:
					#print('products for item: ' + str(item['products']))
					for product in item['products']:
						#print(str(product))
						refined_data.append({'id':item['id'], 'version':item['version'], 'release': item['release'], 'repository': product['name'] + ' ' + product['edition'] + ' ' +  product['architecture']})
						#print('added result: ' + item['name'] + ' ' + item['version'] + '-' + item['release'])

		try:
			refined_data.sort(reverse=True, key=self.mySort)
		except TypeError as e:
			# sometimes the version is so wildly mixed with letters that the sorter gets confused
			# but it's okay to ignore this
			#print('*** warning: sorting error due to strange version (may be ignored): ' + str(e))
			pass

		#print('refined data size: ' + str(len(refined_data)))  
		self.results = refined_data
		return


#### main program
def main():
	sv = SCCVersion()
	signal.signal(signal.SIGINT, sv.cleanup)

	try:
		opts,args = getopt.getopt(sys.argv[1:],  "hp:n:lsvt1234a:d:o:", [ "help", "product=", "name=", "list-products", "short", "verbose", "test", "show-unknown", "show-differences", "show-uptodate", "show-unsupported", "arch=", "supportconfig=", "outputdir=" ])
	except getopt.GetoptError as err:
		print(err)
		sv.usage()
		exit(2)

	product_id = -1
	package_name = ''
	short_response = False
	global show_unknown, show_diff, show_uptodate, show_unsupported
	global uptodate, different, notfound, unsupported

	for o, a in opts:
		if o in ("-h", "--help"):
			sv.show_help()
			exit(1)
		elif o in ("-a", "--arch"):
			sv.arch = a
		elif o in ("-s", "--short"):
			sv.short_response = True
		elif o in ("-p", "--product"):
			product_id = int(a)
		elif o in ("-n", "--name"):
			package_name = a
		elif o in ("-l", "--list-products"):
			sv.list_products()
			exit(0)
		elif o in ("-1", "--show-unknown"):
			sv.show_unknown = True
		elif o in ("-2", "--show-differences"):
			sv.show_diff = True
		elif o in ("-3", "--show-uptodate"):
			sv.show_uptodate = True
		elif o in ("-4", "--show-unsupported"):
			sv.show_unsupported = True
		elif o in ("-v", "--verbose"):
			sv.set_verbose(True)
		elif o in ("-t", "--test"):
			sv.test()
			exit(0)
		elif o in ("-o", "--outputdir"):
			sv.set_outputdir(a)
		elif o in ("-d", "--supportconfig"):
			supportconfigdir = a
			uptodate, unsupported, notfound, different = sv.check_supportconfig(supportconfigdir)
			sv.write_reports()
			exit(0)
		else:
			assert False, "invalid option"

	if product_id == -1 or package_name is '':
		print('Please specify a product ID and package name.')
		sv.usage()
		exit(2)

	if product_id in sv.suma_product_list:
		plist = sv.suma_product_list
	else:
		plist = sv.product_list
  
	if product_id not in plist:
		print ('Product ID ' + str(product_id) + ' is unknown.')
	else:
		if sv.verbose:
			print ('Using product ID ' + str(product_id) +  ' ('  + plist[product_id]['name'] + ')')
	
	sv.search_package(product_id, package_name)

	return

if __name__ == "__main__":
	main()