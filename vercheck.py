#!/usr/bin/python3
import re
import sys
import os
import time
import subprocess
import signal
import getopt
import pdb
import weakref
import warnings
import json
import urllib
from datetime import datetime
from threading import Thread, Lock, active_count
from contextlib import contextmanager
from distutils.version import LooseVersion

# external libraries
try:
    import urllib3
    import yaml
except ImportError as e:
    print(f"Please verify that you have the required Python library installed: {e}")
    exit(1)

# main class that deals with command lines, reports and everything else
class SCCVersion():

    version = '2.6'
    build = '20250813'

    # static product list (taken from RMT and other sources)
    # rmt-cli products list --name "SUSE Linux Enterprise Server" --all
    # rmt-cli products list --name "SUSE Linux Enterprise Desktop" --all
    # rmt-cli products list --name "openSUSE" --all
    #
    # (replaced by this alternative, no authentication needed):
    # https://scc.suse.com/api/package_search/products
    #
    product_list = {}

    # all known module IDs, and corresponding product IDs (from RMT)
    # modules: rmt-cli products list --all --csv | grep '15 SPx' | grep x86_64 | egrep -v 'Debuginfo|Sources' | egrep -i 'Module|PackageHub'
    # related products: rmt-cli products list --all --csv | grep '15 SPx' | grep x86_64 | egrep -v 'Debuginfo|Sources' | egrep -iv 'Module|PackageHub'
    # (replaced by a more clever logic)

    # to get the list of product IDs:
    # rmt-cli products list --name "SUSE Manager Server" --all

    # SUSE Manager from 4.0 to 4.3 is a special case, as it had its own product entry.
    # from 5.x onwards it's just a regular extension for SLE Micro.
    suma_product_list = {
        1899: {'name': 'SUSE Manager Server 4.0', 'identifier': '4.0'},
        2012: {'name': 'SUSE Manager Server 4.1', 'identifier': '4.1'},
        2222: {'name': 'SUSE Manager Server 4.2', 'identifier': '4.2'},
        2378: {'name': 'SUSE Manager Server 4.3', 'identifier': '4.3'},
    }

    # result lists
    uptodate = []
    notfound = []
    different = []
    unsupported = []
    suseorphans = []
    suseptf = []

    # selected product
    selected_product = {}

    # report flags
    show_unknown = False
    show_diff = False
    show_uptodate = False
    show_unsupported = False
    show_suseorphans = False
    show_suseptf = False

    # verbose messages
    verbose = False

    # base name for the reports
    sc_name = ''

    # maximum number of running threads
    max_threads = 35

    # time to wait before starting each chunk of threads
    wait_time = 5

    # override architecture
    arch = None

    # short responses (just package versions)
    short_response = False

    # partial matches allowed?
    partial_search = False

    # force data refresh from SCC (ignore the cache)
    force_refresh = False

    # default output directory for the reports
    outputdir = os.getcwd()

    # cache manager singleton
    cm = None

    # thread list
    threads = []

    def __init__(self):
        # ignore DeprecationWarnings for now to avoid polluting the output
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        self.cm = CacheManager()

    def set_verbose(self, verbose):
        self.verbose = verbose

    def set_force_refresh(self, force_refresh):
        self.force_refresh = force_refresh

    def get_verbose(self, verbose):
        return self.verbose

    def cleanup(self, signalNumber, frame):
        print('\nokay, okay, I\'m leaving!')
        sys.exit(1)
        return

    def color(text, color, bold=True):
        esc = '\x1b['
        ret = ""
        if bold:
            ret += esc + '1m'
        reset = esc + '0m'
        if color == 'red':
            ret += esc + '31m' + text + reset
        elif color == 'green':
            ret += esc + '32m' + text + reset
        elif color == 'yellow':
            ret += esc + '33m' + text + reset
        elif color == 'blue':
            ret += esc + '34m' + text + reset
        elif color == 'magenta':
            ret += esc + '35m' + text + reset
        elif color == 'cyan':
            ret += esc + '36m' + text + reset
        else:
            return text
        return ret

    def fetch_product_list():
        print(f'-- Downloading product list from SCC...')

        # single instance for urllib3 pool
        http = urllib3.PoolManager(maxsize=5)

        # maximum retries for each thread
        max_tries = 3
        tries = 0

        valid_response = False
        connection_failed = False

        # server replies which are temporary errors (and can be retried)
        retry_states = [429, 502, 504]

        # server replies which are permanent errors (and cannot be retried)
        error_states = [400, 403, 404, 422, 500, -1]

        base_url = "https://scc.suse.com/api/package_search/products"

        while not valid_response and tries < max_tries:
            try:
                r = http.request('GET', base_url, headers={
                                 'Accept-Encoding': 'gzip, deflate', 'Connection': 'close'})
            except Exception as e:
                print('Error while connecting: ' + str(e))
                connection_failed = True

            if connection_failed:
                print('It appears the server is offline, giving up.')
                break
            elif r.status == 200:
                if tries > 0:
                    print('got a good reply after %d tries' % (tries))
                return_data = json.loads(r.data.decode('utf-8'))
                valid_response = True
            elif r.status in error_states:
                if r.data:
                    json_data = json.loads(r.data.decode('utf-8'))
                    print(
                        'cannot be processed due to error: [' + json_data['error'] + ']')
                print('got a fatal error (%d). Results will be incomplete!\nPlease contact the service administrators or try again later.' % (r.status))
                break
            elif r.status in retry_states:
                tries = tries + 1
                print(
                    'got non-fatal reply (%d) from server, trying again in 5 seconds (try: %d/%d)' % (r.status, tries, max_tries))
                time.sleep(5)
                continue
            else:
                print('got unknown error %d from the server!' % r.status)

            if valid_response:
                print('* ' + str(len(return_data['data'])) + ' products found.')
                # reprocess the data to fit our logic
                plist={}
                for p in return_data['data']:
                    #'name': 'SUSE Manager Server', 'identifier': 'SUSE-Manager-Server/4.0/x86_64', 'type': 'base', 'free': False, 'architecture': 'x86_64', 'version': '4.0'}
                    plist[p['id']] = {'id':p['id'], 'name':p['name'],'identifier':p['identifier'], 'type':p['type'], 'free':p['free'], 'architecture':p['architecture'], 'version':p['version']}
                return plist
        return {}


    def find_suma(self, directory_name):
        regex_suma = r"SUSE Manager release (.*) .*"
        try:
            f = open(directory_name + '/basic-environment.txt', 'r')
            text = f.read()
            f.close()
            matches_suma = re.search(regex_suma, text)
            for p in self.suma_product_list:
                if matches_suma is not None and matches_suma.group(1) == self.suma_product_list[p]['identifier']:
                    return p
        except Exception as e:
            print('error: ' + str(e))
        return -1

    def find_cpe(self, directory_name, architecture):
        regex_os = r".*\"cpe\:/o\:suse\:(sles|sled|sles_sap|sle-micro)\:(.*)\:?(.*)\""

        try:
            with open(directory_name + '/basic-environment.txt', 'r') as f:
                text = f.read()
                f.close()

            matches_os = re.search(regex_os, text)
            if matches_os.groups() is not None:
                # print('found CPE: ' + str(matches_os.groups()))
                # print('found architecture: ' + architecture)
                probable_id = matches_os.group(1).upper() + '/' +  matches_os.group(2).replace(':sp','.').replace(':', '.') + '/' + architecture.upper()
                print('probable identifier: ' + probable_id)
                for p in self.product_list.items():
                    if p[1]['identifier'].upper() == probable_id:
                        print('found record: ' +  str(p[1]))
                        return p[1]

        except Exception as e:
            print('error: ' + str(e))
        return None

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
            print('error opening hardware.txt, trying basic-environment.txt...')
            try:
                f = open(directory_name + '/basic-environment.txt', 'r')
                text = f.read()
                f.close()
                regex = r"^Linux.* (\w+) GNU\/Linux$"
                matches = re.search(regex, text, re.MULTILINE)
                if matches != None:
                    return matches.group(1)
            except Exception as e:
                print(
                    'could not determine architecture for the supportconfig directory. Please supply one with -a.')
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
                    found_start = True
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
        print('ID' + '\t' + 'Name' +  '\t\t\t\t' + 'Architecture')
        print('----------------------------------------------------------------')
        for p in self.product_list.items():
            print(str(p[1]['id']) + '\t' + str(p[1]['name'])+ ' ' + str(p[1]['version']) + ' ' + str(p[1]['architecture']))

        print('total: ' + str(len(self.product_list)) + ' products.')
        return

    def usage(self):
        print('Usage: ' + sys.argv[0] + ' [-l|--list-products] -p|--product product id -n|--name <package name> [-s|--short] [-v|--verbose] [-1|--show-unknown] [-2|--show-differences] [-3|--show-uptodate] [-4|--show-unsupported] [-5|--show-suseorphans] [-6|--show-suseptf] [-o|--outputdir] [-d|--supportconfig] [-a|--arch <architecture>] [-f|--force-refresh] [-V|--version]')
        return

    def show_version(self):
        print('SCC VerCheck version ' + SCCVersion.color(self.version + '-' +
              self.build, 'green') + ' by Erico Mendonca <erico.mendonca@suse.com>\n')
        return

    def show_help(self):
        self.usage()
        print('\n')
        print('-l|--list-products\t\tLists all supported products. Use this to get a valid product ID for further queries.')
        print('-p|--product <product id>\tSpecifies a valid product ID for queries. Mandatory for searches.')
        print('-n|--name <package name>\tSpecifies a package name to search. Exact matches only. Mandatory for searches.')
        print('-N|--partialname <package name>\tSpecifies a partial package name to search. Mandatory for searches.')
        print('-s|--short\t\t\tOnly outputs the latest version, useful for scripts')
        print('-v|--verbose\t\t\tOutputs extra information about the search and results')
        print('-1|--show-unknown\t\tshows unknown packages as they are found.')
        print('-2|--show-differences\t\tshows packages that have updates available as they are found.')
        print('-3|--show-uptodate\t\tshows packages that are on par with the updated versions as they are found.')
        print('-4|--show-unsupported\t\tshows packages that have a vendor that is different from the system it was collected from.')
        print('-5|--show-suseorphans\t\tshows packages that are from SUSE, but are now orphans (e.g. from different OS/product versions).')
        print('-6|--show-suseptf\t\tshows SUSE-made PTF (Program Temporary Fix) packages.')
        print('-o|--outputdir\t\t\tspecify an output directory for the reports. Default: current directory.')
        print('-d|--supportconfig\t\tAnalyzes a supportconfig directory and generates CSV reports for all packages described by types 1-6.')
        print('-a|--arch <architecture>\t\t\tSupply an architecture for the supportconfig analysis.')
        print('-f|--force-refresh\t\tIgnore cached data and retrieve latest data from SCC and public cloud info')
        print('-V|--version\t\t\tShow program version')
        print('\n')
        return

    def test(self):
        self.threads = []
        package_name = 'glibc'
        instance_nr = 0

        for k, v in self.product_list.items():
            print('searching for package \"glibc\" in product id \"' +
                  str(k) + '\" (' + v['name'] + ' ' +  v['version'] + ')')
            self.threads.insert(instance_nr, PackageSearchEngine(
                instance_nr, k, package_name, v['name'], '0', self.force_refresh, self.partial_search))
            self.threads[instance_nr].start()
            instance_nr = instance_nr + 1

        # fetch results for all threads
        while len(self.threads) > 0:
            for thread_number, t in enumerate(self.threads):
                # if t.is_alive():
                t.join(timeout=5)
                if t.is_alive():
                    print('thread ' + t.name + ' is not ready yet, skipping')
                    self.threads.append(t)
                    continue
                refined_data = t.get_results()

                # for thread_number in range(instance_nr):
                # 	threads[thread_number].join()
                # 	refined_data = threads[thread_number].get_results()
                try:
                    print('[thread ' + str(thread_number) + ' ] latest version for ' + refined_data['query'] + ' on product ID ' + str(
                        refined_data['product_id']) + ' is ' + refined_data['results'][0]['version'] + '-' + refined_data['results'][0]['release'])
                    if self.verbose:
                        for item in refined_data['results']:
                            print('[thread ' + str(thread_number) + ' ] version ' + item['version'] + '-' +
                                  item['release'] + ' is available on repository [' + item['repository'] + ']')
                except IndexError:
                    print('could not find any version for package ' + package_name)
            time.sleep(.1)
        return

    def search_package(self, product_id, package_name):

        self.threads = []

        if product_id in self.suma_product_list:
            plist = self.suma_product_list
        else:
            plist = self.product_list

        print('searching for package \"' + package_name + '\" in product id \"' +
              str(product_id) + '\" (' + plist[product_id]['name'] + ' ' +  plist[product_id]['version'] + ')')
        self.threads.insert(0, PackageSearchEngine(
            0, product_id, package_name, plist[product_id]['name'], '0', self.force_refresh, self.partial_search))
        self.threads[0].start()

        # fetch results for the only thread
        self.threads[0].join()
        refined_data = self.threads[0].get_results()
        sle_results = [p for p in refined_data['results']
                       if 'SUSE Linux Enterprise' in p['repository']]

        try:
            if self.short_response:
                if len(sle_results) > 0:
                    print(sle_results[0]['version'] +
                          '-' + sle_results[0]['release'])
                else:
                    print(refined_data['results'][0]['version'] +
                          '-' + refined_data['results'][0]['release'])
            else:
                if self.partial_search is False:
                    if len(sle_results) > 0:
                        print('latest version for ' + SCCVersion.color(refined_data['query'], 'yellow') + ' on product ID ' + str(refined_data['product_id']) + '(' + SCCVersion.color(plist[product_id]['name'], 'yellow') + ') is ' + SCCVersion.color(
                            sle_results[0]['version'] + '-' + sle_results[0]['release'], 'green') + ', found on ' + SCCVersion.color(sle_results[0]['products'][0]['name'] + ' (' + sle_results[0]['products'][0]['identifier'] + ')', 'green'))
                    else:
                        print('latest version for ' + SCCVersion.color(refined_data['query'], 'yellow') + ' on product ID ' + str(refined_data['product_id']) + '(' + SCCVersion.color(plist[product_id]['name'], 'yellow') + ') is ' + SCCVersion.color(
                            refined_data['results'][0]['version'] + '-' + refined_data['results'][0]['release'], 'green') + ', found on ' + SCCVersion.color(refined_data['results'][0]['products'][0]['name'] + ' (' + refined_data['results'][0]['products'][0]['identifier'] + ')', 'green'))
            if self.partial_search:
                for item in refined_data['results']:
                    print(item['name'] + ' version ' + item['version'] + '-' + item['release'] +
                        ' is available on repository [' + item['repository'] + ']')

            if self.verbose:
                for item in refined_data['results']:
                    print('version ' + item['version'] + '-' + item['release'] +
                          ' is available on repository [' + item['repository'] + ']')
        except IndexError:
            if self.short_response:
                print('none')
            else:
                print('could not find any version for package ' + package_name)
        return

    def ask_the_oracle(self, version_one, version_two):
        # we don't know how to parse this, let's ask zypper
        if self.verbose:
            print('don''t know how to compare: %s and %s, let''s ask the oracle' % (
                version_one, version_two))
        proc = subprocess.Popen(["/usr/bin/zypper", "vcmp", str(version_one),
                                str(version_two)], env={"LANG": "C"}, stdout=subprocess.PIPE)
        output, err = proc.communicate()
        regex = r".*is newer than.*"
        if output is not None:
            matches = re.match(regex, output.decode('utf-8'))
            if matches is not None:
                if self.verbose:
                    print('the oracle says: %s is newer' % str(version_one))
                return True
            else:
                if self.verbose:
                    print('the oracle says: %s is older' % str(version_one))
                return False

    def is_newer(self, version_one, version_two):
        result = False
        ver_regex = r"(.*)-(.*)"
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

    def check_supportconfig(self, supportconfigdir, product_id):
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
        if int(product_id) > -1:
            # if the user supplied a product id, use it
            selected_product_id = product_id
            match_os = self.product_list[selected_product_id]
            print('using supplied product id: ' + str(product_id) + '(' + self.product_list[selected_product_id]['identifier'] + ')')
        else:
            selected_product_id = -1

        if match_os is not None and match_arch != "unknown":
            print('product name = ' + match_os['name'] + ' (id ' + str(
                match_os['id']) + ', ' + match_arch + ')')
            selected_product_id = match_os['id']
            self.selected_product = match_os
            # primary repositories for trusted updates should have this regex
            base_regex = r"(^SUSE Linux Enterprise.*|^Basesystem.*)"
            if match_suma != -1:
                print('found ' + self.suma_product_list[match_suma]
                    ['name'] + ', will use alternate id ' + str(match_suma))
                selected_product_id = match_suma
                # primary repositories for trusted updates should have this regex
                base_regex = r"^SUSE Manager.*"

        else:
            print('error while determining CPE. This is an unknown/unsupported combination!')
            exit(1)
            return ([], [], [], [])

        rpmlist = self.read_rpmlist(supportconfigdir)
        total = len(rpmlist)
        print('found ' + str(total) + ' total packages to check')

        count = 0
        self.threads = []
        # fetch results for all threads
        for chunk in self.list_chunk(rpmlist, self.max_threads):
            for p in chunk:
                self.threads.insert(count, PackageSearchEngine(
                    count, selected_product_id, p[0], p[1], p[2], self.force_refresh, self.partial_search))
                self.threads[count].start()
                count += 1
            progress = '[' + str(count) + '/' + str(total) + ']'
            sys.stdout.write('processing ' + progress)
            blank = ('\b' * (len(progress) + 11))
            sys.stdout.write(blank)
            sys.stdout.flush()
            time.sleep(self.wait_time)

        print('gathering results...    ')
        to_process = len([t for t in self.threads if t.processed == False])
        while to_process > 0:
            for t in [t for t in self.threads if t.done and t.processed == False]:
                if self.verbose:
                    print('joining thread ' + t.name +
                          ' (waiting: ' + str(to_process) + ')...')
                t.join(timeout=5)
                # time.sleep(.001)
                if t.is_alive():
                    print('thread ' + t.name + ' is not ready yet, skipping')
                    self.threads.append(t)
                    continue
                # else:
                # print('thread ' + t.name + ' is dead')

                refined_data = t.get_results()
                # print('refined data = ' + str(refined_data))
                try:
                    if ('SL-Micro' in match_os['identifier']) or 'SLE-Micro' in match_os['identifier']:
                        target_version = 'SUSE Linux Enterprise 15'
                    else:
                        target_version = 'SUSE Linux Enterprise ' + \
                            match_os['version'].split('.')[0]

                    # print("package does not exist, target_version is " + target_version)
                    # print("supplied distro for package " + str(refined_data['query']) + ' is ' + str(refined_data['supplied_distro']))
                    # print("target identifier is " + target_version)
                    if (('SLES' in match_os['identifier']) and (str(refined_data['supplied_distro']) not in target_version)):
                        self.unsupported.append(
                            [refined_data['query'], refined_data['supplied_distro'], refined_data['supplied_version']])

                    if len(refined_data['results']) == 0:
                        self.notfound.append(
                            [refined_data['query'], refined_data['supplied_distro'], refined_data['supplied_version']])
                    else:
                        latest = None
                        for item in refined_data['results']:
                            latest = item['version'] + '-' + item['release']
                            selected_repo = item['repository']
                            if (re.match(base_regex, item['repository']) is not None) and (self.is_newer(item['version'] + '-' + item['release'], refined_data['supplied_version'])):
                                if self.verbose:
                                    print('---> found version %s-%s for package %s in repository %s which is a base repository, ignoring the rest' % (
                                        item['version'], item['release'], refined_data['query'], item['repository']))
                                break
                        if latest is None:
                            latest = refined_data['results'][0]['version'] + \
                                '-' + refined_data['results'][0]['release']
                            selected_repo = refined_data['results'][0]['repository']
                        if self.verbose:
                            print('latest version for ' + refined_data['query'] + ' on product ID ' + str(refined_data['product_id']) + ' is ' + refined_data['results']
                                  [0]['version'] + '-' + refined_data['results'][0]['release'] + ' in repository ' + refined_data['results'][0]['repository'])
                        # print('latest = ' + latest)
                        if self.is_newer(latest, refined_data['supplied_version']) and (latest != refined_data['supplied_version']):
                            self.different.append(
                                [refined_data['query'], refined_data['supplied_version'], latest, selected_repo])
                        else:
                            self.uptodate.append(
                                [refined_data['query'], refined_data['supplied_version']])

                    t.processed = True
                    to_process = len(
                        [t for t in self.threads if t.processed == False])
                    time.sleep(.001)
                except IndexError:
                    # print('[thread ' + str(thread_number) + '] could not find any version for package ' + refined_data['query'])
                    pass
                except KeyError as e:
                    print('Cannot find field: ' + e)
                    pass
                print('thread ' + t.name + ' is done')
                time.sleep(.1)
                sys.stdout.flush()
            time.sleep(.1)

        # check if there are SUSE orphan packages in notfound
        self.notfound.sort()
        for package, distribution, version in self.notfound.copy():
            if 'SUSE Linux Enterprise' in distribution:
                if self.verbose:
                    print('**** moving SUSE orphan package to appropriate list: ' +
                          package + '-' + version + ' (' + distribution + ')')
                self.notfound.remove([package, distribution, version])
                self.suseorphans.append([package, distribution, version])

        # check if there are SUSE PTF packages in unsupported
        self.unsupported.sort()
        for package, distribution, version in self.unsupported.copy():
            if 'SUSE Linux Enterprise PTF' in distribution:
                if self.verbose:
                    print('**** moving SUSE PTF package to appropriate list: ' +
                          package + '-' + version + ' (' + distribution + ')')
                self.unsupported.remove([package, distribution, version])
                self.suseptf.append([package, distribution, version])

        sys.stdout.write('\nDone.\n')
        sys.stdout.flush()

        return (self.uptodate, self.unsupported, self.notfound, self.different, self.suseorphans, self.suseptf)

    def write_reports(self):
        if len(self.uptodate) == 0:
            print('no reports will be written (unsupported product?)')
            return
        else:
            print('writing CSV reports to ' + self.outputdir + '\n')
            try:
                os.makedirs(self.outputdir, exist_ok=True)
            except OSError as e:
                print('error creating output directory at %s: %s' %
                      (self.outputdir, str(e)))

            try:
                with open(os.path.join(self.outputdir, 'vercheck-uptodate-' + self.sc_name + '.csv'), 'w') as f:
                    for p, c in self.uptodate:
                        f.write(p + ',' + c + '\n')
                    f.close()
            except Exception as e:
                print('Error writing file: ' + str(e))
                return

            try:
                with open(os.path.join(self.outputdir, 'vercheck-notfound-' + self.sc_name + '.csv'), 'w') as f:
                    for p, d, c in self.notfound:
                        f.write(p + ',' + d + ',' + c + '\n')
                    f.close()
            except Exception as e:
                print('Error writing file: ' + str(e))
                return

            try:
                with open(os.path.join(self.outputdir, 'vercheck-unsupported-' + self.sc_name + '.csv'), 'w') as f:
                    for p, d, c in self.unsupported:
                        f.write(p + ',' + d + ',' + c + '\n')
                    f.close()
            except Exception as e:
                print('Error writing file: ' + str(e))
                return

            try:
                with open(os.path.join(self.outputdir, 'vercheck-different-' + self.sc_name + '.csv'), 'w') as f:
                    for p, c, l, r in self.different:
                        f.write(p + ',' + c + ',' + l + ',' + r + '\n')
                    f.close()
            except Exception as e:
                print('Error writing file: ' + str(e))
                return

            try:
                with open(os.path.join(self.outputdir, 'vercheck-suseorphans-' + self.sc_name + '.csv'), 'w') as f:
                    for p, d, c in self.suseorphans:
                        f.write(p + ',' + d + ',' + c + '\n')
                    f.close()
            except Exception as e:
                print('Error writing file: ' + str(e))
                return

            try:
                with open(os.path.join(self.outputdir, 'vercheck-suseptf-' + self.sc_name + '.csv'), 'w') as f:
                    for p, d, c in self.suseptf:
                        f.write(p + ',' + d + ',' + c + '\n')
                    f.close()
            except Exception as e:
                print('Error writing file: ' + str(e))
                return

        field_size = 30
        if self.show_uptodate:
            print('\n\t\t---  Up-to-date packages ---\n')
            print(str.ljust('Name', field_size) + '\t' +
                  str.ljust('Current Version', field_size))
            print('=' * 80)
            for p, c in self.uptodate:
                print(str.ljust(p, field_size) + '\t' + c)
            print('\nTotal: ' + str(len(self.uptodate)) + ' packages')

        if self.show_diff:
            print('\n\t\t---  Different packages ---\n')
            print(str.ljust('Name', field_size) + '\t' + str.ljust('Current Version', field_size) +
                  '\t' + str.ljust('Latest Version', field_size) + '\t' + str.ljust('Repository', field_size))
            print('=' * 132)
            for p, c, l, r in self.different:
                print(str.ljust(p, field_size) + '\t' + str.ljust(c, field_size) +
                      '\t' + str.ljust(l, field_size) + '\t' + str.ljust(r, field_size))
            print('\nTotal: ' + str(len(self.different)) + ' packages')

        if self.show_unsupported:
            print('\n\t\t---  Unsupported packages ---\n')
            print(str.ljust('Name', field_size) + '\t' + str.ljust('Vendor',
                  field_size) + '\t' + str.ljust('Current Version', field_size))
            print('=' * 80)
            for p, c, l in self.unsupported:
                print(str.ljust(p, field_size) + '\t' + str.ljust(c,
                      field_size) + '\t' + str.ljust(l, field_size))
            print('\nTotal: ' + str(len(self.unsupported)) + ' packages')

        if self.show_unknown:
            print('\n\t\t--- Unknown packages ---\n')
            print(str.ljust('Name', field_size) + '\t' + str.ljust('Vendor',
                  field_size) + '\t' + str.ljust('Current Version', field_size))
            print('=' * 80)
            for p, c, l in self.notfound:
                print(str.ljust(p, field_size) + '\t' + str.ljust(c,
                      field_size) + '\t' + str.ljust(l, field_size))
            print('\nTotal: ' + str(len(self.notfound)) + ' packages')

        if self.show_suseorphans:
            print('\n\t\t--- SUSE orphan packages ---\n')
            print(str.ljust('Name', field_size) + '\t' + str.ljust('Vendor',
                  field_size) + '\t' + str.ljust('Current Version', field_size))
            print('=' * 80)
            for p, c, l in self.suseorphans:
                print(str.ljust(p, field_size) + '\t' + str.ljust(c,
                      field_size) + '\t' + str.ljust(l, field_size))
            print('\nTotal: ' + str(len(self.suseorphans)) + ' packages')

        if self.show_suseptf:
            print('\n\t\t--- SUSE PTF packages ---\n')
            print(str.ljust('Name', field_size) + '\t' + str.ljust('Vendor',
                  field_size) + '\t' + str.ljust('Current Version', field_size))
            print('=' * 80)
            for p, c, l in self.suseptf:
                print(str.ljust(p, field_size) + '\t' + str.ljust(c,
                      field_size) + '\t' + str.ljust(l, field_size))
            print('\nTotal: ' + str(len(self.suseptf)) + ' packages')

        return


