CREATE TABLE telemetry (
    id SERIAL PRIMARY KEY,
    device_name TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    sys_uptime_ticks BIGINT,
    in_octets BIGINT,
    out_octets BIGINT,
    in_errors BIGINT,
    out_errors BIGINT
);
