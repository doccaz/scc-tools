# scc-tools

A set of simple tools to interact with SUSE Customer Center (SCC).

It basically uses the APIs available at https://scc.suse.com/api/package_search/v4/documentation

## vercheck

This tool searches for the latest version of a package, for one specific product.

Usage: 
```
# Usage: vercheck.py [-l|--list-products] -p|--product=product id -n|--name <package name> [-s|--short] [-v|--verbose]
```

### Examples


* Listing supported products list (-l or --list):

```
#  ./vercheck.py -l
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
1612    SUSE Linux Enterprise Server for SAP 15 x86_64
1766    SUSE Linux Enterprise Server for SAP 15 SP1 x86_64
1941    SUSE Linux Enterprise Server for SAP 15 SP2 x86_64
total: 18 products.
``` 

Note: SLE 11 and derivatives are not supported for queries by the API, even though there are valid product numbers for it.

*  Checking for the latest version of the package "glibc" for product 1421 (SLES 12 SP3 x86_64), verbose mode:

```
# ./vercheck.py -p 1421 -n glibc -v
Using product ID 1421 (SUSE Linux Enterprise Server 12 SP3 x86_64)
looking for glibc on product id 1421
version 2.22-62.6.2 is available on repository [SUSE Linux Enterprise Server 12 SP3 x86_64]
version 2.22-62.3.4 is available on repository [SUSE Linux Enterprise Server 12 SP3 x86_64]
version 2.22-62.22.5 is available on repository [SUSE Linux Enterprise Server LTSS 12 SP3 x86_64]
version 2.22-62.22.5 is available on repository [SUSE Linux Enterprise Point of Service Image Server 12 SP2 x86_64]
version 2.22-62.22.5 is available on repository [SUSE Enterprise Storage 5 x86_64]
version 2.22-62.22.5 is available on repository [SUSE OpenStack Cloud 8 x86_64]
version 2.22-62.22.5 is available on repository [HPE Helion OpenStack 8 x86_64]
version 2.22-62.22.5 is available on repository [SUSE Linux Enterprise Server BCL 12 SP3 x86_64]
version 2.22-62.22.5 is available on repository [SUSE OpenStack Cloud Crowbar 8 x86_64]
version 2.22-62.19.1 is available on repository [SUSE Linux Enterprise Point of Service Image Server 12 SP2 x86_64]
version 2.22-62.19.1 is available on repository [SUSE Linux Enterprise Server 12 SP3 x86_64]
version 2.22-62.16.2 is available on repository [SUSE Linux Enterprise Server 12 SP3 x86_64]
version 2.22-62.13.2 is available on repository [SUSE Linux Enterprise Server 12 SP3 x86_64]
version 2.22-62.13.2 is available on repository [SUSE Linux Enterprise Point of Service Image Server 12 SP2 x86_64]
version 2.22-62.10.1 is available on repository [SUSE Linux Enterprise Server 12 SP3 x86_64]
version 2.22-61.3 is available on repository [SUSE Linux Enterprise Server 12 SP3 x86_64]
latest version for glibc is 2.22-62.22.5
```

Note that it correctly treats second- and third-order release numbers, and sorts them accordingly to get the latest version.


* Checking for the latest version of the package "glibc" for product 1421 (SLES 12 SP3 x86_64), short answer:
```
# ./vercheck.py -p 1421 -n glibc -s
2.22-62.22.5

```

* Analyzing a supportconfig
```
 ./vercheck.py -d ~/Documents/nts_dxl1lnxsl002_200616_1148 
Analyzing supportconfig directory: /home/erico/Documents/nts_dxl1lnxsl002_200616_1148
product name = SUSE Linux Enterprise Server 15 SP1 x86_64 (1763)
found 498 total packages to check
[1/498] BBbigfix-conf-x86: not found
[2/498] BBcerts: not found
[3/498] BBpkicerts: not found
[4/498] BESAgent: not found
[5/498] GeoIP: current version is 1.6.12-4.17 (latest: 1.6.12-6.3.1)
[6/498] GeoIP-data: current version is 1.6.12-4.17 (latest: 1.6.12-6.3.1)
[7/498] SUSEConnect: current version is 0.3.17-3.16.1 (latest: 0.3.22-7.9.1)
[8/498] aaa_base: current version is 84.87+git20180409.04c9dae-3.9.1 (latest: 84.87+git20180409.04c9dae-3.39.1)
[9/498] aaa_base-extras: current version is 84.87+git20180409.04c9dae-3.9.1 (latest: 84.87+git20180409.04c9dae-3.39.1)
[10/498] apache2: current version is 2.4.33-3.18.2 (latest: 2.4.33-3.30.1)
...
[493/498] zypper: current version is 1.14.36-3.16.9 (latest: 1.14.37-3.19.1)
[494/498] zypper-lifecycle-plugin: up-to-date (0.6.1490613702.a925823-2.43)
[495/498] zypper-log: current version is 1.14.36-3.16.9 (latest: 1.14.37-3.19.1)
[496/498] zypper-migration-plugin: current version is 0.12.1580220831.7102be8-6.4.1 (latest: 0.12.1590748670.86b0749-6.7.1)
[497/498] zypper-needs-restarting: current version is 1.14.30-3.7.2 (latest: 1.14.37-3.19.1)
[498/498] zypper-search-packages-plugin: up-to-date (0.7-5.35)
up-to-date:249 packages
not found:6 packages
different:243 packages
```

This option analyzes a previously extracted supportconfig report. It will find the installed RPMs in the report, and run
searches on ALL packages in order to find which ones are up-to-date, have older versions, or are not found in the official
repositories.

It generates 3 CSV reports: uptodate.csv, different.csv and notfound.csv, respectively.