# separate class instantiated by each thread, does a search and posts results
class PackageSearchEngine(Thread):

    # number of concurrent threads
    max_threads = 20

    # single instance for urllib3 pool
    http = urllib3.PoolManager(maxsize=5)

    # set default socket options
    # HTTPConnection.default_socket_options += [ (socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) ]
    # HTTPConnection.debuglevel = 15

    # maximum retries for each thread
    max_tries = 5

    # server replies which are temporary errors (and can be retried)
    retry_states = [429, 502, 504]

    # server replies which are permanent errors (and cannot be retried)
    error_states = [400, 403, 404, 422, 500]

    results = {}

    def __init__(self, instance_nr, product_id, package_name, supplied_distro, supplied_version, force_refresh, partial_search):
        super(PackageSearchEngine, self).__init__(
            name='search-' + package_name)
        urllib3.disable_warnings()
        self.instance_nr = instance_nr
        self.product_id = product_id
        self.package_name = package_name
        self.supplied_distro = supplied_distro
        self.supplied_version = supplied_version
        self.force_refresh = force_refresh
        self.partial_search = partial_search
        self.cm = CacheManager()
        self.done = False
        self.processed = False

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
        # print('release %s will be considered as %s' % (e['release'], release))
        return LooseVersion(v + '-' + r)

    def get_results(self):
        return {'product_id': self.product_id, 'query': self.package_name, 'supplied_distro': self.supplied_distro, 'supplied_version': self.supplied_version, 'results': self.results}

    def run(self):
        # print('[Thread ' + str(self.instance_nr) + '] looking for ' + self.package_name + ' on product id ' + str(self.product_id))
        tries = 0
        valid_response = False
        refined_data = []
        return_data = []
        cached = False

        # load the local cache if it exists and checks for valid data
        cached_data = self.cm.get_cache_data()
        product_list = {}
        if (self.cm.initialized) and self.force_refresh is False:
            try:
                item, product = self.cm.get_record(
                    self.product_id, self.package_name)
                if item is None:
                    cached = False
                else:
                    if ((item['name'] == self.package_name) and (product is not None)):
                        age = datetime.strptime(
                            item['timestamp'], "%Y-%m-%dT%H:%M:%S.%f") - datetime.now()
                        cached = True
                        if age.days > self.cm.get_max_age():

                            item['repository'] = product['name']
                            item['product_id'] = self.product_id
                            refined_data.append(item)
                        else:
                            print('cached data for ' + self.package_name +
                                  ' is too old ( ' + str(age.days) + ' days), discarding cache entry')
                            self.cm.remove_record(item)
                            cached = False
            except KeyError as e:
                print('invalid cache entry for ' + self.package_name +
                      ', removing (reason: ' + e + ')')
                self.cm.remove_record(item)

        if (cached):
            self.sort_and_deliver(refined_data)
            print('found ' + self.package_name + ' for product ID ' +
                  str(self.product_id) + ' (cached)')
            return
        else:
            while not valid_response and tries < self.max_tries:
                try:
                    r = self.http.request('GET', 'https://scc.suse.com/api/package_search/packages?product_id=' + str(self.product_id) +
                                          '&query=' + urllib.parse.quote(self.package_name), headers={'Accept-Encoding': 'gzip, deflate', 'Accept':'application/vnd.scc.suse.com.v4+json', 'Connection': 'close'})
                except Exception as e:
                    print('Error while connecting: ' + str(e))
                    exit(1)

                return_data = {}

                if r.status == 200:
                    if tries > 0:
                        print('thread %d got a good reply after %d tries' %
                              (self.instance_nr, tries))
                    return_data = json.loads(r.data.decode('utf-8'))
                    valid_response = True
                elif r.status in self.error_states:
                    if r.data:
                        json_data = json.loads(r.data.decode('utf-8'))
                        print(
                            'cannot be processed due to error: [' + json_data['error'] + ']')
                    print('thread %d got a fatal error (%d). Results will be incomplete!\nPlease contact the service administrators or try again later.' % (
                        self.instance_nr, r.status))
                    break
                elif r.status in self.retry_states:
                    print('thread %d got non-fatal reply (%d) from server, trying again in 5 seconds ' %
                          (self.instance_nr, r.status))
                    time.sleep(5)
                    tries = tries + 1
                    continue
                else:
                    print('got unknown error %d from the server!' % r.status)

            if return_data:
                for item in return_data['data']:
                    # discard items that do not match exactly our query
                    if not self.partial_search and item['name'] != self.package_name:
                        # print('discarding item: ' + item)
                        continue
                    else:
                        # valid data, add it to the cache and to the results
                        # print('added result: ' + item['name'] + ' ' + item['version'] + '-' + item['release'])
                        item['repository'] = item['products'][0]['name'] + ' ' + \
                            item['products'][0]['architecture']
                        item['timestamp'] = datetime.now().isoformat()
                        refined_data.append(item)
                        self.cm.add_record(item)

            self.sort_and_deliver(refined_data)
        return

    def sort_and_deliver(self, refined_data):
        # sort and deliver the data
        try:
            refined_data.sort(reverse=True, key=self.mySort)
        except TypeError as e:
            # sometimes the version is so wildly mixed with letters that the sorter gets confused
            # but it's okay to ignore this
            # print('*** warning: sorting error due to strange version (may be ignored): ' + str(e))
            pass

        # print('refined data size: ' + str(len(refined_data)))
        self.results = refined_data
        self.done = True
        self.cm.write_cache()
        # del self.cm
        return


