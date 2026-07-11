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
        SELECT id, timestamp, in_octets, out_octets, in_errors, out_errors, is_synthetic
        FROM telemetry
        ORDER BY id
    """
    return pd.read_sql(query, conn)

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    df = load_data(conn)
    conn.close()

    print(f"Loaded {len(df)} rows ({df['is_synthetic'].sum()} synthetic, {(~df['is_synthetic']).sum()} real)\n")

    # These four columns are what the model actually "looks at" to judge normal vs abnormal
    features = df[["in_octets", "out_octets", "in_errors", "out_errors"]]

    model = IsolationForest(
        n_estimators=100,   # how many random trees to build
        contamination=0.3,  # our rough guess: ~30% of this dataset is anomalous (we know, since we injected it)
        random_state=42,    # fixes randomness so results are reproducible run-to-run
    )

    # fit_predict: trains the model AND scores every row in one step
    # returns -1 for "anomaly", 1 for "normal"
    df["prediction"] = model.fit_predict(features)
    df["is_anomaly"] = df["prediction"] == -1

    # How well did it do? Compare against our known ground truth (is_synthetic)
    true_positives = ((df["is_anomaly"]) & (df["is_synthetic"])).sum()
    false_positives = ((df["is_anomaly"]) & (~df["is_synthetic"])).sum()
    false_negatives = ((~df["is_anomaly"]) & (df["is_synthetic"])).sum()
    true_negatives = ((~df["is_anomaly"]) & (~df["is_synthetic"])).sum()

    print("=== Confusion matrix ===")
    print(f"True positives  (correctly flagged synthetic anomalies): {true_positives}")
    print(f"False positives (real data wrongly flagged as anomaly):  {false_positives}")
    print(f"False negatives (synthetic anomalies missed):            {false_negatives}")
    print(f"True negatives  (real data correctly left alone):        {true_negatives}")

    print("\n=== Flagged anomalies ===")
    print(df[df["is_anomaly"]][["id", "timestamp", "in_octets", "out_octets", "in_errors", "out_errors", "is_synthetic"]])

if __name__ == "__main__":
    main()
