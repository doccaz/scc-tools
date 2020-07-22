#!/usr/bin/python3
import re
import sys
import urllib3
import json
import getopt
from distutils.version import LooseVersion

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
	
# single instance for urllib3 pool
http = urllib3.PoolManager()

def find_cpe(directory_name, architecture):
	regex = r"CPE_NAME=\"(.*)\""
	
	try:
		f = open(directory_name + '/basic-environment.txt', 'r')
		text = f.read()
		f.close()
		matches = re.search(regex, text)
		for p in product_list:
			if matches.group(1) == product_list[p]['identifier'] and architecture == product_list[p]['arch']:
				return p
	except Exception as e:
		print ('error: ' + str(e))
	return -1

def find_arch(directory_name):
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

def read_rpmlist(directory_name):
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

def mySort(e):
	return LooseVersion(e['version'] + '-' + e['release'])

def search_package(product_id, package_name, verbose):
	if verbose:
		print('looking for ' + package_name + ' on product id ' + str(product_id))

	urllib3.disable_warnings()

	try:
		r = http.request('GET', 'https://scc.suse.com/api/package_search/packages?product_id=' + str(product_id) + '&query=' + package_name, headers={'Accept-Encoding': 'gzip, deflate'})
	except Exception as e:
		print('Error while connecting: ' + str(e))
		exit(1)

	return_data = {}

	if r.status == 200:
		return_data = json.loads(r.data)
	elif r.status == 422:
		json_data = json.loads(r.data)
		print('cannot be processed due to error: [' + json_data['error'] + ']')
	elif verbose:
		print('got error ' + str(r.status) + ' from the server!')

	refined_data = []

	if return_data:
		for item in return_data['data']:
			# discard items that do not match exactly our query
			#print(str(item))
			if item['name'] != package_name:
				continue
			else:
				#print('products for item: ' + str(item['products']))
				for product in item['products']:
					#print(str(product))
					if verbose:
						print('version ' + item['version'] + '-' + item['release'] + ' is available on repository [' + product['name'] + ' ' + product['edition'] + ' ' +  product['architecture'] + ']')
					refined_data.append({'id':item['id'], 'version':item['version'], 'release': item['release']})
					#print('added result: ' + item['name'] + ' ' + item['version'] + '-' + item['release'])

	try:	
		refined_data.sort(reverse=True, key=mySort)
	except TypeError as e:
		# sometimes the version is so wildly mixed with letters that the sorter gets confused
		# but it's okay to ignore this
		# print('warning: sorting error due to strange version (may be ignored): ' + str(e))
		pass

	#print('refined data size: ' + str(len(refined_data)))
	return refined_data

def list_products():
	print('Known products list')
	print('ID	Name')
	print('-----------------------------------------------------')
	for k, v in product_list.items():
		print(str(k) + '\t' + v['name'])

	print('total: ' + str(len(product_list)) +  ' products.')
	return

def usage():
	print('Usage: ' + sys.argv[0] + ' [-l|--list-products] -p|--product product id -n|--name <package name> [-s|--short] [-v|--verbose] [-1|--show-unknown] [-2|--show-differences] [-3|--show-uptodate] [-d|--supportconfig]')
	return

def show_help():
	usage()	
	print('\n')
	print('-l|--list-products\t\tLists all supported products. Use this to get a valid product ID for further queries.\n')
	print('-p|--product <product id>\tSpecifies a valid product ID for queries. Mandatory for searches.\n')
	print('-n|--name <package name>\tSpecifies a package name to search. Exact matches only for now. Mandatory for searches.\n')
	print('-s|--short\t\t\tOnly outputs the latest version, useful for scripts\n')
	print('-v|--verbose\t\t\tOutputs extra information about the search and results\n')
	print('-1|--show-unknown: shows unknown packages as they are found.\n')
	print('-2|--show-differences): shows packages that have updates available as they are found.\n')
	print('-3|--show-uptodate): shows packages that are on par with the updated versions as they are found.\n')
	print('-d|--supportconfig\t\tAnalyzes a supportconfig directory and generates CSV reports for up-to-date, not found and different packages.')
	print('\n')
	return

def test():
	package_name = 'glibc'
	for k, v in product_list.items():
		print('searching for package \"glibc\" in product id \"' + str(k) + '\" (' + v['name'] + ')')
		refined_data = search_package(k, package_name, True)
		try:
			print('latest version for ' + package_name + ' is ' + refined_data[0]['version'] + '-' + refined_data[0]['release'])
		except IndexError:
			print('could not find any version for package ' + package_name)

	return

