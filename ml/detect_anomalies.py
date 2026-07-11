import psycopg2
import pandas as pd
from sklearn.ensemble import IsolationForest

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "telemetry",
    "password": "telemetry_pass",
    "dbname": "telemetry",
}

def load_data(conn):
    query = """
        SELECT id, timestamp, device_name, in_octets, out_octets,
               in_errors, out_errors, avg_latency_ms, poll_failed, is_synthetic
        FROM telemetry
        ORDER BY id
    """
    return pd.read_sql(query, conn)

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    df = load_data(conn)
    conn.close()

    print(f"Loaded {len(df)} rows\n")

    # Fill any missing values (from failed polls) with 0 so the model can process them —
    # a missing reading during a fault is itself informative, not something to discard
    features = df[["in_octets", "out_octets", "in_errors", "out_errors", "avg_latency_ms"]].fillna(0)
    # Convert poll_failed (True/False) into a numeric 1/0 so the model can use it directly
    features = features.assign(poll_failed=df["poll_failed"].fillna(False).astype(int))

    model = IsolationForest(
        n_estimators=100,
        contamination="auto",  # let the model estimate this itself, since we no longer
                                 # know the exact ratio the way we did with synthetic data
        random_state=42,
    )

    df["prediction"] = model.fit_predict(features)
    df["is_anomaly"] = df["prediction"] == -1

    print("=== Flagged anomalies ===")
    print(df[df["is_anomaly"]][
        ["id", "timestamp", "device_name", "avg_latency_ms", "poll_failed", "in_octets", "out_octets"]
    ])

    print(f"\nTotal rows: {len(df)}, flagged anomalies: {df['is_anomaly'].sum()}")

if __name__ == "__main__":
    main()
