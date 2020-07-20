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
# ./vercheck.py -l
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
2117    SUSE Linux Enterprise Server 12 LTSS x86_64
2056    SUSE Linux Enterprise Server 15 LTSS x86_64
total: 20 products.
``` 

*  Checking for the latest version of the package "glibc" for product 1421 (SLES 12 SP3 x86_64):

```
erico@suselab-erico:~/Projetos/scc-tools> ./vercheck.py -p 1421 -n glibc
version 2.22-62.6.2 is available
version 2.22-62.3.4 is available
version 2.22-62.19.1 is available
version 2.22-62.16.2 is available
version 2.22-62.13.2 is available
version 2.22-62.10.1 is available
version 2.22-61.3 is available
latest version for glibc is 2.22-62.6.2
```

* Checking for the latest version of the package "glibc" for product 1421 (SLES 12 SP3 x86_64) -- short answer:
```
# ./vercheck.py -p 1421 -n glibc -s
2.22-62.6.2
```
