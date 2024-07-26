CREATE TABLE social_post_data (
    post_id TEXT NOT NULL,
    embed_html TEXT,
    create_utc INT,
    PRIMARY KEY (post_id)
);

COPY social_post_data
FROM '/docker-entrypoint-initdb.d/test_post_data.csv'
DELIMITER E'\t'
CSV HEADER;
