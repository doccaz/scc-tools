#!/usr/bin/python3
import sys
import urllib3
import json
import collections

def mySort(e):
	return e['id']


if len(sys.argv) != 3:
	print('Usage: ' + sys.argv[0] + ' <product id> <package name>')
	exit(1)
else:
	product_id = int(sys.argv[1])
	package_name = sys.argv[2]

print('looking for ' + package_name + ' on product id ' + str(product_id))

http = urllib3.PoolManager()
urllib3.disable_warnings()

try:
	r = http.request('GET', 'https://scc.suse.com/api/package_search/packages?product_id=' + str(product_id) + '&query=' + package_name)
except Exception as e:
	print('Error while connecting: ' + str(e))
	exit(1)

return_data = {}

if r.status == 200:
	return_data = json.loads(r.data)

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
					print('version ' + item['version'] + '-' + item['release'] + ' is available for product_id ' + str(product_id) + '(id = ' + str(item['id']) + ')')
					refined_data.append({'id':item['id'], 'version':item['version'], 'release': item['release']})
	
print('--------')
refined_data.sort(reverse=True, key=mySort)

try:
	print('latest version for ' + package_name + ' is ' + refined_data[0]['version'] + '-' + refined_data[0]['release'])
except IndexError:
	print('could not find any version for package ' + package_name)
	exit(1)



