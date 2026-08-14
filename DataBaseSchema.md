# BigDB HTTPArchive
psql downstream


## Requests Table
CREATE TABLE requests (
    date date NOT NULL,
    rank integer NOT NULL,
    page text NOT NULL,
    page_domain text,
    url text NOT NULL,
    url_domain text,
    archive_hash text,
    req_index integer,
    referer text,
    referer_domain text,
    frame_id text,
    respBodySize integer,
    document_url text,
    document_url_domain text
);

## script script_contents table
CREATE TABLE script_contents (
    hash text NOT NULL UNIQUE,
    content text NOT NULL
);

# PageGraph Tables

## Pages 
CREATE TABLE pg_pages (
    date smallint NOT NULL,
    page text NOT NULL,
    path text NOT NULL,
    subpage bool NOT NULL
);

# Requests
CREATE TABLE pg_requests_new (
    crawl_date smallint NOT NULL,
    page text NOT NULL,
    page_domain text NOT NULL,
    url text NOT NULL,
    url_domain text NOT NULL,
    frame text,
    frame_domain text,
    hash text,
    all_effects_new JSONB, 
    path text NOT NULL,
    timestamp INT
);


# SRI Info
CREATE TABLE pg_sri (
    crawl_date smallint NOT NULL,
    page text NOT NULL,
    url text NOT NULL,
    req_hash text, 
    sha256 text, 
    sha384 text,
    sha512 text,
    frame text,
    html_tag_info text,
    html_hash text
);