# main program
def main():
    sv = SCCVersion()
    signal.signal(signal.SIGINT, sv.cleanup)

    try:
        opts, args = getopt.getopt(sys.argv[1:],  "Vhp:n:N:lsvt123456a:d:o:f", ["version", "help", "product=", "name=", "partialname=", "list-products", "short", "verbose", "test", "show-unknown",
                                   "show-differences", "show-uptodate", "show-unsupported", "show-suseorphans", "show-suseptf", "arch=", "supportconfig=", "outputdir=", "force-refresh"])
    except getopt.GetoptError as err:
        print(err)
        sv.usage()
        exit(2)

    product_id = -1
    package_name = ''
    supportconfig_used = False
    short_response = False
    global show_unknown, show_diff, show_uptodate, show_unsupported, show_suseorphans, show_suseptf, partial_search
    global uptodate, different, notfound, unsupported, suseorphans, suseptf

    for o, a in opts:
        if o in ("-h", "--help"):
            sv.show_help()
            exit(1)
        if o in ("-V", "--version"):
            sv.show_version()
            exit(1)
        elif o in ("-a", "--arch"):
            sv.arch = a
        elif o in ("-s", "--short"):
            sv.short_response = True
        elif o in ("-p", "--product"):
            product_id = int(a)
        elif o in ("-n", "--name"):
            package_name = a
        elif o in ("-N", "--partialname"):
            package_name = a
            sv.partial_search = True
        elif o in ("-o", "--outputdir"):
            sv.outputdir = a
        elif o in ("-l", "--list-products"):
            sv.product_list = SCCVersion.fetch_product_list()
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
        elif o in ("-5", "--show-suseorphans"):
            sv.show_suseorphans = True
        elif o in ("-6", "--show-suseptf"):
            sv.show_suseptf = True
        elif o in ("-v", "--verbose"):
            sv.set_verbose(True)
        elif o in ("-f", "--force-refresh"):
            sv.set_force_refresh(True)
        elif o in ("-t", "--test"):
            sv.product_list = SCCVersion.fetch_product_list()
            sv.test()
            exit(0)
        elif o in ("-d", "--supportconfig"):
            sv.product_list = SCCVersion.fetch_product_list()
            supportconfigdir = a
            if os.path.isdir(a) is False:
                print(f"Directory {a} does not exist.\nIf you're using multiple options in one parameter, make sure -d is the last one (e.g. -vd <directory),\nor use it separately (-v -d <directory>)")
                exit(1)
            pc = PublicCloudCheck(force_refresh=sv.force_refresh)
            if (pc.analyze(supportconfigdir)):
                print(
                    f"--> Image ID is [{SCCVersion.color(pc.get_results()['name'], 'yellow')}]")
                if pc.get_results()['unsupported']:
                    print(
                        f"--> This image is {SCCVersion.color('UNSUPPORTED', 'red')} ({pc.get_results()['version']} not found in PINT data), continuing normal package analysis")
                else:
                    pc.get_report()

            supportconfig_used = True
            # Always continue with RPM analysis after printing public-cloud info
            uptodate, unsupported, notfound, different, suseorphans, suseptf = sv.check_supportconfig(
                supportconfigdir, product_id)
            sv.write_reports()
        else:
            assert False, "invalid option"

    if product_id == -1 or package_name == '':
        print('Please specify a product ID and package name.')
        sv.usage()
        exit(2)
    sv.product_list = SCCVersion.fetch_product_list()
    if product_id in sv.suma_product_list:
        plist = sv.suma_product_list
    elif product_id in sv.product_list:
        plist = sv.product_list
    else:
        plist=None

    if plist is None:
        print('Product ID ' + str(product_id) + ' is unknown.')
        exit(2)
    else:
        if sv.verbose:
            pname = plist[product_id]['name'] + ' ' + plist[product_id]['version'] + ' ' + plist[product_id]['architecture']
            print('Using product ID ' + str(product_id) +
                  ' (' + pname + ')')

    sv.search_package(product_id, package_name)

    return

