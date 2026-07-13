import subprocess
import time
import psycopg2

HOST = "localhost"
PORT = "1162"
COMMUNITY = "public"
DEVICE_NAME = "router1"

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "telemetry",
    "password": "telemetry_pass",
    "dbname": "telemetry",
}

OIDS = {
    "sysUptime":    "1.3.6.1.2.1.1.3.0",
    "ifInOctets":   "1.3.6.1.2.1.2.2.1.10.2",
    "ifOutOctets":  "1.3.6.1.2.1.2.2.1.16.2",
    "ifInErrors":   "1.3.6.1.2.1.2.2.1.14.2",
    "ifOutErrors":  "1.3.6.1.2.1.2.2.1.20.2",
    "memTotal":     "1.3.6.1.2.1.25.2.3.1.5.1",
    "memUsed":      "1.3.6.1.2.1.25.2.3.1.6.1",
}


def snmp_get(oid, numeric=False):
    output_fmt = "qvt" if numeric else "qv"
    cmd = ["snmpget", "-v2c", "-c", COMMUNITY, "-O", output_fmt, f"{HOST}:{PORT}", oid]
    start = time.monotonic()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
    except subprocess.TimeoutExpired:
        elapsed = time.monotonic() - start
        print(f"WARNING: snmpget timed out for {oid}")
        return None, elapsed, False

    elapsed = time.monotonic() - start
    if result.returncode != 0:
        print(f"WARNING: snmpget failed for {oid}: {result.stderr.strip()}")
        return None, elapsed, False
    value = result.stdout.strip()
    try:
        return int(value), elapsed, True
    except ValueError:
        print(f"WARNING: could not parse value '{value}' for {oid}")
        return None, elapsed, False


def poll_once():
    results = {}
    latencies = []
    any_failure = False

    for name, oid in OIDS.items():
        value, elapsed, success = snmp_get(oid, numeric=(name == "sysUptime"))
        results[name] = value
        latencies.append(elapsed)
        if not success:
            any_failure = True

    results["avg_latency_ms"] = round(sum(latencies) / len(latencies) * 1000, 2)
    results["poll_failed"] = any_failure
    return results


def insert_reading(conn, data):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO telemetry
                (device_name, sys_uptime_ticks, in_octets, out_octets, in_errors, out_errors,
                 avg_latency_ms, poll_failed, mem_total_kb, mem_used_kb)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                DEVICE_NAME,
                data["sysUptime"],
                data["ifInOctets"],
                data["ifOutOctets"],
                data["ifInErrors"],
                data["ifOutErrors"],
                data["avg_latency_ms"],
                data["poll_failed"],
                data["memTotal"],
                data["memUsed"],
            ),
        )
    conn.commit()


if __name__ == "__main__":
    print("Connecting to Postgres...")
    conn = psycopg2.connect(**DB_CONFIG)
    print(f"Connected. Polling {HOST}:{PORT} every 30s. Ctrl+C to stop.\n")

    try:
        while True:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            data = poll_once()
            insert_reading(conn, data)
            print(f"[{timestamp}] inserted: {data}")
            time.sleep(30)
    except KeyboardInterrupt:
        print("\nStopping poller.")
    finally:
        conn.close()