def check_supportconfig(supportconfigdir, show_unknown, show_diff, show_uptodate):

	uptodate = []
	notfound = []
	different = []

	print('Analyzing supportconfig directory: ' + supportconfigdir)

	match_arch = find_arch(supportconfigdir)
	match_os = find_cpe(supportconfigdir, match_arch)
	if match_os != -1 and match_arch != "unknown":
		print('product name = ' + product_list[match_os]['name'] + ' (id ' + str(match_os) + ', ' + match_arch + ')')
	else:
		print('error while determining CPE')
		return ([],[],[])

	rpmlist = read_rpmlist(supportconfigdir)
	total = len(rpmlist)
	print('found ' + str(total) + ' total packages to check')
	
	count=1
	for p in rpmlist:
		refined_data = search_package(match_os, p[0], False)
		#print('refined data = ' + str(refined_data))
		progress = '[' + str(count) + '/' + str(total) + ']'
		sys.stdout.write('processing ' + progress)
		blank = ('\b' * (len(progress) + 11))

		if len(refined_data) == 0:
			if show_unknown:
				sys.stdout.write('\n' + p[0] + ': not found\n')		
			notfound.append([p[0], p[1]])
		else:
			latest = refined_data[0]['version'] + '-' + refined_data[0]['release']
			#print('latest = ' + latest)
		
			if latest != p[1]:
				if show_diff:
					sys.stdout.write('\n' + p[0] + ': current version is ' + p[1] + ' (latest: ' + latest + ')\n')
				different.append([p[0], p[1], latest]) 
			else:
				if show_uptodate:
					sys.stdout.write('\n' + p[0] + ': up-to-date (' + latest + ')\n')
				uptodate.append([p[0], p[1]]) 

		count+=1
		sys.stdout.write(blank)
		sys.stdout.flush()
	sys.stdout.write('\nDone.\n')
	sys.stdout.flush()
	
	return (uptodate, notfound, different)

def write_reports(uptodate, notfound, different):
	print('up-to-date:' + str(len(uptodate)) + ' packages')
	try:	
		with open('uptodate.csv', 'w') as f:
			for p, c in uptodate:
				f.write(p + ',' + c + '\n')
			f.close()
	except Exception as e:
		print('Error writing file: ' + str(e))
		return
	
	print('not found:' + str(len(notfound)) + ' packages')
	try:	
		with open('notfound.csv', 'w') as f:
			for p, c in notfound:
				f.write(p + ',' + c + '\n')
			f.close()
	except Exception as e:
		print('Error writing file: ' + str(e))
		return

	print('different:' + str(len(different)) + ' packages')
	try:	
		with open('different.csv', 'w') as f:
			for p, c, l  in different:
				f.write(p + ',' + c + ',' + l + '\n')
			f.close()
	except Exception as e:
		print('Error writing file: ' + str(e))
		return

	return

#### main program
def main():
	try:
		opts,args = getopt.getopt(sys.argv[1:],  "hp:n:lsvt123d:", [ "help", "product=", "name=", "list-products", "short", "verbose", "test", "show-unknown", "show-differences", "show-uptodate", "supportconfig=" ])
	except getopt.GetoptError as err:
		print(err)
		usage()
		exit(2)

	product_id = -1
	package_name = ''
	short_response = False
	verbose = False
	show_unknown = False
	show_diff = False
	show_uptodate = False

	for o, a in opts:
		if o in ("-h", "--help"):
			show_help()
			exit(1)
		elif o in ("-s", "--short"):
			short_response = True
		elif o in ("-p", "--product"):
			product_id = int(a)
		elif o in ("-n", "--name"):
			package_name = a
		elif o in ("-l", "--list-products"):
			list_products()
			exit(0)
		elif o in ("-1", "--show-unknown"):
			show_unknown = True
		elif o in ("-2", "--show-differences"):
			show_diff = True
		elif o in ("-3", "--show-uptodate"):
			show_uptodate = True
		elif o in ("-v", "--verbose"):
			verbose = True
		elif o in ("-t", "--test"):
			test()
			exit(0)
		elif o in ("-d", "--supportconfig"):
			supportconfigdir = a
			uptodate, notfound, different = check_supportconfig(supportconfigdir,  show_unknown, show_diff, show_uptodate)
			write_reports(uptodate, notfound, different)
			exit(0)
		else:
			assert False, "invalid option"

	if product_id == -1 or package_name is '':
		print('Please specify a product ID and package name.')
		usage()
		exit(2)

	if product_id not in product_list:
		print ('Product ID ' + str(product_id) + ' is unknown.')
	else:
		if verbose:
			print ('Using product ID ' + str(product_id) +  ' ('  + product_list[product_id]['name'] + ')')
	
	refined_data = search_package(product_id, package_name, verbose)

	try:
		if short_response:
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