# package cache


class Singleton(type):
    # Inherit from "type" in order to gain access to method __call__
    def __init__(self, *args, **kwargs):
        self.__instance = None  # Create a variable to store the object reference
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        if self.__instance is None:
            # if the object has not already been created
            # Call the __init__ method of the subclass and save the reference
            self.__instance = super().__call__(*args, **kwargs)
            return self.__instance
        else:
            # if object reference already exists; return it
            return self.__instance


class CacheManager(metaclass=Singleton):
    cache_data = []
    max_age_days = -5  # entries from the cache over 5 days old are discarded
    user_cache_dir = os.path.join(os.getenv('HOME'), '.cache/scc-tools')
    default_cache_dir = '/var/cache/scc-tools'
    cache_file = 'scc_data.json'
    active_cache_file = ''
    _lock = Lock()
    initialized = False
    verbose = False

    def __init__(self):
        if (os.access(self.default_cache_dir, os.W_OK)):
            self.active_cache_file = os.path.join(
                self.default_cache_dir, self.cache_file)
        else:
            self.active_cache_file = os.path.join(
                self.user_cache_dir, self.cache_file)
            if (os.path.exists(self.user_cache_dir) is False):
                os.makedirs(self.user_cache_dir)

        self.load_cache()
        # print('my cache has ' + len(self.cache_data) + ' entries')
        weakref.finalize(self, self.write_cache)

    @contextmanager
    def acquire_timeout(self, timeout):
        result = self._lock.acquire(timeout=timeout)
        time.sleep(0.001)
        # print('lock result = ' + result)
        if result:
            self._lock.release()
        yield result
        # print('lock status: ' + lock.locked())

    # loads the JSON cache if available
    def load_cache(self):
        try:
            with self.acquire_timeout(2) as acquired:
                if acquired:
                    if not self.initialized:
                        # if the default directory is writeable, use it
                        with open(self.active_cache_file, "r") as f:
                            self.cache_data = json.loads(f.read())
                        self.initialized = True
                        print('loaded ' + str(len(self.cache_data)) +
                              ' items from cache (' + self.active_cache_file + ')')
        except IOError:
            # print('Error reading the package cache from ' + self.active_cache_file + '(non-fatal)')
            return False
        except json.decoder.JSONDecodeError:
            print('Invalid cache data (non-fatal)')
            # print('Data read: ' + '[' + self.cache_data + ']')
            return False
        return True

    # saves the package data for later use
    def write_cache(self):
        try:
            with self.acquire_timeout(2) as acquired:
                if acquired:
                    if self.verbose:
                        print('writing ' + str(len(self.cache_data)) +
                              ' items to cache at ' + self.active_cache_file)
                    with open(self.active_cache_file, "w+") as f:
                        f.write(json.dumps(self.cache_data,
                                default=self.dt_parser))
                else:
                    print('write_cache: could not acquire lock!')
                    exit(1)
        except IOError:
            print(
                'Error saving package cache at ' + self.active_cache_file + ' (non-fatal)')
            return False
        return True

    # fetches a record from the cache
    def get_record(self, product_id, package_name):
        for item in self.cache_data:
            if package_name == item['name']:
                for p in item['products']:
                    if product_id == p['id']:
                        if self.verbose:
                            print("* cache hit: " + item)
                        item['repository'] = p['name']
                        return item, p

        return None, None

    # removes a record from the cache
    def remove_record(self, record):
        with self.acquire_timeout(5) as acquired:
            if acquired:
                for item in self.cache_data.copy():
                    if record['id'] == item['id']:
                        if self.verbose:
                            print('removing record from cache: ' + record)
                        self.cache_data.remove(item)
            else:
                print('remove_record: could not acquire lock!')
                exit(1)
        # print('items in cache: ' +  str(len(self.cache_data)))

    # adds a new record to the cache
    def add_record(self, record):
        # print('appending record to cache: ' + record)
        with self.acquire_timeout(5) as acquired:
            if acquired:
                found = False
                for item in self.cache_data:
                    if record['id'] == item['id'] and record['name'] == item['name']:
                        found = True
                        break
                if (found is False):
                    if self.verbose:
                        print("* cache: added record for " + record['id'])
                    self.cache_data.append(record)
                # else:
                # print('cache: rejecting duplicate item')
            else:
                print('add_record: could not acquire lock!')
                exit(1)
        # print('items in cache: ' + str(len(self.cache_data)))

    def get_max_age(self):
        return self.max_age_days

    def dt_parser(dt):
        if isinstance(dt, datetime):
            return dt.isoformat()

    def get_cache_data(self):
        return self.cache_data


