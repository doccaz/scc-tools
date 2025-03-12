# scc-tools

A set of simple tools to interact with SUSE Customer Center (SCC).

It basically uses the APIs available at https://scc.suse.com/api/package_search/v4/documentation

[![build result](https://build.opensuse.org/projects/home:emendonca/packages/scc-tools/badge.svg?type=default)](https://build.opensuse.org/package/show/home:emendonca/scc-tools)

## vercheck

This tool searches for the latest versions of packages on SCC.

It started as a pet project to do a simple package search with the API, but it evolved into a much more complex tool that can analyze supportconfig archives, correlate product versions and repositories, and generate reports on package versions.

Disclaimer: I'm a SUSE employee.


Usage:
```
# ./vercheck.py [-l|--list-products] -p|--product product id -n|--name <package name> [-s|--short] [-v|--verbose] [-1|--show-unknown] [-2|--show-differences] [-3|--show-uptodate] [-4|--show-unsupported] [-5|--show-suseorphans] [-6|--show-suseptf] [-o|--outputdir] [-d|--supportconfig] [-a|--arch] [-f|--force-refresh] [-V|--version]

```

It uses compression, and a single urllib3 pool instance, to minimize the impact on the public server as much as possible. In order to speed things up, I open multiple threads and consume the RPM list slowly.
I also tried to use all resources that do NOT require authentication, inspired by the public package search at https://scc.suse.com/packages . That is why I opted to use a *static* product list inside the code (which doesn't really change that often).

Vercheck has an internal cache. This was made in order to sidestep current rate-limiting issues on the SCC API servers (issue #22).

This is how it works:
1) a JSON file (scc_data.json) is created/updated to hold cache entries, either in /var/cache/scc-tools or ~/.cache/scc-tools. The directory is selected based on whether it can write to each location, in order of preference.

2) the cache currently holds entries for 5 days. This guarantees that fresh information can be retrieved in a reasonable timeframe if necessary.
Here's an example of an entry being dropped and immediately being queued for a refresh:
```
cached data for zypper is too old (-6 days), discarding cache entry
removing record from cache: {'id': 21851832, 'name': 'zypper', 'arch': 'x86_64', 'version': '1.14.51', 'release': '3.52.1', 'products': [{'id': 2219, 'name': 'SUSE Linux Enterprise Server LTSS', 'identifier': 'SLES-LTSS/15.1/x86_64', 'type': 'extension', 'free': False, 'edition': '15 SP1', 'architecture': 'x86_64'}], 'timestamp': '2022-03-12T02:15:30.193223', 'repository': 'Basesystem Module 15 SP2 x86_6415 SP2x86_64', 'product_id': 1939}
searching for zypper for product ID 1939 in SCC
```
3) the same cache mechanism is implemented for Public Cloud images, using data from SUSE PINT (pint.suse.com). In this case, the information about active/inactive/deprecated/deleted images are kept for 7 days, and automatically refreshed upon running.

4) it also contains an internal table correlating each product to modules (taken from RMT). This is necessary in order to maintain cache consistency, as sometimes a suitable updated package resides in a different module repository, and we need to know what was the original product ID in order to return the correct cache entry.

5) there is an additional command-line option:
```
-f|--force-refresh              Ignore cached data and retrieve latest data from SCC and public cloud info
```
This ignores the cache and goes straight to SCC for the latest data (the results are added to the cache at the end for later use though).

6) it's also heavily multi-threaded, and as such it has a way more complex data locking logic.

*IMPORTANT*: As we discovered through testing, running multiple parallel copies of this version may "lose" some of the recently refreshed cache entries. This limitation is by design. What happens is that in every session I read the cached entries to memory, then write it all at the end. Everything is changed in-memory. So, whoever runs last "wins". This is to avoid thousands of small disk writes, and possibly being called a "disk killer" :-)
In the future I intend to implement a more robust cache backend (sqlite?) and address this. I might also merge it back to a single version of the script.


### Examples

* Listing supported products list (-l or --list):

```
$  ./vercheck.py -l
Known products list
ID      Name
-----------------------------------------------------
1117    SUSE Linux Enterprise Server 12 x86_64
1322    SUSE Linux Enterprise Server 12 SP1 x86_64
1357    SUSE Linux Enterprise Server 12 SP2 x86_64
1421    SUSE Linux Enterprise Server 12 SP3 x86_64
1625    SUSE Linux Enterprise Server 12 SP4 x86_64
1878    SUSE Linux Enterprise Server 12 SP5 x86_64
1319    SUSE Linux Enterprise Server for SAP 12 x86_64
1346    SUSE Linux Enterprise Server for SAP 12 SP1 x86_64
1414    SUSE Linux Enterprise Server for SAP 12 SP2 x86_64
1426    SUSE Linux Enterprise Server for SAP 12 SP3 x86_64
1755    SUSE Linux Enterprise Server for SAP 12 SP4 x86_64
1880    SUSE Linux Enterprise Server for SAP 12 SP5 x86_64
1575    SUSE Linux Enterprise Server 15 x86_64
1763    SUSE Linux Enterprise Server 15 SP1 x86_64
1939    SUSE Linux Enterprise Server 15 SP2 x86_64
...

As of Oct 2023, 103 products are supported.
```

