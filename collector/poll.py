import subprocess
import time

HOST = "localhost"
PORT = "1161"
COMMUNITY = "public"

OIDS = {
    "sysUptime":    "1.3.6.1.2.1.1.3.0",
    "ifInOctets":   "1.3.6.1.2.1.2.2.1.10.2",
    "ifOutOctets":  "1.3.6.1.2.1.2.2.1.16.2",
    "ifInErrors":   "1.3.6.1.2.1.2.2.1.14.2",
    "ifOutErrors":  "1.3.6.1.2.1.2.2.1.20.2",
}

def snmp_get(oid):
    """Run snmpget as a subprocess and parse its text output."""
    cmd = [
        "snmpget", "-v2c", "-c", COMMUNITY, "-O", "qv",
        f"{HOST}:{PORT}", oid
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)

    if result.returncode != 0:
        return f"ERROR: {result.stderr.strip()}"
    return result.stdout.strip()

def poll_once():
    results = {}
    for name, oid in OIDS.items():
        results[name] = snmp_get(oid)
    return results

if __name__ == "__main__":
    print(f"Starting SNMP poller — target {HOST}:{PORT}, every 30s. Ctrl+C to stop.\n")
    while True:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        data = poll_once()
        print(f"[{timestamp}] {data}")
        time.sleep(30)       
