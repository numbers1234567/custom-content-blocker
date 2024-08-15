CREATE TABLE social_post_data (
    internal_id INT NOT NULL,
    post_id TEXT NOT NULL,
    title TEXT NOT NULL,
    embed_html TEXT,
    create_utc INT,
    PRIMARY KEY (internal_id)
);

CREATE TABLE blip_features (
    internal_id INT NOT NULL REFERENCES social_post_data(internal_id),
    features DECIMAL[768] NOT NULL,
    PRIMARY KEY (internal_id)
);

CREATE TABLE user_credentials (
    user_id INT NOT NULL,
    create_utc INT NOT NULL,
    email VARCHAR(50) NOT NULL,
    PRIMARY KEY (user_id)
);

CREATE TABLE curation_modes (
    primary_user INT NOT NULL REFERENCES user_credentials(user_id),
    curation_name CHAR(20),
    curation_key CHAR(40),
    create_utc INT,
    PRIMARY KEY (primary_user, curation_key)
);

COPY social_post_data
FROM '/docker-entrypoint-initdb.d/test_post_data.csv'
DELIMITER E'\t'
CSV HEADER;

COPY blip_features
FROM '/docker-entrypoint-initdb.d/test_blip_data.csv'
DELIMITER E'\t'
CSV HEADER;