Note: SLE 11 and derivatives are not supported for queries by the API, even though there are valid product numbers for it.

*  Checking for the latest version of the package "glibc" for product 2465 (SLES 15 SP5 x86_64), verbose mode:

```
$ ./vercheck.py -p 2465 -n glibc -v
Using product ID 2465 (SUSE Linux Enterprise Server 15 SP5 x86_64)
searching for package "glibc" in product id "2465" (SUSE Linux Enterprise Server 15 SP5 x86_64)
found glibc for product ID 2465 (cached)
latest version for glibc on product ID 2465(SUSE Linux Enterprise Server 15 SP5 x86_64) is 2.31-150300.46.1, found on Basesystem Module (sle-module-basesystem/15.5/x86_64)
version 2.31-150300.46.1 is available on repository [Basesystem Module 15 SP5 x86_64 15 SP5 x86_64]

```

Note that it correctly treats second- and third-order release numbers, and sorts them accordingly to get the latest version.


* Checking for the latest version of the package "glibc" for product 2465 (SLES 15 SP5 x86_64), short answer:
```
$ ./vercheck.py -p 2465 -n glibc -s
searching for package "glibc" in product id "2465" (SUSE Linux Enterprise Server 15 SP5 x86_64)
searching for glibc for product ID 2465 in SCC
2.31-150300.63.1

```

* Analyzing a supportconfig
```
$ ./vercheck.py -d tests/SLE15SP5/scc_rmt_231027_1743
loaded 2628 items from cache (/home/erico/.cache/scc-tools/scc_data.json)
loaded 5 items from cache (/home/erico/.cache/scc-tools/public_cloud_amazon.json)
* cached data OK (-4 days old)
loaded 5 items from cache (/home/erico/.cache/scc-tools/public_cloud_google.json)
* cached data OK (-4 days old)
loaded 5 items from cache (/home/erico/.cache/scc-tools/public_cloud_microsoft.json)
* cached data OK (-4 days old)
--- AMAZON data as of 2023-10-27T17:24:07.180514
* 1468 active images
* 942 inactive images
* 9060 deprecated images
* 14763 deleted images

--- MICROSOFT data as of 2023-10-27T17:24:07.180514
* 187 active images
* 147 inactive images
* 548 deprecated images
* 4543 deleted images

--- GOOGLE data as of 2023-10-27T17:24:07.180514
* 33 active images
* 26 inactive images
* 106 deprecated images
* 708 deleted images

--> Public cloud provider for tests/SLE15SP5/scc_rmt_231027_1743 is [none]
--> not a public cloud image, continuing normal analysis
Analyzing supportconfig directory: tests/SLE15SP5/scc_rmt_231027_1743
product name = SUSE Linux Enterprise Server 15 SP5 x86_64 (id 2465, x86_64)
found 986 total packages to check
found Mesa-dri for product ID 2465 (cached)
found Mesa for product ID 2465 (cached)
found Mesa-gallium for product ID 2465 (cached)
found Mesa-libEGL1 for product ID 2465 (cached)
found Mesa-libGL1 for product ID 2465 (cached)
found Mesa-libglapi0 for product ID 2465 (cached)
...
thread search-yast2-ycp-ui-bindings is done
thread search-zisofs-tools is done
thread search-zstd is done
thread search-zypper is done
thread search-zypper-lifecycle-plugin is done
thread search-zypper-log is done
thread search-zypper-needs-restarting is done

Done.
writing CSV reports to /home/erico/Projetos/scc-tools


```

This option analyzes a previously extracted supportconfig report. It will find the installed RPMs in the report, and run searches on ALL packages in order to find which ones are up-to-date, have older versions, or are not found in the official repositories. Packages that are from unsupported vendors also get their own report. Packages that are orphans (as in, packages that belong to another version of the OS and were left installed) and PTF (Program Temporary Fix) packages built by SUSE also have a separate report.

It generates these six CSV reports:
* vercheck-uptodate-[directory name].csv,
* vercheck-different-[directory name].csv,
* vercheck-notfound-[directory name].csv,
* vercheck-unsupported-[directory name].csv,
* vercheck-suseorphans-[directory name].csv, and
* vercheck-suseptf-[directory name].csv

respectively.

An output directory can be specified by adding the "-o" (or --outputdir) parameter before the supportconfig directory:
```
 ./vercheck.py -o /tmp/reports -d ~/Documents/nts_dxl1lnxsl002_200616_1148
```

## Requirements

Dependencies: This utility depends on urllib3 and pyaml. It also uses zypper as a last-resort mechanism to verify versions. Therefore it will **not** run on e.g. Debian based systems.

For Tumbleweed 03/25 this is the working pyaml RPM:

    zypper in python313-yamlcore


## Final considerations

This utility only uses public resources maintained by SUSE LLC, no logins are necessary.

I make no guarantees on availability or speed. I try to make sure that the information mined by vercheck is as accurate as possible, but errors can occur.

If you find a bug or inconsistency, please open an issue! https://github.com/doccaz/scc-tools/issues

// **end** //