class PublicImageCacheManager():
    cache_data = []
    max_age_days = -5  # entries from the cache over 5 days old are discarded
    user_cache_dir = os.path.join(os.getenv('HOME'), '.cache/scc-tools')
    default_cache_dir = '/var/cache/scc-tools'
    provider = ''
    cache_file = ''
    initialized = False
    failed = False

    def __init__(self, provider, force_refresh=False):
        self.provider = provider
        self.cache_file = 'public_cloud_' + provider + '.json'

        if (os.access(self.default_cache_dir, os.W_OK)):
            self.active_cache_file = os.path.join(
                self.default_cache_dir, self.cache_file)
        else:
            self.active_cache_file = os.path.join(
                self.user_cache_dir, self.cache_file)
            if (os.path.exists(self.user_cache_dir) is False):
                os.makedirs(self.user_cache_dir)

        if self.load_cache():
            age = datetime.strptime(self.cache_data['timestamp'], "%Y-%m-%dT%H:%M:%S.%f") - datetime.now()
            if force_refresh or age.days < self.get_max_age():
                print(f'* forcing metadata refresh for public images for {provider}')
                tmp_cache_data = self.get_image_states(provider)
                if len(tmp_cache_data) > 0:
                    self.cache_data = tmp_cache_data
                    with open(self.active_cache_file, 'w') as f:
                        f.write(json.dumps(self.cache_data))
            else:
                print(f'* public images cached data OK ({age.days} days old)')
        else:
            print(f'* cached data for {provider} does not exist, downloading')
            tmp_cache_data = self.get_image_states(provider)
            if len(tmp_cache_data) > 0:
                self.cache_data = tmp_cache_data
                with open(self.active_cache_file, 'w') as f:
                    f.write(json.dumps(self.cache_data))

        self.initialized = True
        return

    def load_cache(self):
        try:
            if not self.initialized:
                # if the default directory is writeable, use it
                with open(self.active_cache_file, "r") as f:
                    self.cache_data = json.loads(f.read())
                self.initialized = True
                print('loaded ' + str(len(self.cache_data)) +
                      ' items from cache (' + self.active_cache_file + ')')
        except IOError:
            # print('Error reading the package cache from ' + self.active_cache_file + '(non-fatal)')
            return False
        except json.decoder.JSONDecodeError:
            print('Invalid cache data (non-fatal)')
            # print('Data read: ' + '[' + self.cache_data + ']')
            return False

        return True

    def get_cache_data(self):
        return self.cache_data

    def get_max_age(self):
        return self.max_age_days

    def dt_parser(dt):
        if isinstance(dt, datetime):
            return dt.isoformat()

    def fetch_image_states(self, provider, list_type):
        print(f'-- Downloading data for {list_type} images on {provider}...')

        # single instance for urllib3 pool
        http = urllib3.PoolManager(maxsize=5)

        # maximum retries for each thread
        max_tries = 3
        tries = 0

        valid_response = False
        connection_failed = False

        # server replies which are temporary errors (and can be retried)
        retry_states = [429, 502, 504]

        # server replies which are permanent errors (and cannot be retried)
        error_states = [400, 403, 404, 422, 500, -1]

        base_url = "https://susepubliccloudinfo.suse.com/v1/" + \
            provider + "/images/" + list_type + ".json"

        while not valid_response and tries < max_tries:
            try:
                r = http.request('GET', base_url, headers={
                                 'Accept-Encoding': 'gzip, deflate', 'Connection': 'close'})
            except Exception as e:
                print('Error while connecting: ' + str(e))
                connection_failed = True

            if connection_failed:
                print('It appears the server is offline, giving up.')
                break
            elif r.status == 200:
                if tries > 0:
                    print('got a good reply after %d tries' % (tries))
                return_data = json.loads(r.data.decode('utf-8'))
                valid_response = True
            elif r.status in error_states:
                if r.data:
                    json_data = json.loads(r.data.decode('utf-8'))
                    print(
                        'cannot be processed due to error: [' + json_data['error'] + ']')
                print('got a fatal error (%d). Results will be incomplete!\nPlease contact the service administrators or try again later.' % (r.status))
                break
            elif r.status in retry_states:
                tries = tries + 1
                print(
                    'got non-fatal reply (%d) from server, trying again in 5 seconds (try: %d/%d)' % (r.status, tries, max_tries))
                time.sleep(5)
                continue
            else:
                print('got unknown error %d from the server!' % r.status)

            if valid_response:
                return return_data['images']

        return {}

    def get_image_states(self, provider):
        image_data = {}
        self.failed = False
        image_data['timestamp'] = datetime.now().isoformat()
        image_data['incomplete'] = False
        image_data['active'] = self.fetch_image_states(provider, 'active')
        if len(image_data['active']) == 0:
            print('cannot download cloud data for active images at the moment, will use cached data if available.')
            self.failed = True

        image_data['inactive'] = self.fetch_image_states(provider, 'inactive')
        if len(image_data['inactive']) == 0:
            print('cannot download cloud data for inactive images at the moment, will use cached data if available.')
            self.failed = True

        image_data['deprecated'] = self.fetch_image_states(
            provider, 'deprecated')
        if len(image_data['deprecated']) == 0:
            print('cannot download cloud data for deprecated images at the moment, will use cached data if available.')
            self.failed = True

        image_data['deleted'] = self.fetch_image_states(provider, 'deleted')
        if len(image_data['deleted']) == 0:
            print('cannot download cloud data for deleted images at the moment, will use cached data if available.')
            self.failed = True

        if self.failed:
            image_data['incomplete'] = True

        return image_data


