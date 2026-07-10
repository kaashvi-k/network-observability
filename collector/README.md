# Collector

Polls SNMP metrics from the snmp-target container every 30 seconds.

Uses `subprocess` + the system `snmpget` binary rather than the `pysnmp`
library — pysnmp 7.x is a full async rewrite with a different API than
most SNMP tutorials assume, and older pysnmp versions are incompatible
with modern Python. Shelling out to `snmpget` directly is more stable
and transparent for this project's scope.
