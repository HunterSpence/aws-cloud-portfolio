-- EventStream — Athena Table Definitions
-- Run these in the Athena console to query the S3 data lake

CREATE DATABASE IF NOT EXISTS eventstream;

CREATE EXTERNAL TABLE IF NOT EXISTS eventstream.raw_events (
    event_id        STRING,
    event_type      STRING,
    source          STRING,
    timestamp       STRING,
    payload         STRING,
    user_id         STRING,
    session_id      STRING,
    ip_address      STRING,
    user_agent      STRING,
    processed_at    STRING,
    shard_id        STRING
)
PARTITIONED BY (
    year    INT,
    month   INT,
    day     INT,
    hour    INT
)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
LOCATION 's3://eventstream-data-lake/raw/'
TBLPROPERTIES ('has_encrypted_data'='false');

-- Repair partitions after new data arrives
MSCK REPAIR TABLE eventstream.raw_events;
