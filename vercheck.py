#!/usr/bin/python3
import re
import sys
import urllib3
import json
import getopt
from distutils.version import LooseVersion

# static product list (taken from RMT and other sources)
product_list = {
	1117: { 'name': 'SUSE Linux Enterprise Server 12 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles:12' },
	1118: { 'name': 'SUSE Linux Enterprise Desktop 12 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sled:12' },
	1322: { 'name': 'SUSE Linux Enterprise Server 12 SP1 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles:12:sp1' },
	1333: { 'name': 'SUSE Linux Enterprise Desktop 12 SP1 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sled:12:sp1' },
	1357: { 'name': 'SUSE Linux Enterprise Server 12 SP2 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles:12:sp2' },
	1358: { 'name': 'SUSE Linux Enterprise Desktop 12 SP2 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sled:12:sp2' },
	1421: { 'name': 'SUSE Linux Enterprise Server 12 SP3 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles:12:sp3' },
	1425: { 'name': 'SUSE Linux Enterprise Desktop 12 SP3 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sled:12:sp3' },
	1625: { 'name': 'SUSE Linux Enterprise Server 12 SP4 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles:12:sp4' },
	1629: { 'name': 'SUSE Linux Enterprise Desktop 12 SP4 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sled:12:sp4' },
	1878: { 'name': 'SUSE Linux Enterprise Server 12 SP5 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles:12:sp5' },
	1319: { 'name': 'SUSE Linux Enterprise Server for SAP 12 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles:12' },
	1346: { 'name': 'SUSE Linux Enterprise Server for SAP 12 SP1 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles_sap:12:sp1' },
	1414: { 'name': 'SUSE Linux Enterprise Server for SAP 12 SP2 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles_sap:12:sp2' },
	1426: { 'name': 'SUSE Linux Enterprise Server for SAP 12 SP3 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles_sap:12:sp3' },
	1755: { 'name': 'SUSE Linux Enterprise Server for SAP 12 SP4 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles_sap:12:sp4' },
	1880: { 'name': 'SUSE Linux Enterprise Server for SAP 12 SP5 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles_sap:12:sp5' },
	1575: { 'name': 'SUSE Linux Enterprise Server 15 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles:15' },
	1609: { 'name': 'SUSE Linux Enterprise Desktop 15 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sled:15' },
	1763: { 'name': 'SUSE Linux Enterprise Server 15 SP1 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles:15:sp1' },
	1764: { 'name': 'SUSE Linux Enterprise Desktop 15 SP1 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sled:15:sp1' },
	1939: { 'name': 'SUSE Linux Enterprise Server 15 SP2 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles:15:sp2' },
	1935: { 'name': 'SUSE Linux Enterprise Desktop 15 SP2 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sled:15:sp2' },
	1612: { 'name': 'SUSE Linux Enterprise Server for SAP 15 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles_sap:15' },
	1766: { 'name': 'SUSE Linux Enterprise Server for SAP 15 SP1 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles_sap:15:sp1' },
	1941: { 'name': 'SUSE Linux Enterprise Server for SAP 15 SP2 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles_sap:15:sp2' },
}
	
# single instance for urllib3 pool
http = urllib3.PoolManager()

def find_cpe(directory_name):
	regex = r"CPE_NAME=\"(.*)\""
	
	try:
		f = open(directory_name + '/basic-environment.txt', 'r')
		text = f.read()
		f.close()

		matches = re.search(regex, text)
		for p in product_list:
			if matches.group(1) == product_list[p]['identifier']:
				return p
	except Exception as e:
		print ('error: ' + str(e))
	return -1

def read_rpmlist(directory_name):
	rpmlist = []
	regex_start = r"(^NAME.*VERSION)\n"
	regex_package = r"(\S*).*\s([0-9].*)"
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

	if verbose is True:
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

	try:	
		refined_data.sort(reverse=True, key=mySort)
	except TypeError as e:
		print('wrong version format: ' + str(e))

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
	print('Usage: ' + sys.argv[0] + ' [-l|--list-products] -p|--product=product id -n|--name <package name> [-s|--short] [-v|--verbose]')
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

def check_supportconfig(supportconfigdir):

	uptodate = []
	notfound = []
	different = []

	match_os = find_cpe(supportconfigdir)
	if match_os != -1:
		print('product name = ' + product_list[match_os]['name'])
	else:
		print('error while determining CPE')
		return ([],[],[])

	rpmlist = read_rpmlist(supportconfigdir)
	total = len(rpmlist)
	print('found ' + str(total) + ' total packages to check')
	
	count=1
	for p in rpmlist:
		refined_data = search_package(match_os, p[0], False)
		try:
			latest = refined_data[0]['version'] + '-' + refined_data[1]['release']
			if latest != p[1]:
				print('[' + str(count) + '/' + str(total) + '] ' + p[0] + ': latest version is ' + latest + ' (current: ' + p[1] + ')')
				different.append([p[0], p[1], latest]) 
			else:
				print('[' + str(count) + '/' + str(total) + '] ' + p[0] + ': up-to-date')
				uptodate.append([p[0], p[1]]) 

		except IndexError:
			print('[' + str(count) + '/' + str(total) + '] ' + p[0] + ': not found')
			notfound.append(p[0])
		count+=1
	return (uptodate, notfound, different)

#### main program
def main():

	try:
		opts,args = getopt.getopt(sys.argv[1:],  "hp:n:lsvtd:", [ "help", "product=", "name=", "list-products", "short", "verbose", "test", "supportconfig=" ])
	except getopt.GetoptError as err:
		print(err)
		usage()
		exit(2)

	product_id = -1
	package_name = ''
	short_response = False
	verbose = False
	for o, a in opts:
		if o in ("-h", "--help"):
			usage()
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
		elif o in ("-d", "--supportconfig"):
			supportconfigdir = a
			uptodate, notfound, different = check_supportconfig(supportconfigdir)

			exit(0)

		elif o in ("-v", "--verbose"):
			verbose = True
		elif o in ("-t", "--test"):
			test()
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
		if verbose is True:
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

