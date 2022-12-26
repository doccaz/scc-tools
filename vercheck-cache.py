#!/usr/bin/python3
import re
import sys, os, time
from threading import Thread, Lock, active_count
from contextlib import contextmanager
import urllib3, urllib
import json
import getopt
import signal
from distutils.version import LooseVersion
import subprocess
from datetime import datetime
#import socket
#from urllib3.connection import HTTPConnection
import pdb
import weakref
import warnings

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

	# all known module IDs, and corresponding product IDs (from RMT)
	sle_modules_by_product_list = {
        1522: { 'name': 'HPC Module 12 aarch64', 'edition': '12', 'architecture': 'aarch64', 'products': [1375, 1424, 1628, 1875]},
		1539: { 'name': 'Web and Scripting Module 12 aarch64', 'edition': '12', 'architecture': 'aarch64', 'products': [1375, 1424, 1628, 1875]}, 
		1528: { 'name': 'Public Cloud Module 12 aarch64', 'edition': '12', 'architecture': 'aarch64', 'products': [1375, 1424, 1628, 1875]}, 
		1376: { 'name': 'Toolchain Module 12 aarch64', 'edition': '12', 'architecture': 'aarch64', 'products': [1375, 1424, 1628, 1875]}, 
    
       	1148: { 'name': 'Legacy Module 12 ppc64le', 'edition': '12', 'architecture': 'ppc64le', 'products': [1116]},
		1151: { 'name': 'Web and Scripting Module 12 ppc64le', 'edition': '12', 'architecture': 'ppc64le', 'products': [1116]}, 
		1218: { 'name': 'Public Cloud Module 12 ppc64le', 'edition': '12', 'architecture': 'ppc64le', 'products': [1116]}, 
		1294: { 'name': 'Advanced Systems Management Module 12 ppc64le', 'edition': '12', 'architecture': 'ppc64le', 'products':[1116]},
		1339: { 'name': 'Toolchain Module 12 ppc64le', 'edition': '12', 'architecture': 'ppc64le', 'products': [1116]}, 
    	1353: { 'name': 'Containers Module 12 ppc64le', 'edition': '12', 'architecture': 'ppc64le', 'products': [1116]}, 
		1367: { 'name': 'Certifications Module 12 ppc64le', 'edition': '12', 'architecture': 'ppc64le', 'products': [1116]},
    
  		1149: { 'name': 'Legacy Module 12 s390x', 'edition': '12', 'architecture': 's390x', 'products': [1115]},
		1152: { 'name': 'Web and Scripting Module 12 s390x', 'edition': '12', 'architecture': 's390x', 'products': [1115]}, 
		1295: { 'name': 'Advanced Systems Management Module 12 s390x', 'edition': '12', 'architecture': 's390x', 'products':[ 1115]},
		1340: { 'name': 'Toolchain Module 12 s390x', 'edition': '12', 'architecture': 's390x', 'products': [1115]}, 
    	1354: { 'name': 'Containers Module 12 s390x', 'edition': '12', 'architecture': 's390x', 'products': [1115]}, 
		1367: { 'name': 'Certifications Module 12 s390x', 'edition': '12', 'architecture': 's390x', 'products': [1115]},
  		1474: { 'name': 'SUSE Package Hub 12 s390x', 'edition': '12', 'architecture': 's390x', 'products': [1115]},
    
    	1477: { 'name': 'SUSE Package Hub 12 SP1 s390x', 'edition': '12 SP1', 'architecture': 's390x', 'products': [1335]},
    	1480: { 'name': 'SUSE Package Hub 12 SP2 s390x', 'edition': '12 SP2', 'architecture': 's390x', 'products': [1356]},
    	1530: { 'name': 'SUSE Package Hub 12 SP3 s390x', 'edition': '12 SP3', 'architecture': 's390x', 'products': [1423]},
    	1812: { 'name': 'SUSE Package Hub 12 SP4 s390x', 'edition': '12 SP4', 'architecture': 's390x', 'products': [1627]},
    	1914: { 'name': 'SUSE Package Hub 12 SP5 s390x', 'edition': '12 SP5', 'architecture': 's390x', 'products': [1877]},
       
		1150: { 'name': 'Legacy Module 12 x86_64', 'edition': '12', 'architecture': 'x86_64', 'products': [1117, 1118, 1319]},
		1153: { 'name': 'Web and Scripting Module 12 x86_64', 'edition': '12', 'architecture': 'x86_64', 'products': [1117, 1118, 1319]},
		1212: { 'name': 'Advanced Systems Management Module 12 x86_64', 'edition': '12', 'architecture': 'x86_64', 'products': [1117, 1118, 1319]},
		1220: { 'name': 'Public Cloud Module 12 x86_64', 'edition': '12', 'architecture': 'x86_64', 'products': [1117, 1118, 1319]},
		1332: { 'name': 'Containers Module 12 x86_64', 'edition': '12', 'architecture': 'x86_64', 'products': [1117, 1118, 1319]},
		1341: { 'name': 'Toolchain Module 12 x86_64', 'edition': '12', 'architecture': 'x86_64', 'products': [1117, 1118, 1319]},
		1368: { 'name': 'Certifications Module 12 x86_64', 'edition': '12', 'architecture': 'x86_64', 'products': [1117, 1118, 1319]},
		1440: { 'name': 'HPC Module 12 x86_64', 'edition': '12', 'architecture': 'x86_64', 'products': [1117, 1118, 1319]},
		1473: { 'name': 'SUSE Package Hub 12 x86_64', 'edition': '12', 'architecture': 'x86_64', 'products': [1117, 1118, 1319]},

		1476: { 'name': 'SUSE Package Hub 12 SP1 x86_64', 'edition': '12 SP1', 'architecture': 'x86_64', 'products': [1333, 1322, 1346]},
		1479: { 'name': 'SUSE Package Hub 12 SP2 x86_64', 'edition': '12 SP2', 'architecture': 'x86_64', 'products': [1358, 1749, 1438, 1357]},
		1529: { 'name': 'SUSE Package Hub 12 SP3 x86_64', 'edition': '12 SP3', 'architecture': 'x86_64', 'products': [1425, 1751, 1619, 1421, 1426]},
		1813: { 'name': 'SUSE Package Hub 12 SP4 x86_64', 'edition': '12 SP4', 'architecture': 'x86_64', 'products': [1629, 1759, 1924, 1625, 1755, 2117]},
		1915: { 'name': 'SUSE Package Hub 12 SP5 x86_64', 'edition': '12 SP5', 'architecture': 'x86_64', 'products': [2020, 1873, 2006, 1878, 1880]},

		1587: { 'name': 'Basesystem Module 15 s390x', 'edition': '15', 'architecture': 's390x', 'products': [1584]}, 
		1593: { 'name': 'Desktop Applications Module 15 s390x', 'edition': '15', 'architecture': 's390x', 'products': [1584]}, 
		1596: { 'name': 'Development Tools Module 15 s390x', 'edition': '15', 'architecture': 's390x', 'products': [1584]}, 
		1599: { 'name': 'Server Applications Module 15 s390x', 'edition': '15', 'architecture': 's390x', 'products': [1584]}, 
		1602: { 'name': 'Legacy Module 15 s390x', 'edition': '15', 'architecture': 's390x', 'products': [1584]}, 
		1641: { 'name': 'Containers Module 15 s390x', 'edition': '15', 'architecture': 's390x', 'products': [1584]}, 
		1646: { 'name': 'Public Cloud Module 15 s390x', 'edition': '15', 'architecture': 's390x', 'products': [1584]}, 
		1720: { 'name': 'Web and Scripting Module 15 s390x', 'edition': '15', 'architecture': 's390x', 'products': [1584]}, 
		1742: { 'name': 'SUSE Package Hub 15 s390x', 'edition': '15', 'architecture': 's390x', 'products': [1584]}, 

		1589: { 'name': 'Basesystem Module 15 aarch64', 'edition': '15', 'architecture': 'aarch64', 'products': [1586]},
		1595: { 'name': 'Desktop Applications Module 15 aarch64', 'edition': '15', 'architecture': 'aarch64', 'products': [1586]},
		1598: { 'name': 'Development Tools Module 15 aarch64', 'edition': '15', 'architecture': 'aarch64', 'products': [1586]},
		1601: { 'name': 'Server Applications Module 15 aarch64', 'edition': '15', 'architecture': 'aarch64', 'products': [1586]},
		1604: { 'name': 'Legacy Module 15 aarch64', 'edition': '15', 'architecture': 'aarch64', 'products': [1586]},
		1645: { 'name': 'Public Cloud Module 15 aarch64', 'edition': '15', 'architecture': 'aarch64', 'products': [1586]},
		1718: { 'name': 'Web and Scripting Module 15 aarch64', 'edition': '15', 'architecture': 'aarch64', 'products': [1586]},
		1733: { 'name': 'HPC Module 15 aarch64', 'edition': '15', 'architecture': 'aarch64', 'products': [1586]},
        1740: { 'name': 'SUSE Package Hub 15 aarch64', 'edition': '15', 'architecture': 'aarch64', 'products': [1586]},

		1576: { 'name': 'Basesystem Module 15 x86_64', 'edition': '15', 'architecture': 'x86_64', 'products': [1612, 1575, 1609, 1732, 2056]},
		1578: { 'name': 'Desktop Applications Module 15 x86_64', 'edition': '15', 'architecture': 'x86_64', 'products': [1612, 1575, 1609, 1732, 2056]},
		1579: { 'name': 'Development Tools Module 15 x86_64', 'edition': '15', 'architecture': 'x86_64', 'products': [1612, 1575, 1609, 1732, 2056]},
		1580: { 'name': 'Server Applications Module 15 x86_64', 'edition': '15', 'architecture': 'x86_64', 'products': [1612, 1575, 1609, 1732, 2056]},
		1581: { 'name': 'Legacy Module 15 x86_64', 'edition': '15', 'architecture': 'x86_64', 'products': [1612, 1575, 1609, 1732, 2056]},
		1611: { 'name': 'Public Cloud Module 15 x86_64', 'edition': '15', 'architecture': 'x86_64', 'products': [1612, 1575, 1609, 1732, 2056]},
		1642: { 'name': 'Containers Module 15 x86_64', 'edition': '15', 'architecture': 'x86_64', 'products': [1612, 1575, 1609, 1732, 2056]},
		1721: { 'name': 'Web and Scripting Module 15 x86_64', 'edition': '15', 'architecture': 'x86_64', 'products': [1612, 1575, 1609, 1732, 2056]},
		1734: { 'name': 'HPC Module 15 x86_64', 'edition': '15', 'architecture': 'x86_64', 'products': [1612, 1575, 1609, 1732, 2056]},
		2131: { 'name': 'NVIDIA Compute Module 15 x86_64', 'edition': '15', 'architecture': 'x86_64', 'products': [1612, 1575, 1609, 1732, 2056]},  
 		1727: { 'name': 'SAP Applications Module 15 x86_64', 'edition': '15', 'architecture': 'x86_64', 'products': [1612, 1575, 1609, 1732, 2056]},
		1728: { 'name': 'SUSE Cloud Application Platform Tools Module 15 x86_64', 'edition': '15', 'architecture': 'x86_64', 'products': [1612, 1575, 1609, 1732, 2056]},
		1743: { 'name': 'SUSE Package Hub 15 x86_64', 'edition': '15', 'architecture': 'x86_64', 'products': [1612, 1575, 1609, 1732, 2056]},

		1771: { 'name': 'Basesystem Module 15 SP1 s390x', 'edition': '15 SP1', 'architecture': 's390x', 'products': [1762]}, 
		1775: { 'name': 'Desktop Applications Module 15 SP1 s390x', 'edition': '15 SP1', 'architecture': 's390x', 'products': [1762]}, 
		1779: { 'name': 'Server Applications Module 15 SP1 s390x', 'edition': '15 SP1', 'architecture': 's390x', 'products': [1762]}, 
		1789: { 'name': 'Containers Module 15 SP1 s390x', 'edition': '15 SP1', 'architecture': 's390x', 'products': [1762]}, 
		1793: { 'name': 'Development Tools Module 15 SP1 s390x', 'edition': '15 SP1', 'architecture': 's390x', 'products': [1762]}, 
		1797: { 'name': 'Web and Scripting Module 15 SP1 s390x', 'edition': '15 SP1', 'architecture': 's390x', 'products': [1762]}, 
		1803: { 'name': 'Legacy Module 15 SP1 s390x', 'edition': '15 SP1', 'architecture': 's390x', 'products': [1762]}, 
		1807: { 'name': 'Public Cloud Module 15 SP1 s390x', 'edition': '15 SP1', 'architecture': 's390x', 'products': [1762]}, 
		1824: { 'name': 'Transactional Server Module 15 SP1 s390x', 'edition': '15 SP1', 'architecture': 's390x', 'products': [1762]}, 
		1866: { 'name': 'Python 2 Module 15 SP1 s390x', 'edition': '15 SP1', 'architecture': 's390x', 'products': [1762]}, 
  		1870: { 'name': 'SUSE Package Hub 15 SP1 s390x', 'edition': '15 SP1', 'architecture': 's390x', 'products': [1762]}, 
  
  		1769: { 'name': 'Basesystem Module 15 SP1 aarch64', 'edition': '15 SP1', 'architecture': 'aarch64', 'products': [1760]}, 
		1773: { 'name': 'Desktop Applications Module 15 SP1 aarch64', 'edition': '15 SP1', 'architecture': 'aarch64', 'products': [1760]}, 
		1777: { 'name': 'Server Applications Module 15 SP1 aarch64', 'edition': '15 SP1', 'architecture': 'aarch64', 'products': [1760]}, 
		1920: { 'name': 'Containers Module 15 SP1 aarch64', 'edition': '15 SP1', 'architecture': 'aarch64', 'products': [1760]}, 
		1791: { 'name': 'Development Tools Module 15 SP1 aarch64', 'edition': '15 SP1', 'architecture': 'aarch64', 'products': [1760]}, 
		1795: { 'name': 'Web and Scripting Module 15 SP1 aarch64', 'edition': '15 SP1', 'architecture': 'aarch64', 'products': [1760]}, 
		1801: { 'name': 'Legacy Module 15 SP1 aarch64', 'edition': '15 SP1', 'architecture': 'aarch64', 'products': [1760]}, 
		1805: { 'name': 'Public Cloud Module 15 SP1 aarch64', 'edition': '15 SP1', 'architecture': 'aarch64', 'products': [1760]}, 
		1822: { 'name': 'Transactional Server Module 15 SP1 aarch64', 'edition': '15 SP1', 'architecture': 'aarch64', 'products': [1760]}, 
		1864: { 'name': 'Python 2 Module 15 SP1 aarch64', 'edition': '15 SP1', 'architecture': 'aarch64', 'products': [1760]},
  		1799: { 'name': 'HPC Module 15 SP1 aarch64', 'edition': '15 SP1', 'architecture': 'aarch64', 'products': [1760]},  
        1868: { 'name': 'SUSE Package Hub 15 SP1 aarch64', 'edition': '15 SP1', 'architecture': 'aarch64', 'products': [1760]},

		1772: { 'name': 'Basesystem Module 15 SP1 x86_64', 'edition': '15 SP1', 'architecture': 'x86_64', 'products': [1766, 1763, 1764, 1768, 1861]},
		1776: { 'name': 'Desktop Applications Module 15 SP1 x86_64', 'edition': '15 SP1', 'architecture': 'x86_64', 'products': [1766, 1763, 1764, 1768, 1861]},
		1790: { 'name': 'Containers Module 15 SP1 x86_64', 'edition': '15 SP1', 'architecture': 'x86_64', 'products': [1766, 1763, 1764, 1768, 1861]},
		1794: { 'name': 'Development Tools Module 15 SP1 x86_64', 'edition': '15 SP1', 'architecture': 'x86_64', 'products': [1766, 1763, 1764, 1768, 1861]},
		1780: { 'name': 'Server Applications Module 15 SP1 x86_64', 'edition': '15 SP1', 'architecture': 'x86_64', 'products': [1766, 1763, 1764, 1768, 1861]},
		1798: { 'name': 'Web and Scripting Module 15 SP1 x86_64', 'edition': '15 SP1', 'architecture': 'x86_64', 'products': [1766, 1763, 1764, 1768, 1861]},
		1800: { 'name': 'HPC Module 15 SP1 x86_64', 'edition': '15 SP1', 'architecture': 'x86_64', 'products': [1766, 1763, 1764, 1768, 1861]},
		1804: { 'name': 'Legacy Module 15 SP1 x86_64', 'edition': '15 SP1', 'architecture': 'x86_64', 'products': [1766, 1763, 1764, 1768, 1861]},
		1808: { 'name': 'Public Cloud Module 15 SP1 x86_64', 'edition': '15 SP1', 'architecture': 'x86_64', 'products': [1766, 1763, 1764, 1768, 1861]},
		1809: { 'name': 'SUSE Cloud Application Platform Tools Module 15 SP1 x86_64', 'edition': '15 SP1', 'architecture': 'x86_64', 'products': [1766, 1763, 1764, 1768, 1861]},
		1825: { 'name': 'Transactional Server Module 15 SP1 x86_64', 'edition': '15 SP1', 'architecture': 'x86_64', 'products': [1766, 1763, 1764, 1768, 1861]},
		1867: { 'name': 'Python 2 Module 15 SP1 x86_64', 'edition': '15 SP1', 'architecture': 'x86_64', 'products': [1766, 1763, 1764, 1768, 1861]},
		1787: { 'name': 'SAP Applications Module 15 SP1 x86_64', 'edition': '15 SP1', 'architecture': 'x86_64', 'products': [1766, 1763, 1764, 1768, 1861]},   
		1862: { 'name': 'SUSE Real Time Module 15 SP1 x86_64', 'edition': '15 SP1', 'architecture': 'x86_64', 'products': [1766, 1763, 1764, 1768, 1861]},  
		1871: { 'name': 'SUSE Package Hub 15 SP1 x86_64', 'edition': '15 SP1', 'architecture': 'x86_64', 'products': [1766, 1763, 1764, 1768, 1861]},
  
		1945: { 'name': 'Basesystem Module 15 SP2 s390x', 'edition': '15 SP2', 'architecture': 's390x', 'products': [1938]}, 
		1962: { 'name': 'Containers Module 15 SP2 s390x', 'edition': '15 SP2', 'architecture': 's390x', 'products': [1938]}, 
		1966: { 'name': 'Desktop Applications Module 15 SP2 s390x', 'edition': '15 SP2', 'architecture': 's390x', 'products': [1938]}, 
		1970: { 'name': 'Development Tools Module 15 SP2 s390x', 'edition': '15 SP2', 'architecture': 's390x', 'products': [1938]}, 
		1981: { 'name': 'Legacy Module 15 SP2 s390x', 'edition': '15 SP2', 'architecture': 's390x', 'products': [1938]}, 
		1987: { 'name': 'Public Cloud Module 15 SP2 s390x', 'edition': '15 SP2', 'architecture': 's390x', 'products': [1938]}, 
		1991: { 'name': 'Python 2 Module 15 SP2 s390x', 'edition': '15 SP2', 'architecture': 's390x', 'products': [1938]}, 
		1954: { 'name': 'Server Applications Module 15 SP2 s390x', 'edition': '15 SP2', 'architecture': 's390x', 'products': [1938]}, 
		1975: { 'name': 'Web and Scripting Module 15 SP2 s390x', 'edition': '15 SP2', 'architecture': 's390x', 'products': [1938]}, 
		1997: { 'name': 'Transactional Server Module 15 SP2 s390x', 'edition': '15 SP2', 'architecture': 's390x', 'products': [1938]},
  		1949: { 'name': 'SUSE Package Hub 15 SP2 s390x', 'edition': '15 SP2', 'architecture': 's390x', 'products': [1938]},  

  		1943: { 'name': 'Basesystem Module 15 SP2 aarch64', 'edition': '15 SP2', 'architecture': 'aarch64', 'products': [1936]}, 
		1964: { 'name': 'Desktop Applications Module 15 SP2 aarch64', 'edition': '15 SP2', 'architecture': 'aarch64', 'products': [1936]}, 
		1952: { 'name': 'Server Applications Module 15 SP2 aarch64', 'edition': '15 SP2', 'architecture': 'aarch64', 'products': [1936]}, 
		1960: { 'name': 'Containers Module 15 SP2 aarch64', 'edition': '15 SP2', 'architecture': 'aarch64', 'products': [1936]}, 
		1968: { 'name': 'Development Tools Module 15 SP2 aarch64', 'edition': '15 SP2', 'architecture': 'aarch64', 'products': [1936]}, 
		1973: { 'name': 'Web and Scripting Module 15 SP2 aarch64', 'edition': '15 SP2', 'architecture': 'aarch64', 'products': [1936]}, 
		1979: { 'name': 'Legacy Module 15 SP2 aarch64', 'edition': '15 SP2', 'architecture': 'aarch64', 'products': [1936]}, 
		1985: { 'name': 'Public Cloud Module 15 SP2 aarch64', 'edition': '15 SP2', 'architecture': 'aarch64', 'products': [1936]}, 
		1995: { 'name': 'Transactional Server Module 15 SP2 aarch64', 'edition': '15 SP2', 'architecture': 'aarch64', 'products': [1936]}, 
		1989: { 'name': 'Python 2 Module 15 SP2 aarch64', 'edition': '15 SP2', 'architecture': 'aarch64', 'products': [1936]},
  		1933: { 'name': 'HPC Module 15 SP2 aarch64', 'edition': '15 SP2', 'architecture': 'aarch64', 'products': [1936]},  
        1947: { 'name': 'SUSE Package Hub 15 SP2 aarch64', 'edition': '15 SP2', 'architecture': 'aarch64', 'products': [1936]},

		1946: { 'name': 'Basesystem Module 15 SP2 x86_64', 'edition': '15 SP2', 'architecture': 'x86_64', 'products': [1941, 1939, 1935, 1934, 2003]},
		1955: { 'name': 'Server Applications Module 15 SP2 x86_64', 'edition': '15 SP2', 'architecture': 'x86_64', 'products': [1941, 1939, 1935, 1934, 2003]},
		1963: { 'name': 'Containers Module 15 SP2 x86_64', 'edition': '15 SP2', 'architecture': 'x86_64', 'products': [1941, 1939, 1935, 1934, 2003]},
		1967: { 'name': 'Desktop Applications Module 15 SP2 x86_64', 'edition': '15 SP2', 'architecture': 'x86_64', 'products': [1941, 1939, 1935, 1934, 2003]},
		1971: { 'name': 'Development Tools Module 15 SP2 x86_64', 'edition': '15 SP2', 'architecture': 'x86_64', 'products': [1941, 1939, 1935, 1934, 2003]},
		1976: { 'name': 'Web and Scripting Module 15 SP2 x86_64', 'edition': '15 SP2', 'architecture': 'x86_64', 'products': [1941, 1939, 1935, 1934, 2003]},
		1978: { 'name': 'HPC Module 15 SP2 x86_64', 'edition': '15 SP2', 'architecture': 'x86_64', 'products': [1941, 1939, 1935, 1934, 2003]},
		1982: { 'name': 'Legacy Module 15 SP2 x86_64', 'edition': '15 SP2', 'architecture': 'x86_64', 'products': [1941, 1939, 1935, 1934, 2003]},
		1988: { 'name': 'Public Cloud Module 15 SP2 x86_64', 'edition': '15 SP2', 'architecture': 'x86_64', 'products': [1941, 1939, 1935, 1934, 2003]},
		1992: { 'name': 'Python 2 Module 15 SP2 x86_64', 'edition': '15 SP2', 'architecture': 'x86_64', 'products': [1941, 1939, 1935, 1934, 2003]},
		1998: { 'name': 'Transactional Server Module 15 SP2 x86_64', 'edition': '15 SP2', 'architecture': 'x86_64', 'products': [1941, 1939, 1935, 1934, 2003]},
		2075: { 'name': 'SUSE Cloud Application Platform Tools Module 15 SP2 x86_64', 'edition': '15 SP2', 'architecture': 'x86_64', 'products': [1941, 1939, 1935, 1934, 2003]},
		1994: { 'name': 'SAP Applications Module 15 SP2 x86_64', 'edition': '15 SP2', 'architecture': 'x86_64', 'products': [1941, 1939, 1935, 1934, 2003]},  
		2005: { 'name': 'SUSE Real Time Module 15 SP2 x86_64', 'edition': '15 SP2', 'architecture': 'x86_64', 'products': [1941, 1939, 1935, 1934, 2003]},  
		1950: { 'name': 'SUSE Package Hub 15 SP2 x86_64', 'edition': '15 SP2', 'architecture': 'x86_64', 'products': [1941, 1939, 1935, 1934, 2003]},

		2144: { 'name': 'Basesystem Module 15 SP3 s390x', 'edition': '15 SP3', 'architecture': 's390x', 'products': [2139]}, 
		2148: { 'name': 'Desktop Applications Module 15 SP3 s390x', 'edition': '15 SP3', 'architecture': 's390x', 'products': [2139]}, 
		2152: { 'name': 'Server Applications Module 15 SP3 s390x', 'edition': '15 SP3', 'architecture': 's390x', 'products': [2139]}, 
		2156: { 'name': 'Containers Module 15 SP3 s390x', 'edition': '15 SP3', 'architecture': 's390x', 'products': [2139]}, 
  		2388: { 'name': 'Certifications Module 15 SP3 s390x', 'edition': '15 SP3', 'architecture': 's390x', 'products': [2139]}, 
		2160: { 'name': 'Development Tools Module 15 SP3 s390x', 'edition': '15 SP3', 'architecture': 's390x', 'products': [2139]}, 
		2164: { 'name': 'Web and Scripting Module 15 SP3 s390x', 'edition': '15 SP3', 'architecture': 's390x', 'products': [2139]}, 
		2170: { 'name': 'Legacy Module 15 SP3 s390x', 'edition': '15 SP3', 'architecture': 's390x', 'products': [2139]}, 
		2174: { 'name': 'Public Cloud Module 15 SP3 s390x', 'edition': '15 SP3', 'architecture': 's390x', 'products': [2139]}, 
		2179: { 'name': 'Transactional Server Module 15 SP3 s390x', 'edition': '15 SP3', 'architecture': 's390x', 'products': [2139]}, 
		2183: { 'name': 'Python 2 Module 15 SP3 s390x', 'edition': '15 SP3', 'architecture': 's390x', 'products': [2139]}, 
		2190: { 'name': 'SUSE Package Hub 15 SP3 s390x', 'edition': '15 SP3', 'architecture': 's390x', 'products': [2139]}, 

		2142: { 'name': 'Basesystem Module 15 SP3 aarch64', 'edition': '15 SP3', 'architecture': 'aarch64', 'products': [2137]}, 
		2146: { 'name': 'Desktop Applications Module 15 SP3 aarch64', 'edition': '15 SP3', 'architecture': 'aarch64', 'products': [2137]}, 
		2150: { 'name': 'Server Applications Module 15 SP3 aarch64', 'edition': '15 SP3', 'architecture': 'aarch64', 'products': [2137]}, 
		2154: { 'name': 'Containers Module 15 SP3 aarch64', 'edition': '15 SP3', 'architecture': 'aarch64', 'products': [2137]}, 
		2158: { 'name': 'Development Tools Module 15 SP3 aarch64', 'edition': '15 SP3', 'architecture': 'aarch64', 'products': [2137]}, 
		2164: { 'name': 'Web and Scripting Module 15 SP3 aarch64', 'edition': '15 SP3', 'architecture': 'aarch64', 'products': [2137]}, 
		2168: { 'name': 'Legacy Module 15 SP3 aarch64', 'edition': '15 SP3', 'architecture': 'aarch64', 'products': [2137]}, 
		2172: { 'name': 'Public Cloud Module 15 SP3 aarch64', 'edition': '15 SP3', 'architecture': 'aarch64', 'products': [2137]}, 
		2177: { 'name': 'Transactional Server Module 15 SP3 aarch64', 'edition': '15 SP3', 'architecture': 'aarch64', 'products': [2137]}, 
		2181: { 'name': 'Python 2 Module 15 SP3 aarch64', 'edition': '15 SP3', 'architecture': 'aarch64', 'products': [2137]}, 
		2166: { 'name': 'HPC Module 15 SP3 aarch64', 'edition': '15 SP3', 'architecture': 'aarch64', 'products': [2137]}, 
  		2386: { 'name': 'Certifications Module 15 SP3 aarch64', 'edition': '15 SP3', 'architecture': 'aarch64', 'products': [2137]}, 
      	2188: { 'name': 'SUSE Package Hub 15 SP3 aarch64', 'edition': '15 SP3', 'architecture': 'aarch64', 'products': [2137]},
    
		2143: { 'name': 'Basesystem Module 15 SP3 ppc64le', 'edition': '15 SP3', 'architecture': 'ppc64le', 'products': [2138]}, 
		2147: { 'name': 'Desktop Applications Module 15 SP3 ppc64le', 'edition': '15 SP3', 'architecture': 'ppc64le', 'products': [2138]}, 
		2151: { 'name': 'Server Applications Module 15 SP3 ppc64le', 'edition': '15 SP3', 'architecture': 'ppc64le', 'products': [2138]}, 
		2155: { 'name': 'Containers Module 15 SP3 ppc64le', 'edition': '15 SP3', 'architecture': 'ppc64le', 'products': [2138]}, 
		2159: { 'name': 'Development Tools Module 15 SP3 ppc64le', 'edition': '15 SP3', 'architecture': 'ppc64le', 'products': [2138]}, 
		2163: { 'name': 'Web and Scripting Module 15 SP3 ppc64le', 'edition': '15 SP3', 'architecture': 'ppc64le', 'products': [2138]}, 
		2169: { 'name': 'Legacy Module 15 SP3 ppc64le', 'edition': '15 SP3', 'architecture': 'ppc64le', 'products': [2138]}, 
		2173: { 'name': 'Public Cloud Module 15 SP3 ppc64le', 'edition': '15 SP3', 'architecture': 'ppc64le', 'products': [2138]}, 
		2178: { 'name': 'Transactional Server Module 15 SP3 ppc64le', 'edition': '15 SP3', 'architecture': 'ppc64le', 'products': [2138]}, 
		2182: { 'name': 'Python 2 Module 15 SP3 ppc64le', 'edition': '15 SP3', 'architecture': 'ppc64le', 'products': [2138]}, 
  		2387: { 'name': 'Certifications Module 15 SP3 ppc64le', 'edition': '15 SP3', 'architecture': 'ppc64le', 'products': [2138]}, 
      	2189: { 'name': 'SUSE Package Hub 15 SP3 ppc64le', 'edition': '15 SP3', 'architecture': 'ppc64le', 'products': [2138]},

		2145: { 'name': 'Basesystem Module 15 SP3 x86_64', 'edition': '15 SP3', 'architecture': 'x86_64', 'products': [2136, 2140, 2134, 2133, 2285]},
		2389: { 'name': 'Certifications Module 15 SP3 x86_64', 'edition': '15 SP3', 'architecture': 'x86_64', 'products': [2136, 2140, 2134, 2285]},  
		2149: { 'name': 'Desktop Applications Module 15 SP3 x86_64', 'edition': '15 SP3', 'architecture': 'x86_64', 'products': [2136, 2140, 2134, 2285]},
		2153: { 'name': 'Server Applications Module 15 SP3 x86_64', 'edition': '15 SP3', 'architecture': 'x86_64', 'products': [2136, 2140, 2134, 2285]},
		2157: { 'name': 'Containers Module 15 SP3 x86_64', 'edition': '15 SP3', 'architecture': 'x86_64', 'products': [2136, 2140, 2134, 2285]},
		2161: { 'name': 'Development Tools Module 15 SP3 x86_64', 'edition': '15 SP3', 'architecture': 'x86_64', 'products': [2136, 2140, 2134, 2285]},
		2165: { 'name': 'Web and Scripting Module 15 SP3 x86_64', 'edition': '15 SP3', 'architecture': 'x86_64', 'products': [2136, 2140, 2134, 2285]},
		2167: { 'name': 'HPC Module 15 SP3 x86_64', 'edition': '15 SP3', 'architecture': 'x86_64', 'products': [2136, 2140, 2134, 2285]},
		2171: { 'name': 'Legacy Module 15 SP3 x86_64', 'edition': '15 SP3', 'architecture': 'x86_64', 'products': [2136, 2140, 2134, 2285]},
		2175: { 'name': 'Public Cloud Module 15 SP3 x86_64', 'edition': '15 SP3', 'architecture': 'x86_64', 'products': [2136, 2140, 2134, 2285]},
		2180: { 'name': 'Transactional Server Module 15 SP3 x86_64', 'edition': '15 SP3', 'architecture': 'x86_64', 'products': [2136, 2140, 2134, 2285]},
		2184: { 'name': 'Python 2 Module 15 SP3 x86_64', 'edition': '15 SP3', 'architecture': 'x86_64', 'products': [2136, 2140, 2134, 2285]},
  		2198: { 'name': 'SAP Applications Module 15 SP3 x86_64', 'edition': '15 SP3', 'architecture': 'x86_64', 'products': [2136, 2140, 2134, 2285]},
  		2176: { 'name': 'SUSE Cloud Application Platform Tools Module 15 SP3 x86_64', 'edition': '15 SP3', 'architecture': 'x86_64', 'products': [2136, 2140, 2134, 2285]},    
		2286: { 'name': 'SUSE Real Time Module 15 SP3 x86_64', 'edition': '15 SP3', 'architecture': 'x86_64', 'products': [2136, 2140, 2134, 2285]},
		2191: { 'name': 'SUSE Package Hub 15 SP3 x86_64', 'edition': '15 SP3', 'architecture': 'x86_64', 'products': [2136, 2140, 2134, 2285]},

		2297: { 'name': 'Basesystem Module 15 SP4 ppc64le', 'edition': '15 SP4', 'architecture': 'ppc64le', 'products': [2290]}, 
		2301: { 'name': 'Desktop Applications Module 15 SP4 ppc64le', 'edition': '15 SP4', 'architecture': 'ppc64le', 'products': [2290]}, 
		2305: { 'name': 'Server Applications Module 15 SP4 ppc64le', 'edition': '15 SP4', 'architecture': 'ppc64le', 'products': [2290]}, 
		2309: { 'name': 'Containers Module 15 SP4 ppc64le', 'edition': '15 SP4', 'architecture': 'ppc64le', 'products': [2290]}, 
		2313: { 'name': 'Development Tools Module 15 SP4 ppc64le', 'edition': '15 SP4', 'architecture': 'ppc64le', 'products': [2290]}, 
		2317: { 'name': 'Web and Scripting Module 15 SP4 ppc64le', 'edition': '15 SP4', 'architecture': 'ppc64le', 'products': [2290]}, 
		2321: { 'name': 'Legacy Module 15 SP4 ppc64le', 'edition': '15 SP4', 'architecture': 'ppc64le', 'products': [2290]}, 
		2325: { 'name': 'Public Cloud Module 15 SP4 ppc64le', 'edition': '15 SP4', 'architecture': 'ppc64le', 'products': [2290]}, 
		2329: { 'name': 'Transactional Server Module 15 SP4 ppc64le', 'edition': '15 SP4', 'architecture': 'ppc64le', 'products': [2290]}, 
		2403: { 'name': 'Python 3 Module 15 SP4 ppc64le', 'edition': '15 SP4', 'architecture': 'ppc64le', 'products': [2290]}, 
  		2391: { 'name': 'Certifications Module 15 SP4 ppc64le', 'edition': '15 SP4', 'architecture': 'ppc64le', 'products': [2290]}, 
      	2345: { 'name': 'SUSE Package Hub 15 SP4 ppc64le', 'edition': '15 SP4', 'architecture': 'ppc64le', 'products': [2290]},
       
     	2296: { 'name': 'Basesystem Module 15 SP4 aarch64', 'edition': '15 SP4', 'architecture': 'aarch64', 'products': [2289, 2353]}, 
		2300: { 'name': 'Desktop Applications Module 15 SP4 aarch64', 'edition': '15 SP4', 'architecture': 'aarch64', 'products': [2289, 2353]}, 
		2304: { 'name': 'Server Applications Module 15 SP4 aarch64', 'edition': '15 SP4', 'architecture': 'aarch64', 'products': [2289, 2353]}, 
		2308: { 'name': 'Containers Module 15 SP4 aarch64', 'edition': '15 SP4', 'architecture': 'aarch64', 'products': [2289, 2353]}, 
		2312: { 'name': 'Development Tools Module 15 SP4 aarch64', 'edition': '15 SP4', 'architecture': 'aarch64', 'products': [2289, 2353]}, 
		2316: { 'name': 'Web and Scripting Module 15 SP4 aarch64', 'edition': '15 SP4', 'architecture': 'aarch64', 'products': [2289, 2353]}, 
		2320: { 'name': 'Legacy Module 15 SP4 aarch64', 'edition': '15 SP4', 'architecture': 'aarch64', 'products': [2289, 2353]}, 
		2324: { 'name': 'Public Cloud Module 15 SP4 aarch64', 'edition': '15 SP4', 'architecture': 'aarch64', 'products': [2289, 2353]}, 
		2328: { 'name': 'Transactional Server Module 15 SP4 aarch64', 'edition': '15 SP4', 'architecture': 'aarch64', 'products': [2289, 2353]}, 
		2402: { 'name': 'Python 3 Module 15 SP4 aarch64', 'edition': '15 SP4', 'architecture': 'aarch64', 'products': [2289, 2353]}, 
  		2390: { 'name': 'Certifications Module 15 SP4 aarch64', 'edition': '15 SP4', 'architecture': 'aarch64', 'products': [2289, 2353]}, 
      	2355: { 'name': 'HPC Module 15 SP4 aarch64', 'edition': '15 SP4', 'architecture': 'aarch64', 'products': [2289, 2353]}, 
      	2345: { 'name': 'SUSE Package Hub 15 SP4 aarch64', 'edition': '15 SP4', 'architecture': 'aarch64', 'products': [2289, 2353]},  
       
     	2298: { 'name': 'Basesystem Module 15 SP4 s390x', 'edition': '15 SP4', 'architecture': 's390x', 'products': [2291]}, 
		2302: { 'name': 'Desktop Applications Module 15 SP4 s390x', 'edition': '15 SP4', 'architecture': 's390x', 'products': [2291]}, 
		2306: { 'name': 'Server Applications Module 15 SP4 s390x', 'edition': '15 SP4', 'architecture': 's390x', 'products': [2291]}, 
		2310: { 'name': 'Containers Module 15 SP4 s390x', 'edition': '15 SP4', 'architecture': 's390x', 'products': [2291]}, 
		2314: { 'name': 'Development Tools Module 15 SP4 s390x', 'edition': '15 SP4', 'architecture': 's390x', 'products': [2291]}, 
		2318: { 'name': 'Web and Scripting Module 15 SP4 s390x', 'edition': '15 SP4', 'architecture': 's390x', 'products': [2291]}, 
		2322: { 'name': 'Legacy Module 15 SP4 s390x', 'edition': '15 SP4', 'architecture': 's390x', 'products': [2291]}, 
		2326: { 'name': 'Public Cloud Module 15 SP4 s390x', 'edition': '15 SP4', 'architecture': 's390x', 'products': [2291]}, 
		2330: { 'name': 'Transactional Server Module 15 SP4 s390x', 'edition': '15 SP4', 'architecture': 's390x', 'products': [2291]}, 
		2404: { 'name': 'Python 3 Module 15 SP4 s390x', 'edition': '15 SP4', 'architecture': 's390x', 'products': [2291]}, 
  		2392: { 'name': 'Certifications Module 15 SP4 s390x', 'edition': '15 SP4', 'architecture': 's390x', 'products': [2291]}, 
      	2355: { 'name': 'HPC Module 15 SP4 s390x', 'edition': '15 SP4', 'architecture': 's390x', 'products': [2291]}, 
      	2346: { 'name': 'SUSE Package Hub 15 SP4 s390x', 'edition': '15 SP4', 'architecture': 's390x', 'products': [2291]},         

     	2299: { 'name': 'Basesystem Module 15 SP4 x86_64', 'edition': '15 SP4', 'architecture': 'x86_64', 'products': [2295, 2354, 2292, 2294]}, 
    	2393: { 'name': 'Certifications Module 15 SP4 x86_64', 'edition': '15 SP4', 'architecture': 'x86_64', 'products': [2295, 2354, 2292, 2294]}, 
		2303: { 'name': 'Desktop Applications Module 15 SP4 x86_64', 'edition': '15 SP4', 'architecture': 'x86_64', 'products': [2295, 2354, 2292, 2294]}, 
		2307: { 'name': 'Server Applications Module 15 SP4 x86_64', 'edition': '15 SP4', 'architecture': 'x86_64', 'products': [2295, 2354, 2292, 2294]}, 
		2311: { 'name': 'Containers Module 15 SP4 x86_64', 'edition': '15 SP4', 'architecture': 'x86_64', 'products': [2295, 2354, 2292, 2294]}, 
		2315: { 'name': 'Development Tools Module 15 SP4 x86_64', 'edition': '15 SP4', 'architecture': 'x86_64', 'products': [2295, 2354, 2292, 2294]}, 
		2319: { 'name': 'Web and Scripting Module 15 SP4 x86_64', 'edition': '15 SP4', 'architecture': 'x86_64', 'products': [2295, 2354, 2292, 2294]}, 
		2323: { 'name': 'Legacy Module 15 SP4 x86_64', 'edition': '15 SP4', 'architecture': 'x86_64', 'products': [2295, 2354, 2292, 2294]}, 
		2327: { 'name': 'Public Cloud Module 15 SP4 x86_64', 'edition': '15 SP4', 'architecture': 'x86_64', 'products': [2295, 2354, 2292, 2294]}, 
		2331: { 'name': 'Transactional Server Module 15 SP4 x86_64', 'edition': '15 SP4', 'architecture': 'x86_64', 'products': [2295, 2354, 2292, 2294]}, 
		2405: { 'name': 'Python 3 Module 15 SP4 x86_64', 'edition': '15 SP4', 'architecture': 'x86_64', 'products': [2295, 2354, 2292, 2294]}, 
		2342: { 'name': 'SAP Applications Module 15 SP4 x86_64', 'edition': '15 SP4', 'architecture': 'x86_64', 'products': [2295, 2354, 2292, 2294]}, 
  		2392: { 'name': 'Certifications Module 15 SP4 x86_64', 'edition': '15 SP4', 'architecture': 'x86_64', 'products': [2295, 2354, 2292, 2294]}, 
      	2356: { 'name': 'HPC Module 15 SP4 x86_64', 'edition': '15 SP4', 'architecture': 'x86_64', 'products': [2295, 2354, 2292, 2294]}, 
      	2346: { 'name': 'SUSE Package Hub 15 SP4 x86_64', 'edition': '15 SP4', 'architecture': 'x86_64', 'products': [2295, 2354, 2292, 2294]},         

		2471: { 'name': 'Basesystem Module 15 SP5 aarch64', 'edition': '15 SP5', 'architecture': 'aarch64', 'products': [2462, 2469]},
		2483: { 'name': 'Containers Module 15 SP5 aarch64', 'edition': '15 SP5', 'architecture': 'aarch64', 'products': [2462, 2469]},
		2475: { 'name': 'Desktop Applications Module 15 SP5 aarch64', 'edition': '15 SP5', 'architecture': 'aarch64', 'products': [2462, 2469]},
		2487: { 'name': 'Development Tools Module 15 SP5 aarch64', 'edition': '15 SP5', 'architecture': 'aarch64', 'products': [2462, 2469]},
		2497: { 'name': 'Legacy Module 15 SP5 aarch64', 'edition': '15 SP5', 'architecture': 'aarch64', 'products': [2462, 2469]},
		2495: { 'name': 'HPC Module 15 SP5 aarch64', 'edition': '15 SP5', 'architecture': 'aarch64', 'products': [2462, 2469]},
		2501: { 'name': 'Public Cloud Module 15 SP5 aarch64', 'edition': '15 SP5', 'architecture': 'aarch64', 'products': [2462, 2469]},
		2533: { 'name': 'Python 3 Module 15 SP5 aarch64', 'edition': '15 SP5', 'architecture': 'aarch64', 'products': [2462, 2469]},
		2479: { 'name': 'Server Applications Module 15 SP5 aarch64', 'edition': '15 SP5', 'architecture': 'aarch64', 'products': [2462, 2469]},
		2505: { 'name': 'Transactional Server Module 15 SP5 aarch64', 'edition': '15 SP5', 'architecture': 'aarch64', 'products': [2462, 2469]},
		2491: { 'name': 'Web and Scripting Module 15 SP5 aarch64', 'edition': '15 SP5', 'architecture': 'aarch64', 'products': [2462, 2469]},

		2472: { 'name': 'Basesystem Module 15 SP5 ppc64le', 'edition': '15 SP5', 'architecture': 'ppc64le', 'products': [2463]},
		2484: { 'name': 'Containers Module 15 SP5 ppc64le', 'edition': '15 SP5', 'architecture': 'ppc64le', 'products': [2463]},
		2476: { 'name': 'Desktop Applications Module 15 SP5 ppc64le', 'edition': '15 SP5', 'architecture': 'ppc64le', 'products': [2463]},
		2488: { 'name': 'Development Tools Module 15 SP5 ppc64le', 'edition': '15 SP5', 'architecture': 'ppc64le', 'products': [2463]},
		2498: { 'name': 'Legacy Module 15 SP5 ppc64le', 'edition': '15 SP5', 'architecture': 'ppc64le', 'products': [2463]},
		2502: { 'name': 'Public Cloud Module 15 SP5 ppc64le', 'edition': '15 SP5', 'architecture': 'ppc64le', 'products': [2463]},
		2534: { 'name': 'Python 3 Module 15 SP5 ppc64le', 'edition': '15 SP5', 'architecture': 'ppc64le', 'products': [2463]},
		2480: { 'name': 'Server Applications Module 15 SP5 ppc64le', 'edition': '15 SP5', 'architecture': 'ppc64le', 'products': [2463]},
		2506: { 'name': 'Transactional Server Module 15 SP5 ppc64le', 'edition': '15 SP5', 'architecture': 'ppc64le', 'products': [2463]},
		2492: { 'name': 'Web and Scripting Module 15 SP5 ppc64le', 'edition': '15 SP5', 'architecture': 'ppc64le', 'products': [2463]},

		2473: { 'name': 'Basesystem Module 15 SP5 s390x', 'edition': '15 SP5', 'architecture': 's390x', 'products': [2464]},
		2485: { 'name': 'Containers Module 15 SP5 s390x', 'edition': '15 SP5', 'architecture': 's390x', 'products': [2464]},
		2477: { 'name': 'Desktop Applications Module 15 SP5 s390x', 'edition': '15 SP5', 'architecture': 's390x', 'products': [2464]},
		2489: { 'name': 'Development Tools Module 15 SP5 s390x', 'edition': '15 SP5', 'architecture': 's390x', 'products': [2464]},
		2499: { 'name': 'Legacy Module 15 SP5 s390x', 'edition': '15 SP5', 'architecture': 's390x', 'products': [2464]},
		2503: { 'name': 'Public Cloud Module 15 SP5 s390x', 'edition': '15 SP5', 'architecture': 's390x', 'products': [2464]},
		2535: { 'name': 'Python 3 Module 15 SP5 s390x', 'edition': '15 SP5', 'architecture': 's390x', 'products': [2464]},
		2481: { 'name': 'Server Applications Module 15 SP5 s390x', 'edition': '15 SP5', 'architecture': 's390x', 'products': [2464]},
		2507: { 'name': 'Transactional Server Module 15 SP5 s390x', 'edition': '15 SP5', 'architecture': 's390x', 'products': [2464]},
		2493: { 'name': 'Web and Scripting Module 15 SP5 s390x', 'edition': '15 SP5', 'architecture': 's390x', 'products': [2464]},

		2474: { 'name': 'Basesystem Module 15 SP5 x86_64', 'edition': '15 SP5', 'architecture': 'x86_64', 'products': [2468,2470,2465,2467]},
		2486: { 'name': 'Containers Module 15 SP5 x86_64', 'edition': '15 SP5', 'architecture': 'x86_64', 'products': [2468,2470,2465,2467]},
		2478: { 'name': 'Desktop Applications Module 15 SP5 x86_64', 'edition': '15 SP5', 'architecture': 'x86_64', 'products': [2468,2470,2465,2467]},
		2490: { 'name': 'Development Tools Module 15 SP5 x86_64', 'edition': '15 SP5', 'architecture': 'x86_64', 'products': [2468,2470,2465,2467]},
		2496: { 'name': 'HPC Module 15 SP5 x86_64', 'edition': '15 SP5', 'architecture': 'x86_64', 'products': [2468,2470,2465,2467]},
		2500: { 'name': 'Legacy Module 15 SP5 x86_64', 'edition': '15 SP5', 'architecture': 'x86_64', 'products': [2468,2470,2465,2467]},
		2504: { 'name': 'Public Cloud Module 15 SP5 x86_64', 'edition': '15 SP5', 'architecture': 'x86_64', 'products': [2468,2470,2465,2467]},
		2536: { 'name': 'Python 3 Module 15 SP5 x86_64', 'edition': '15 SP5', 'architecture': 'x86_64', 'products': [2468,2470,2465,2467]},
		2519: { 'name': 'SAP Applications Module 15 SP5 x86_64', 'edition': '15 SP5', 'architecture': 'x86_64', 'products': [2468,2470,2465,2467]},
		2482: { 'name': 'Server Applications Module 15 SP5 x86_64', 'edition': '15 SP5', 'architecture': 'x86_64', 'products': [2468,2470,2465,2467]},
		2508: { 'name': 'Transactional Server Module 15 SP5 x86_64', 'edition': '15 SP5', 'architecture': 'x86_64', 'products': [2468,2470,2465,2467]},
		2494: { 'name': 'Web and Scripting Module 15 SP5 x86_64', 'edition': '15 SP5', 'architecture': 'x86_64', 'products': [2468,2470,2465,2467]},

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
	suseorphans = []
	suseptf = []
 
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
	max_threads = 25

	# time to wait before starting each chunk of threads
	wait_time = 10

	# override architecture
	arch = None

	# short responses (just package versions)
	short_response = False

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
		print('Usage: ' + sys.argv[0] + ' [-l|--list-products] -p|--product product id -n|--name <package name> [-s|--short] [-v|--verbose] [-1|--show-unknown] [-2|--show-differences] [-3|--show-uptodate] [-4|--show-unsupported] [-5|--show-suseorphans] [-6|--show-suseptf] [-o|--outputdir] [-d|--supportconfig] [-f|--force-refresh]')
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
		print('-5|--show-suseorphans)\t\tshows packages that are from SUSE, but are now orphans (e.g. from different OS/product versions).\n')
		print('-6|--show-suseptf)\t\tshows SUSE-made PTF (Program Temporary Fix) packages.\n')
		print('-o|--outputdir)\t\tspecify an output directory for the reports. Default: current directory.\n')
		print('-d|--supportconfig\t\tAnalyzes a supportconfig directory and generates CSV reports for up-to-date, not found and different packages.\n')
		print('-a|--arch\t\tSupply an architecture for the supportconfig analysis.')
		print('-f|--force-refresh\t\tIgnore cached data and retrieve latest data from SCC')
		print('\n')
		return

	def test(self):
		self.threads = []
		package_name = 'glibc'
		instance_nr = 0

		for k, v in self.product_list.items():
			print('searching for package \"glibc\" in product id \"' + str(k) + '\" (' + v['name'] + ')')
			self.threads.insert(instance_nr, PackageSearchEngine(instance_nr, k, package_name, v['name'], '0', self.force_refresh))
			self.threads[instance_nr].start()
			instance_nr = instance_nr + 1

		# fetch results for all threads
		while len(self.threads) > 0:
			for thread_number, t in enumerate(self.threads):
				#if t.is_alive():
					t.join(timeout=5)
					if t.is_alive():
						print(f'thread {t.name} is not ready yet, skipping')
						self.threads.append(t)
						continue
					refined_data = t.get_results()

				# for thread_number in range(instance_nr):
				# 	threads[thread_number].join()
				# 	refined_data = threads[thread_number].get_results()
					try:
						print('[thread ' +  str(thread_number) + ' ] latest version for ' + refined_data['query'] + ' on product ID ' + str(refined_data['product_id']) +  ' is ' + refined_data['results'][0]['version'] + '-' + refined_data['results'][0]['release'])
						if self.verbose:
							for item in refined_data['results']:
									print('[thread ' +  str(thread_number) + ' ] version ' + item['version'] + '-' + item['release'] + ' is available on repository [' + item['repository'] + ']')
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

		print('searching for package \"' + package_name + '\" in product id \"' + str(product_id) + '\" (' + plist[product_id]['name'] + ')')
		self.threads.insert(0, PackageSearchEngine(0, product_id, package_name, plist[product_id]['name'], '0', self.force_refresh))
		self.threads[0].start()

		# fetch results for the only thread
		self.threads[0].join()
		refined_data = self.threads[0].get_results()
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
		self.threads=[]
		# fetch results for all threads
		for chunk in self.list_chunk(rpmlist, self.max_threads):
			for p in chunk:
				self.threads.insert(count, PackageSearchEngine(count, selected_product_id, p[0], p[1], p[2], self.force_refresh))
				self.threads[count].start()
				count+=1
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
					print(f'joining thread {t.name} (waiting: {to_process})...')
				t.join(timeout=5)
				# time.sleep(.001)
				if t.is_alive():
					print(f'thread {t.name} is not ready yet, skipping')
					self.threads.append(t)
					continue
				# else:
				#	print(f'thread {t.name} is dead')
     
				refined_data = t.get_results()
				#print('refined data = ' + str(refined_data))
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
					
					t.processed = True
					to_process = len([t for t in self.threads if t.processed == False])
					time.sleep(.001)
				except IndexError:
					#print('[thread ' + str(thread_number) + '] could not find any version for package ' + refined_data['query'])
					pass
				except KeyError as e:
					print(f'Cannot find field: {e}')
					pass
				print(f'thread {t.name} is done')
				time.sleep(.1)
				sys.stdout.flush()
			time.sleep(.1)

		# check if there are SUSE orphan packages in notfound
		self.notfound.sort()
		for package, distribution, version in self.notfound.copy():
			if 'SUSE Linux Enterprise' in distribution:
				if self.verbose:
					print(f'**** moving SUSE orphan package to appropriate list: {package}-{version} ({distribution})')
				self.notfound.remove([package, distribution, version])
				self.suseorphans.append([package, distribution, version])

		# check if there are SUSE PTF packages in unsupported
		self.unsupported.sort()
		for package, distribution, version in self.unsupported.copy():
			if 'SUSE Linux Enterprise PTF' in distribution:
				if self.verbose:
					print(f'**** moving SUSE PTF package to appropriate list: {package}-{version} ({distribution})')
				self.unsupported.remove([package, distribution, version])
				self.suseptf.append([package, distribution, version])


		sys.stdout.write('\nDone.\n')
		sys.stdout.flush()
		
		return (self.uptodate, self.unsupported, self.notfound, self.different, self.suseorphans, self.suseptf)

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
				with open(os.path.join(self.outputdir,'vercheck-unsupported-' + self.sc_name + '.csv'), 'w') as f:
					for p, d, c in self.unsupported:
						f.write(p + ',' + d + ',' + c + '\n')
					f.close()
			except Exception as e:
				print('Error writing file: ' + str(e))
				return

			try:
				with open(os.path.join(self.outputdir,'vercheck-different-' + self.sc_name + '.csv'), 'w') as f:
					for p, c, l, r  in self.different:
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

		if self.show_suseorphans:
			print('\n\t\t--- SUSE orphan packages ---\n')
			print(str.ljust('Name', field_size) + '\t' + str.ljust('Vendor', field_size) + '\t' + str.ljust('Current Version', field_size))
			print('=' * 80)
			for p, c, l  in self.suseorphans:
					print(str.ljust(p, field_size) + '\t' + str.ljust(c, field_size) + '\t' + str.ljust(l, field_size))
			print('\nTotal: ' + str(len(self.suseorphans)) + ' packages')

		if self.show_suseptf:
			print('\n\t\t--- SUSE PTF packages ---\n')
			print(str.ljust('Name', field_size) + '\t' + str.ljust('Vendor', field_size) + '\t' + str.ljust('Current Version', field_size))
			print('=' * 80)
			for p, c, l  in self.suseptf:
					print(str.ljust(p, field_size) + '\t' + str.ljust(c, field_size) + '\t' + str.ljust(l, field_size))
			print('\nTotal: ' + str(len(self.suseptf)) + ' packages')

		return


### separate class instantiated by each thread, does a search and posts results
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
	retry_states = [ 429, 502, 504 ]

	# server replies which are permanent errors (and cannot be retried)
	error_states = [ 400, 403, 404, 422, 500 ]

	results = {}
 
	def __init__(self, instance_nr, product_id, package_name, supplied_distro, supplied_version, force_refresh):
		super(PackageSearchEngine, self).__init__(name='search-' + package_name) 
		urllib3.disable_warnings()
		self.instance_nr = instance_nr
		self.product_id = product_id
		self.package_name = package_name
		self.supplied_distro = supplied_distro
		self.supplied_version = supplied_version
		self.force_refresh = force_refresh
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
		#print('release %s will be considered as %s' % (e['release'], release))
		return LooseVersion(v + '-' + r)

	def get_results(self):
		return { 'product_id': self.product_id, 'query': self.package_name, 'supplied_distro': self.supplied_distro, 'supplied_version': self.supplied_version, 'results': self.results }

	def run(self):
		#print('[Thread ' + str(self.instance_nr) + '] looking for ' + self.package_name + ' on product id ' + str(self.product_id))
		tries = 0
		valid_response = False
		refined_data = []
		return_data = []
		cached = False
  
		# load the local cache if it exists and checks for valid data
		cached_data = self.cm.get_cache_data()
		modules_data = SCCVersion.sle_modules_by_product_list
		product_list = SCCVersion.product_list
		if (self.cm.initialized) and self.force_refresh is False:
			try:
				item, product = self.cm.get_record(self.product_id, self.package_name)
				if item is None:
					cached = False
				else:
					if ( (item['name'] == self.package_name) and (product is not None)):
							age=datetime.strptime(item['timestamp'], "%Y-%m-%dT%H:%M:%S.%f") - datetime.now()
							cached = True
							if age.days > self.cm.get_max_age():
								
								item['repository'] = product['name'] + ' ' + product['edition'] + ' ' +  product['architecture']
								item['product_id'] = self.product_id           
								refined_data.append(item)
							else:
								print(f'cached data for {self.package_name} is too old ({age.days} days), discarding cache entry')
								self.cm.remove_record(item)
								cached = False
			except KeyError as e:
					print(f'invalid cache entry for {self.package_name}, removing (reason: {e})')
					self.cm.remove_record(item)
	
		if (cached):
			self.sort_and_deliver(refined_data)
			print(f'found {self.package_name} for product ID {self.product_id} (cached)')
			return
		else:
			print(f'searching for {self.package_name} for product ID {self.product_id} in SCC')
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
					print('thread %d got non-fatal reply (%d) from server, trying again in 5 seconds ' % (self.instance_nr, r.status))
					time.sleep(5)
					tries = tries + 1
					continue
				else:
					print('got unknown error %d from the server!' % r.status)

			if return_data:
				for item in return_data['data']:
					# discard items that do not match exactly our query
					if item['name'] != self.package_name:
						#print(f'discarding item: {item}')
						continue
					else:
						# valid data, add it to the cache and to the results
						#print('added result: ' + item['name'] + ' ' + item['version'] + '-' + item['release'])
						item['repository'] = item['products'][0]['name'] + ' ' + item['products'][0]['edition'] + ' ' +  item['products'][0]['architecture']
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
			#print('*** warning: sorting error due to strange version (may be ignored): ' + str(e))
			pass

		#print('refined data size: ' + str(len(refined_data)))
		self.results = refined_data
		self.done = True
		del self.cm
		return


#### main program
def main():
	sv = SCCVersion()
	signal.signal(signal.SIGINT, sv.cleanup)

	try:
		opts,args = getopt.getopt(sys.argv[1:],  "hp:n:lsvt123456a:d:o:f", [ "help", "product=", "name=", "list-products", "short", "verbose", "test", "show-unknown", "show-differences", "show-uptodate", "show-unsupported", "show-suseorphans", "show-suseptf", "arch=", "supportconfig=", "outputdir=", "force-refresh" ])
	except getopt.GetoptError as err:
		print(err)
		sv.usage()
		exit(2)

	product_id = -1
	package_name = ''
	short_response = False
	global show_unknown, show_diff, show_uptodate, show_unsupported, show_suseorphans, show_suseptf
	global uptodate, different, notfound, unsupported, suseorphans, suseptf

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
		elif o in ("-o", "--outputdir"):
			sv.outputdir = a
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
		elif o in ("-5", "--show-suseorphans"):
			sv.show_suseorphans = True
		elif o in ("-6", "--show-suseptf"):
			sv.show_suseptf = True
		elif o in ("-v", "--verbose"):
			sv.set_verbose(True)
		elif o in ("-f", "--force-refresh"):
			sv.set_force_refresh(True)
		elif o in ("-t", "--test"):
			sv.test()
			exit(0)
		elif o in ("-d", "--supportconfig"):
			supportconfigdir = a
			uptodate, unsupported, notfound, different, suseorphans, suseptf = sv.check_supportconfig(supportconfigdir)
			sv.write_reports()

			exit(0)
		else:
			assert False, "invalid option"

	if product_id == -1 or package_name == '':
		print('Please specify a product ID and package name.')
		sv.usage()
		exit(2)

	if product_id in sv.suma_product_list:
		plist = sv.suma_product_list
	else:
		plist = sv.product_list
  
	if product_id not in plist:
		print ('Product ID ' + str(product_id) + ' is unknown.')
		exit(2)
	else:
		if sv.verbose:
			print ('Using product ID ' + str(product_id) +  ' ('  + plist[product_id]['name'] + ')')
	
	sv.search_package(product_id, package_name)

	return

# package cache
class Singleton(type): 
    # Inherit from "type" in order to gain access to method __call__
    def __init__(self, *args, **kwargs):
        self.__instance = None # Create a variable to store the object reference
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        if self.__instance is None:
            # if the object has not already been created
            self.__instance = super().__call__(*args, **kwargs) # Call the __init__ method of the subclass and save the reference
            return self.__instance
        else:
            # if object reference already exists; return it
            return self.__instance
        
class CacheManager(metaclass=Singleton):
	cache_data = []	
	max_age_days = -5 # entries from the cache over 5 days old are discarded
	user_cache_dir = os.path.join(os.getenv('HOME'), '.cache/scc-tools')
	default_cache_dir = '/var/cache/scc-tools'
	cache_file = 'scc_data.json'
	active_cache_file = ''
	_lock = Lock()
	initialized = False
     
	def __init__(self):
		if (os.access(self.default_cache_dir, os.W_OK)):
			self.active_cache_file = os.path.join(self.default_cache_dir, self.cache_file)
		else:
			self.active_cache_file = os.path.join(self.user_cache_dir, self.cache_file)
			if (os.path.exists(self.user_cache_dir) is False):
				os.makedirs(self.user_cache_dir)
	
		self.load_cache()
		# print(f'my cache has {len(self.cache_data)} entries')
		weakref.finalize(self, self.write_cache)
  
	@contextmanager
	def acquire_timeout(self, timeout):
		result = self._lock.acquire(timeout=timeout)
		time.sleep(0.001)
		# print(f'lock result = {result}')
		if result:
			self._lock.release()
		yield result
		# print(f'lock status: {lock.locked()}')

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
						print(f'loaded {len(self.cache_data)} items from cache ({self.active_cache_file})')
		except IOError:
			#print(f'Error reading the package cache from {self.active_cache_file} (non-fatal)')
			return False
		except json.decoder.JSONDecodeError:
			print(f'Invalid cache data (non-fatal)')
			#print(f'Data read: [{self.cache_data}]')
			return False
		return True

    # saves the package data for later use
	def write_cache(self):
		try:
			with self.acquire_timeout(2) as acquired:
				if acquired:
					print(f'writing {len(self.cache_data)} items to cache at {self.active_cache_file}')
					with open(self.active_cache_file, "w+") as f:
						f.write(json.dumps(self.cache_data, default=self.dt_parser))
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
		product_list = SCCVersion.product_list
		modules_data = SCCVersion.sle_modules_by_product_list
		for item in self.cache_data:
			if package_name == item['name']:
				for p in item['products']:
					if product_id == p['id']:
						#print(f'item found in cache: {item}')
						item['repository'] = p['name'] + ' ' + p['edition'] + ' ' +  p['architecture']
						return item, p
  
				# check compatible module list
				for m in modules_data:
					if product_id in modules_data[m]['products']:
						#print(f"module {m} ({modules_data[m]['name']}) claims to be compatible with product id {product_id} ({product_list[product_id]['name']})")
						item['repository'] = modules_data[m]['name'] + ' ' + modules_data[m]['edition'] + ' ' + modules_data[m]['architecture']
						#print(f'item found in cache: {item}')
						return item, modules_data[m]
		return None, None
 
	# removes a record from the cache
	def remove_record(self, record):
		with self.acquire_timeout(5) as acquired:
			if acquired:
				for item in self.cache_data.copy():
					if record['id'] ==  item['id']:
						print(f'removing record from cache: {record}')
						self.cache_data.remove(item)
			else:
				print('remove_record: could not acquire lock!')
				exit(1)
		# print(f'items in cache: {len(self.cache_data)}')
  
	# adds a new record to the cache
	def add_record(self, record):
		# print(f'appending record to cache: {record}')
		with self.acquire_timeout(5) as acquired:
			if acquired:
				found=False
				for item in self.cache_data:
					if record['id'] == item['id'] and record['name'] == item['name']:
						found = True
						break
				if (found is False):
					print(f"cache: added record for {record['id']}")
					self.cache_data.append(record)
				#else:
				#	print('cache: rejecting duplicate item')
			else:
				print('add_record: could not acquire lock!')
				exit(1)
		# print(f'items in cache: {len(self.cache_data)}')
    
	def get_max_age(self):
		return self.max_age_days

	def dt_parser(dt):
		if isinstance(dt, datetime):
			return dt.isoformat()

	def get_cache_data(self):
		return self.cache_data


if __name__ == "__main__":
	main()
