# Network Observability Platform

An AI-powered network monitoring and analytics platform that collects, processes, and analyzes real-time telemetry from network devices — including a genuine FRRouting router running real OSPF — with ML-based anomaly detection and automated alerting.

## Architecture
SNMP Devices (snmp-target, router1/FRRouting)
│
├── Custom Python Collector ──► PostgreSQL ──► Grafana
│
└── Prometheus SNMP Exporter ──► Prometheus ──► Grafana
PostgreSQL ──► Isolation Forest (anomaly detection) ──► Alerts (Postgres + syslog-style log + email)

## What this project does

- **Collects real SNMP telemetry** — interface utilization, packet loss, CPU usage, memory consumption, and error statistics — from two devices, one of which is a real FRRouting router running actual OSPF routing.
- **Two parallel collection pipelines**: a custom Python collector (direct SNMP polling → Postgres) and an industry-standard Prometheus + SNMP Exporter pipeline, both feeding Grafana dashboards.
- **ML-based anomaly detection** using Isolation Forest, validated two ways: against synthetic fault injection (direct database rows simulating traffic spikes/errors) and against **real network faults** induced with Linux `tc netem` (genuine packet loss and latency on the router's interface, causing measured SNMP response time increases from ~0.2s to ~3.2s under load).
- **Automated alerting** — severity-classified (INFO/WARNING/CRITICAL) alerts written to Postgres and a syslog-style log file, with real email notifications triggered for CRITICAL/WARNING events.
- **Interactive Grafana dashboards** showing live traffic, errors, memory/CPU usage, and a color-coded alerts table.

## Tech stack

- **Networking**: SNMP (Net-SNMP), FRRouting (real OSPF routing), Linux `tc netem` for fault injection
- **Collection**: Python (`subprocess` + `snmpget`/`snmpwalk`), Prometheus SNMP Exporter
- **Storage**: PostgreSQL, Prometheus TSDB
- **ML**: scikit-learn (Isolation Forest)
- **Visualization**: Grafana
- **Alerting**: Python `logging`, SMTP (Gmail)
- **Infrastructure**: Docker Compose (6 services: snmp-target, router1, postgres, grafana, prometheus, snmp-exporter)

## Running it

```bash
cd docker
docker compose up -d
```

Then:
```bash
cd collector
python3 poll.py
```

Grafana: `http://localhost:3000`
Prometheus: `http://localhost:9090`

## Notable engineering decisions & findings

- Diagnosed and worked around a port-161 privileged-bind conflict specific to the FRRouting/Alpine container by remapping to an unprivileged port.
- Found that Alpine's default `snmpd.conf` was silently conflicting with a custom config, requiring explicit `-C` flag / config file removal.
- Confirmed empirically that virtual (`veth`) network interfaces do not register `tc netem corrupt` faults in `ifInErrors`/`ifOutErrors` counters, since these reflect physical-layer fault detection unavailable on virtual interfaces — packet loss and latency are the genuinely observable fault types in this environment, and the anomaly detection pipeline is built around those signals instead.
- CPU/memory metrics are collected via the Host Resources MIB (`hrProcessorLoad`, `hrStorageTable`), averaged across virtual cores for CPU.

## Known limitations

- CPU/memory metrics are container-level, not tied to a specific physical NIC/hardware fault model.
- Alerting currently supports email; Syslog-style logging and Postgres storage are implemented, SMS (Twilio) was scoped but not built.
