import psycopg2
import pandas as pd
import logging
from sklearn.ensemble import IsolationForest

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "telemetry",
    "password": "telemetry_pass",
    "dbname": "telemetry",
}

# Set up syslog-style logging: timestamped, severity-tagged, written to a file
logging.basicConfig(
    filename="alerts.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

def load_data(conn):
    query = """
        SELECT id, timestamp, device_name, in_octets, out_octets,
               in_errors, out_errors, avg_latency_ms, poll_failed, is_synthetic
        FROM telemetry
        ORDER BY id
    """
    return pd.read_sql(query, conn)

def classify_severity(row):
    """Simple rule-of-thumb severity, based on what we know actually happens in real faults."""
    if row["poll_failed"]:
        return "CRITICAL"
    if pd.notna(row["avg_latency_ms"]) and row["avg_latency_ms"] > 1500:
        return "WARNING"
    return "INFO"

def raise_alert(conn, row):
    severity = classify_severity(row)
    reason_parts = []
    if row["poll_failed"]:
        reason_parts.append("SNMP poll failure/timeout")
    if pd.notna(row["avg_latency_ms"]) and row["avg_latency_ms"] > 1500:
        reason_parts.append(f"high latency ({row['avg_latency_ms']}ms)")
    if not reason_parts:
        reason_parts.append("anomalous traffic pattern")
    reason = "; ".join(reason_parts)

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO alerts (device_name, telemetry_id, reason, severity, avg_latency_ms, poll_failed)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (row["device_name"], row["id"], reason, severity, row["avg_latency_ms"], bool(row["poll_failed"])),
        )
    conn.commit()

    log_line = f"{severity} - device={row['device_name']} telemetry_id={row['id']} reason=\"{reason}\""
    if severity == "CRITICAL":
        logging.critical(log_line)
    elif severity == "WARNING":
        logging.warning(log_line)
    else:
        logging.info(log_line)

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    df = load_data(conn)

    print(f"Loaded {len(df)} rows\n")

    features = df[["in_octets", "out_octets", "in_errors", "out_errors", "avg_latency_ms"]].fillna(0)
    features = features.assign(poll_failed=df["poll_failed"].fillna(False).astype(int))

    model = IsolationForest(n_estimators=100, contamination="auto", random_state=42)
    df["prediction"] = model.fit_predict(features)
    df["is_anomaly"] = df["prediction"] == -1

    anomalies = df[df["is_anomaly"]]
    print(f"Flagging {len(anomalies)} anomalies as alerts...\n")

    for _, row in anomalies.iterrows():
        raise_alert(conn, row)

    conn.close()
    print("Done. Check alerts.log and the 'alerts' table in Postgres.")

if __name__ == "__main__":
    main()
