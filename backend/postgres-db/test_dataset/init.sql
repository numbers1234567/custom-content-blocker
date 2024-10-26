CREATE TABLE social_post_data (
    internal_id INT NOT NULL,
    post_id TEXT NOT NULL UNIQUE,
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
    email VARCHAR(50) NOT NULL UNIQUE,
    PRIMARY KEY (user_id)
);

CREATE TABLE curation_modes (
    primary_user INT NOT NULL REFERENCES user_credentials(user_id) ON DELETE CASCADE,
    curation_id INT NOT NULL UNIQUE,
    curation_name VARCHAR(20),
    curation_key VARCHAR(40) UNIQUE,
    create_utc INT,
    PRIMARY KEY (curation_id)
);

CREATE TABLE blip_curation_heads (
    curation_id INT NOT NULL REFERENCES curation_modes(curation_id) ON DELETE CASCADE,
    weight1 DECIMAL[768][10],
    weight2 DECIMAL[10][2],
    bias1 DECIMAL[10],
    bias2 DECIMAL[2],
    PRIMARY KEY (curation_id)
);

CREATE TABLE doc_freq (
    internal_id INT NOT NULL REFERENCES social_post_data(internal_id),
    n_gram TEXT NOT NULL,
    num_tokens INT NOT NULL,
    freq INT NOT NULL,
    PRIMARY KEY (internal_id, n_gram)
);

COPY social_post_data
FROM '/docker-entrypoint-initdb.d/test_post_data.csv'
DELIMITER E'\t'
CSV HEADER;

COPY blip_features
FROM '/docker-entrypoint-initdb.d/test_blip_data.csv'
DELIMITER E'\t'
CSV HEADER;

COPY user_credentials
FROM '/docker-entrypoint-initdb.d/test_user_data.csv'
DELIMITER E'\t'
CSV HEADER;

COPY curation_modes
FROM '/docker-entrypoint-initdb.d/test_curation_data.csv'
DELIMITER E'\t'
CSV HEADER;

COPY blip_curation_heads
FROM '/docker-entrypoint-initdb.d/test_blip_heads.csv'
DELIMITER E'\t'
CSV HEADER;