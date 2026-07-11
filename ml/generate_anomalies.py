import psycopg2
import random
import time

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "telemetry",
    "password": "telemetry_pass",
    "dbname": "telemetry",
}

DEVICE_NAME = "snmp-target"

def insert_synthetic(conn, in_octets, out_octets, in_errors, out_errors, uptime):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO telemetry
                (device_name, sys_uptime_ticks, in_octets, out_octets, in_errors, out_errors, is_synthetic)
            VALUES (%s, %s, %s, %s, %s, %s, TRUE)
            """,
            (DEVICE_NAME, uptime, in_octets, out_octets, in_errors, out_errors),
        )
    conn.commit()

def generate_traffic_spike(conn, baseline_in, baseline_out, uptime):
    """Simulate a sudden traffic surge — e.g. a DDoS or backup job gone wrong."""
    spike_in = baseline_in + random.randint(50000, 200000)
    spike_out = baseline_out + random.randint(50000, 200000)
    insert_synthetic(conn, spike_in, spike_out, 0, 0, uptime)
    print(f"Injected traffic spike: in={spike_in}, out={spike_out}")

def generate_error_burst(conn, baseline_in, baseline_out, uptime):
    """Simulate a failing link — packets flowing but lots of errors."""
    errors_in = random.randint(50, 500)
    errors_out = random.randint(50, 500)
    insert_synthetic(conn, baseline_in, baseline_out, errors_in, errors_out, uptime)
    print(f"Injected error burst: in_errors={errors_in}, out_errors={errors_out}")

def generate_dead_link(conn, uptime):
    """Simulate an interface going completely silent — no traffic at all."""
    insert_synthetic(conn, 0, 0, 0, 0, uptime)
    print("Injected dead link (zero traffic)")

def get_latest_baseline(conn):
    """Pull the most recent real reading to build believable anomalies around."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT in_octets, out_octets, sys_uptime_ticks
            FROM telemetry
            WHERE is_synthetic = FALSE
            ORDER BY timestamp DESC
            LIMIT 1
            """
        )
        row = cur.fetchone()
    return row if row else (10000, 10000, 400000)

if __name__ == "__main__":
    conn = psycopg2.connect(**DB_CONFIG)
    baseline_in, baseline_out, uptime = get_latest_baseline(conn)

    print("Generating synthetic anomalies based on latest real baseline:")
    print(f"  baseline_in={baseline_in}, baseline_out={baseline_out}\n")

    scenarios = [generate_traffic_spike, generate_error_burst, generate_dead_link]

    for i in range(15):
        scenario = random.choice(scenarios)
        if scenario == generate_dead_link:
            scenario(conn, uptime)
        else:
            scenario(conn, baseline_in, baseline_out, uptime)
        uptime += random.randint(2500, 3500)
        time.sleep(0.5)

    conn.close()
    print("\nDone. 15 synthetic anomaly rows inserted.")