class PublicCloudCheck():
    aws_image_data = {}
    gcp_image_data = {}
    azure_image_data = {}
    valid_states = ['active', 'inactive', 'deprecated', 'deleted']
    match_data = {}
    aws_cm = None
    azure_cm = None
    gcp_cm = None

    def __init__(self, verbose=True, force_refresh=False):
        self.match_data = {}
        self.aws_cm = PublicImageCacheManager(provider='amazon', force_refresh=force_refresh)
        self.gcp_cm = PublicImageCacheManager(provider='google', force_refresh=force_refresh)
        self.azure_cm = PublicImageCacheManager(provider='microsoft', force_refresh=force_refresh)
        self.aws_image_data = self.aws_cm.get_cache_data()
        self.gcp_image_data = self.gcp_cm.get_cache_data()
        self.azure_image_data = self.azure_cm.get_cache_data()
        if verbose:
            print(f"--- AMAZON data as of {self.aws_image_data['timestamp']}")
            if 'incomplete' in self.aws_image_data and self.aws_image_data['incomplete']:
                print("*** data may be incomplete (previous failure downloading)")
            for state in self.valid_states:
                print(f"* {len(self.aws_image_data[state])} {state} images")
            print()
            print(
                f"--- MICROSOFT data as of {self.azure_image_data['timestamp']}")
            if 'incomplete' in self.azure_image_data and self.azure_image_data['incomplete']:
                print("*** data may be incomplete (previous failure downloading)")

            for state in self.valid_states:
                print(f"* {len(self.azure_image_data[state])} {state} images")
            print()
            print(f"--- GOOGLE data as of {self.gcp_image_data['timestamp']}")
            if 'incomplete' in self.gcp_image_data and self.gcp_image_data['incomplete']:
                print("*** data may be incomplete (previous failure downloading)")

            for state in self.valid_states:
                print(f"* {len(self.gcp_image_data[state])} {state} images")
            print()

        return

    def analyze(self, basedir):
        self.provider = self.get_public_image_type(basedir)
        print(
            f"--> Public cloud provider for {basedir} is [{SCCVersion.color(self.provider, 'yellow')}]")
        if self.provider == "unknown":
            print(
                '--> this image has invalid (but present) public cloud metadata. Continuing normal analysis.')
            return False
        elif self.provider == 'none':
            print('--> not a public cloud image, continuing normal analysis')
            return False
        else:
            self.match_data = self.process_public_cloud(basedir, self.provider)
        return True

    def get_results(self):
        return self.match_data

    def get_report(self):
        if self.match_data['license_type'] != '':
            print(f"--> license type is [{self.match_data['license_type']}]")

        if self.match_data['version'] != '':
            print(
                f"--> Results for search on image [{self.match_data['name']}], version [{self.match_data['version']}]:")
        else:
            print(
                f"--> Results for search on image [{self.match_data['name']}]:")

        if self.match_data['unsupported']:
            print(
                f"*** Unsupported image found for public cloud {self.provider}")
        else:
            for state in self.valid_states:
                for item in self.match_data[state]:
                    if 'id' in item.keys():
                        print(
                            f"{state.upper()}: image id [{item['id']}] ({item['name']})")
                    else:
                        print(f"{state.upper()}: image [{item['name']}]")
                    print(f"* publish date: [{item['publishedon']}]")
                    print(f"* more info: [{item['changeinfo']}]")
                    print(f"* deprecated since [{item['deprecatedon']}]")
                    print(f"* deleted on [{item['deletedon']}]")
                    print(f"* replaced by [{item['replacementname']}]")
        return

    def get_public_image_type(self, basedir):
        gcp_regex = r"^\# /usr/bin/gcemetadata"
        azure_regex = r"^\# /usr/bin/azuremetadata"
        aws_regex = r"^\# /usr/bin/ec2metadata"

        meta_file = basedir + '/public_cloud/metadata.txt'
        if os.path.isfile(meta_file):
            with open(meta_file, 'r') as f:
                contents = f.read()
            if re.search(gcp_regex, contents, re.MULTILINE):
                return 'google'
            elif re.search(azure_regex, contents, re.MULTILINE):
                return 'microsoft'
            elif re.search(aws_regex, contents, re.MULTILINE):
                return 'amazon'
            else:
                return 'unknown'
        else:
            return 'none'

    def process_public_cloud(self, basedir, image_type):

        meta_file = basedir + '/public_cloud/metadata.txt'

        match_active_images = []
        match_inactive_images = []
        match_deprecated_images = []
        match_deleted_images = []
        is_unsupported = False
        name = ''
        version = ''
        license_type = ''

        if image_type == 'microsoft':
            # Azure image test
            with open(meta_file, 'r') as f:
                metadata = yaml.safe_load(f)

            query_image = metadata['compute']['storageProfile']['imageReference']
            # if it's not an offer from the marketplace, return None
            if query_image['offer'] is None:
                name = "None:None"
                version = "None"
            else:
                query = query_image['publisher'].lower(
                ) + ':' + query_image['offer'] + ':' + query_image['sku']
                name = query_image['offer'] + ':' + query_image['sku']
                version = query_image['version']
                if metadata['compute']['licenseType'] == 'SLES_BYOS':
                    license_type = 'BYOS'
                else:
                    license_type = 'PAYG'

                regex_image = r"^(" + query + "):"

                for image in self.azure_image_data['active']:
                    if re.match(regex_image, image['urn']):
                        match_active_images.append(image)

                for image in self.azure_image_data['inactive']:
                    if re.match(regex_image, image['urn']):
                        match_inactive_images.append(image)

                for image in self.azure_image_data['deprecated']:
                    if re.match(regex_image, image['urn']):
                        match_deprecated_images.append(image)

        elif image_type == 'google':
            # GCP image test
            regex_image = r"^projects/(.*)/global/images/(.*)"
            md_str = None
            with open(meta_file, 'r') as f:
                contents = f.readlines()

            for l in contents:
                md_str = re.match(r"^image:(.*)$", l)
                if md_str:
                    break

            if md_str:
                image_line = md_str.group(1).strip()
                match = re.match(regex_image, image_line)
                if match:
                    query_project = match.group(1)
                    query_image = match.group(2)
                    name = query_project
                    version = query_image

                    for image in self.gcp_image_data['active']:
                        if image['project'] == query_project and image['name'] == query_image:
                            match_active_images.append(image)

                    for image in self.gcp_image_data['inactive']:
                        if image['project'] == query_project and image['name'] == query_image:
                            match_inactive_images.append(image)

                    for image in self.gcp_image_data['deprecated']:
                        if image['project'] == query_project and image['name'] == query_image:
                            match_deprecated_images.append(image)
                else:
                    name = "Unknown"
                    version = "Unknown/" + image_line
            else:
                print("Warning: No GCP image line found in metadata.txt")
                name = "Unknown"
                version = "Unknown"
        elif image_type == 'amazon':
            # Amazon image test
            regex_image = r"^projects/(.*)/global/images/(.*)"
            md_str = ''
            with open(meta_file, 'r') as f:
                contents = f.read()

            md_str = re.search(r"^ami-id:(.*)$", contents, re.MULTILINE)
            query_image = md_str.group(1).strip()
            name = query_image

            for image in self.aws_image_data['active']:
                if image['id'] == query_image:
                    match_active_images.append(image)

            for image in self.aws_image_data['inactive']:
                if image['id'] == query_image:
                    match_inactive_images.append(image)

            for image in self.aws_image_data['deprecated']:
                if image['id'] == query_image:
                    match_deprecated_images.append(image)

        # deduplicate results (preserve order)
        def _dedupe_list(lst):
            seen = set()
            out = []
            for item in lst:
                key = item.get('id') if isinstance(item, dict) and 'id' in item else item.get('name') if isinstance(item, dict) else item
                if key not in seen:
                    seen.add(key)
                    out.append(item)
            return out

        match_active_images = _dedupe_list(match_active_images)
        match_inactive_images = _dedupe_list(match_inactive_images)
        match_deprecated_images = _dedupe_list(match_deprecated_images)
        match_deleted_images = _dedupe_list(match_deleted_images)

        # if it's not an offer from the marketplace, it's unsupported
        if len(match_active_images) == 0 and len(match_inactive_images) == 0 and len(match_deprecated_images) == 0:
            is_unsupported = True

        # make the final object
        match_data = {
            'name':    name,
            'version': version,
            'active': match_active_images,
            'inactive': match_inactive_images,
            'deprecated': match_deprecated_images,
            'deleted': match_deleted_images,
            'license_type': license_type,
            'unsupported': is_unsupported
        }

        return match_data


if __name__ == "__main__":
    main()
