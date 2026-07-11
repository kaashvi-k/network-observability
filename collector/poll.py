import subprocess
import time
import psycopg2

# SNMP target
HOST = "localhost"
PORT = "1162"
COMMUNITY = "public"
DEVICE_NAME = "snmp-target"

# Postgres connection (matches docker-compose.yml environment values)
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "telemetry",
    "password": "telemetry_pass",
    "dbname": "telemetry",
}

OIDS = {
    "sysUptime":   "1.3.6.1.2.1.1.3.0",
    "ifInOctets":  "1.3.6.1.2.1.2.2.1.10.2",
    "ifOutOctets": "1.3.6.1.2.1.2.2.1.16.2",
    "ifInErrors":  "1.3.6.1.2.1.2.2.1.14.2",
    "ifOutErrors": "1.3.6.1.2.1.2.2.1.20.2",
}

def snmp_get(oid, numeric=False):
    output_fmt = "qvt" if numeric else "qv"
    cmd = ["snmpget", "-v2c", "-c", COMMUNITY, "-O", output_fmt, f"{HOST}:{PORT}", oid]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
    except subprocess.TimeoutExpired:
        print(f"WARNING: snmpget timed out for {oid}")
        return None

    if result.returncode != 0:
        print(f"WARNING: snmpget failed for {oid}: {result.stderr.strip()}")
        return None
    value = result.stdout.strip()
    try:
        return int(value)
    except ValueError:
        print(f"WARNING: could not parse value '{value}' for {oid}")
        return None

def poll_once():
    return {
        "sysUptime": snmp_get(OIDS["sysUptime"], numeric=True),
        "ifInOctets": snmp_get(OIDS["ifInOctets"]),
        "ifOutOctets": snmp_get(OIDS["ifOutOctets"]),
        "ifInErrors": snmp_get(OIDS["ifInErrors"]),
        "ifOutErrors": snmp_get(OIDS["ifOutErrors"]),
    }

def insert_reading(conn, data):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO telemetry
                (device_name, sys_uptime_ticks, in_octets, out_octets, in_errors, out_errors)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                DEVICE_NAME,
                data["sysUptime"],
                data["ifInOctets"],
                data["ifOutOctets"],
                data["ifInErrors"],
                data["ifOutErrors"],
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

