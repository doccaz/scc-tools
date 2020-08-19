#!/usr/bin/python3
import re
import sys, os, time
from threading import Thread
import urllib3
import json
import getopt
import signal
from distutils.version import LooseVersion

### main class that deals with command lines, reports and everything else
class SCCVersion():

	# static product list (taken from RMT and other sources)
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
		1319: { 'name': 'SUSE Linux Enterprise Server for SAP Applications 12 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles:12' },
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
		1612: { 'name': 'SUSE Linux Enterprise Server for SAP 15 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles_sap:15' },
		1613: { 'name': 'SUSE Linux Enterprise Server for SAP Applications 15 ppc64le', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles_sap:15' },
		1765: { 'name': 'SUSE Linux Enterprise Server for SAP Applications 15 SP1 ppc64le', 'arch': 'ppc64le', 'identifier': 'cpe:/o:suse:sles_sap:15:sp1' },
		1766: { 'name': 'SUSE Linux Enterprise Server for SAP Applications 15 SP1 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles_sap:15:sp1' },
		1940: { 'name': 'SUSE Linux Enterprise Server for SAP 15 SP2 ppc64le', 'arch': 'ppc64le', 'identifier': 'cpe:/o:suse:sles_sap:15:sp2' },
		1941: { 'name': 'SUSE Linux Enterprise Server for SAP 15 SP2 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles_sap:15:sp2' },
	}


	# result lists
	uptodate = []
	notfound = []
	different = []

	# report flags
	show_unknown = False
	show_diff = False
	show_uptodate = False

	# verbose messages
	verbose = False

	# base name for the reports
	sc_name = ''

	# maximum number of running threads
	max_threads = 10

	# time to wait before starting each chunk of threads
	wait_time = 1

	def set_verbose(self, verbose):
		self.verbose = verbose

	def cleanup(self, signalNumber, frame):
		print('\nokay, okay, I\'m leaving!')
		self.write_reports()
		sys.exit(0)
		return

	def find_cpe(self, directory_name, architecture):
		regex = r"CPE_NAME=\"(.*)\""
		
		try:
			f = open(directory_name + '/basic-environment.txt', 'r')
			text = f.read()
			f.close()
			matches = re.search(regex, text)
			for p in self.product_list:
				if matches.group(1) == self.product_list[p]['identifier'] and architecture == self.product_list[p]['arch']:
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
			print ('error: ' + str(e))
		return 'unknown'

	def read_rpmlist(self, directory_name):
		rpmlist = []
		regex_start = r"(^NAME.*VERSION)\n"
		regex_package = r"(\S*)\s{2,}\S.*\s{2,}(.*)"
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
						rpmversion = matches.group(2)
						if rpmname.startswith('gpg-pubkey'):
							continue
						if rpmname != '' and rpmversion != '':
							rpmlist.append([rpmname, rpmversion])
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
		print('Usage: ' + sys.argv[0] + ' [-l|--list-products] -p|--product product id -n|--name <package name> [-s|--short] [-v|--verbose] [-1|--show-unknown] [-2|--show-differences] [-3|--show-uptodate] [-d|--supportconfig]')
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
		print('-d|--supportconfig\t\tAnalyzes a supportconfig directory and generates CSV reports for up-to-date, not found and different packages.')
		print('\n')
		return

	def test(self):
		threads = []
		package_name = 'glibc'
		instance_nr = 0

		for k, v in self.product_list.items():
			print('searching for package \"glibc\" in product id \"' + str(k) + '\" (' + v['name'] + ')')
			threads.insert(instance_nr, PackageSearchEngine(instance_nr, k, package_name, '0'))
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

	def check_supportconfig(self, supportconfigdir):

		global sc_name

		sc_name = supportconfigdir.split(os.sep)[-1]
		if sc_name == '.':
			sc_name = os.getcwd().split(os.sep)[-1]

		print('Analyzing supportconfig directory: ' + supportconfigdir)
		
		match_arch = self.find_arch(supportconfigdir)
		match_os = self.find_cpe(supportconfigdir, match_arch)
		if match_os != -1 and match_arch != "unknown":
			print('product name = ' + self.product_list[match_os]['name'] + ' (id ' + str(match_os) + ', ' + match_arch + ')')
		else:
			print('error while determining CPE')
			return ([],[],[])

		rpmlist = self.read_rpmlist(supportconfigdir)
		total = len(rpmlist)
		print('found ' + str(total) + ' total packages to check')
		
		count=0
		threads=[]
		# fetch results for all threads
		for chunk in self.list_chunk(rpmlist, self.max_threads):
			for p in chunk:
				threads.insert(count, PackageSearchEngine(count, match_os, p[0], p[1]))
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
			#print('refined data = ' + str(refined_data))
			try:
				if self.verbose:
					print('latest version for ' + refined_data['query'] + ' on product ID ' + str(refined_data['product_id']) +  ' is ' + refined_data['results'][0]['version'] + '-' + refined_data['results'][0]['release'])
				if len(refined_data['results']) == 0:
					self.notfound.append([refined_data['query'], refined_data['supplied_version']])
				else:
					latest = refined_data['results'][0]['version'] + '-' + refined_data['results'][0]['release']
					#print('latest = ' + latest)
				
					if latest != refined_data['supplied_version']:
						self.different.append([refined_data['query'], refined_data['supplied_version'], latest]) 
					else:
						self.uptodate.append([refined_data['query'], refined_data['supplied_version']]) 
			except IndexError:
				#print('[thread ' + str(thread_number) + '] could not find any version for package ' + refined_data['query'])
				pass

		sys.stdout.write('\nDone.\n')
		sys.stdout.flush()
		
		return (self.uptodate, self.notfound, self.different)

	def write_reports(self):
		print ('writing CSV reports to ' + os.getcwd() + '\n')
		try:	
			with open('vercheck-uptodate-' + sc_name + '.csv', 'w') as f:
				for p, c in self.uptodate:
					f.write(p + ',' + c + '\n')
				f.close()
		except Exception as e:
			print('Error writing file: ' + str(e))
			return
		
		try:	
			with open('vercheck-notfound-' + sc_name + '.csv', 'w') as f:
				for p, c in self.notfound:
					f.write(p + ',' + c + '\n')
				f.close()
		except Exception as e:
			print('Error writing file: ' + str(e))
			return

		try:	
			with open('vercheck-different-' + sc_name + '.csv', 'w') as f:
				for p, c, l  in self.different:
					f.write(p + ',' + c + ',' + l + '\n')
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
			print(str.ljust('Name', field_size) + '\t' + str.ljust('Current Version', field_size) + '\t' + str.ljust('Latest Version', field_size))
			print('=' * 80)
			for p, c, l  in self.different:
					print(str.ljust(p, field_size) + '\t' + str.ljust(c, field_size) + '\t' + str.ljust(l, field_size))
			print('\nTotal: ' + str(len(self.different)) + ' packages')

		if self.show_unknown:
			print('\n\t\t--- Unknown packages ---\n')
			print(str.ljust('Name', field_size) + '\t' + str.ljust('Current Version', field_size))
			print('=' * 80)
			for p, c  in self.notfound:
					print(str.ljust(p, 30) + '\t' + c)	
			print('\nTotal: ' + str(len(self.notfound)) + ' packages')
		return


