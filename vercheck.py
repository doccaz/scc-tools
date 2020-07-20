#!/usr/bin/python3
import sys
import urllib3
import json
import collections
import getopt

# static product list (taken from RMT and other sources)
product_list = {
	1117: { 'name': 'SUSE Linux Enterprise Server 12 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles:12' },
	1322: { 'name': 'SUSE Linux Enterprise Server 12 SP1 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles:12:sp1' },
	1357: { 'name': 'SUSE Linux Enterprise Server 12 SP2 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles:12:sp2' },
	1421: { 'name': 'SUSE Linux Enterprise Server 12 SP3 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles:12:sp3' },
	1625: { 'name': 'SUSE Linux Enterprise Server 12 SP4 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles:12:sp4' },
	1878: { 'name': 'SUSE Linux Enterprise Server 12 SP5 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles:12:sp5' },
	1319: { 'name': 'SUSE Linux Enterprise Server for SAP 12 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles:12' },
	1346: { 'name': 'SUSE Linux Enterprise Server for SAP 12 SP1 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles_sap:12:sp1' },
	1414: { 'name': 'SUSE Linux Enterprise Server for SAP 12 SP2 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles_sap:12:sp2' },
	1426: { 'name': 'SUSE Linux Enterprise Server for SAP 12 SP3 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles_sap:12:sp3' },
	1755: { 'name': 'SUSE Linux Enterprise Server for SAP 12 SP4 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles_sap:12:sp4' },
	1880: { 'name': 'SUSE Linux Enterprise Server for SAP 12 SP5 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles_sap:12:sp5' },
	1575: { 'name': 'SUSE Linux Enterprise Server 15 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles:15' },
	1763: { 'name': 'SUSE Linux Enterprise Server 15 SP1 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles:15:sp1' },
	1939: { 'name': 'SUSE Linux Enterprise Server 15 SP2 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles:15:sp2' },
	1612: { 'name': 'SUSE Linux Enterprise Server for SAP 15 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles_sap:15' },
	1766: { 'name': 'SUSE Linux Enterprise Server for SAP 15 SP1 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles_sap:15:sp1' },
	1941: { 'name': 'SUSE Linux Enterprise Server for SAP 15 SP2 x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles_sap:15:sp2' },
	2117: { 'name': 'SUSE Linux Enterprise Server 12 LTSS x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles:12:sp5' },
	2056: { 'name': 'SUSE Linux Enterprise Server 15 LTSS x86_64', 'arch': 'x86_64', 'identifier': 'cpe:/o:suse:sles:15:sp5' }
}

def mySort(e):
	return e['id']


def search_package(product_id, package_name, verbose):

	if verbose is True:
		print('looking for ' + package_name + ' on product id ' + str(product_id))

	http = urllib3.PoolManager()
	urllib3.disable_warnings()

	try:
		r = http.request('GET', 'https://scc.suse.com/api/package_search/packages?product_id=' + str(product_id) + '&query=' + package_name, headers={'Accept-Encoding': 'gzip, deflate'})
	except Exception as e:
		print('Error while connecting: ' + str(e))
		exit(1)

	return_data = {}

	if r.status == 200:
		return_data = json.loads(r.data)

	return return_data

def list_products():
	print('Known products list')
	print('ID	Name')
	print('-----------------------------------------------------')
	for k, v in product_list.items():
		print(str(k) + '\t' + v['name'])

	print('total: ' + str(len(product_list)) +  ' products.')
	return

def usage():
	print('Usage: ' + sys.argv[0] + ' [-l|--list-products] -p|--product=product id -n|--name <package name>')
	return

def test():
	for k, v in product_list.items():
		print('searching for package \"glibc\" in product id \"' + str(k) + '\" (' + v['name'] + ')')

	return

#### main program
def main():

	try:
		opts,args = getopt.getopt(sys.argv[1:],  "hp:n:lsv", [ "help", "product=", "name=", "list-products", "short", "verbose" ])
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
		elif o in ("-v", "--verbose"):
			verbose = True
		else:
			assert False, "invalid option"


	if product_id == -1 or package_name is '':
		print('Please specify a product ID and package name.')
		usage()
		exit(2)

	if product_id not in product_list:
		print ('Product ID ' + str(product_id) + ' is unknown.')
		exit(1)
	else:
		if verbose is True:
			print ('Using product ID ' + str(product_id) +  ' ('  + product_list[product_id]['name'] + ')')

	return_data = search_package(product_id, package_name, verbose)

	refined_data = []

	if return_data:
		for item in return_data['data']:
			# discard items that do not match exactly our query
			if item['name'] != package_name:
				continue
			else:
				#print('products for item: ' + str(item['products']))
				for product in item['products']:
					if product['id'] == product_id:
						if short_response is False:
							print('version ' + item['version'] + '-' + item['release'] + ' is available')
						refined_data.append({'id':item['id'], 'version':item['version'], 'release': item['release']})
	
	refined_data.sort(reverse=True, key=mySort)

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