### separate class instantiated by each thread, does a search and posts results
class PackageSearchEngine(Thread):

	# number of concurrent threads
	max_threads = 5

	# single instance for urllib3 pool
	http = urllib3.PoolManager(maxsize=max_threads)

	results = {}

	def __init__(self, instance_nr, product_id, package_name, supplied_version):
		super(PackageSearchEngine, self).__init__()
		urllib3.disable_warnings()
		self.instance_nr = instance_nr
		self.product_id = product_id
		self.package_name = package_name
		self.supplied_version = supplied_version
	
	def mySort(self, e):
		return LooseVersion(e['version'] + '-' + e['release'])

	def get_results(self):
		return { 'product_id': self.product_id, 'query': self.package_name, 'supplied_version': self.supplied_version, 'results': self.results }

	def run(self):
		#print('[Thread ' + str(self.instance_nr) + '] looking for ' + self.package_name + ' on product id ' + str(self.product_id))

		try:
			r = self.http.request('GET', 'https://scc.suse.com/api/package_search/packages?product_id=' + str(self.product_id) + '&query=' + self.package_name, headers={'Accept-Encoding': 'gzip, deflate'})
		except Exception as e:
			print('Error while connecting: ' + str(e))
			exit(1)

		return_data = {}

		if r.status == 200:
			return_data = json.loads(r.data)
		elif r.status == 422:
			json_data = json.loads(r.data)
			print('cannot be processed due to error: [' + json_data['error'] + ']')
		else:
			print('got error ' + str(r.status) + ' from the server!')

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
			# print('warning: sorting error due to strange version (may be ignored): ' + str(e))
			pass

		#print('refined data size: ' + str(len(refined_data)))
		self.results = refined_data
		return



#### main program
def main():


	sv = SCCVersion()
	signal.signal(signal.SIGINT, sv.cleanup)

	try:
		opts,args = getopt.getopt(sys.argv[1:],  "hp:n:lsvt123d:", [ "help", "product=", "name=", "list-products", "short", "verbose", "test", "show-unknown", "show-differences", "show-uptodate", "supportconfig=" ])
	except getopt.GetoptError as err:
		print(err)
		sv.usage()
		exit(2)

	product_id = -1
	package_name = ''
	short_response = False
	global show_unknown, show_diff, show_uptodate
	global uptodate, different, notfound

	for o, a in opts:
		if o in ("-h", "--help"):
			sv.show_help()
			exit(1)
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
		elif o in ("-v", "--verbose"):
			sv.set_verbose(True)
		elif o in ("-t", "--test"):
			sv.test()
			exit(0)
		elif o in ("-d", "--supportconfig"):
			supportconfigdir = a
			uptodate, notfound, different = sv.check_supportconfig(supportconfigdir)
			sv.write_reports()
			exit(0)
		else:
			assert False, "invalid option"

	if product_id == -1 or package_name is '':
		print('Please specify a product ID and package name.')
		sv.usage()
		exit(2)

	if product_id not in product_list:
		print ('Product ID ' + str(product_id) + ' is unknown.')
	else:
		if sv.verbose:
			print ('Using product ID ' + str(product_id) +  ' ('  + product_list[product_id]['name'] + ')')
	
	refined_data = search_package(product_id, package_name, verbose)

	try:
		if sv.short_response:
			print(refined_data[0]['version'] + '-' + refined_data[0]['release'])
		else:
			print('latest version for ' + package_name + ' is ' + refined_data[0]['version'] + '-' + refined_data[0]['release'])
	except IndexError:
		if short_response:
			print('none')
		else:
			print('could not find any version for package ' + package_name)
		exit(1)

	return


if __name__ == "__main__":
	main()
