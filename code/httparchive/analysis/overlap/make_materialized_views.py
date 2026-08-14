import json
import itertools
import os
from pathlib import Path
import psycopg2
import sys

sys.path.append(str(Path(f"../../../global_helpers").resolve()))
from connecttodb import connect_to_db

conn = connect_to_db()
conn.autocommit = True
cursor = conn.cursor()


from generate_httparchive_dates import generate_crawl_identifiers
crawl_identifiers = generate_crawl_identifiers()
        
crawl_identifiers.sort(key = lambda date: [int(x) for x in date.split("-")])



for date1, date2 in list(itertools.combinations(crawl_identifiers, 2)):
    print(date1, date2)
    query = f"""CREATE MATERIALIZED VIEW IF NOT EXISTS view{date1.replace('-', '')}to{date2.replace('-', '')} AS
        WITH pages_1 AS (
                SELECT *
                FROM requests
                WHERE date = %s AND
                archive_hash is not NULL AND
                (document_url is not NULL OR referer is not NULL) AND
                page_domain != url_domain AND
                ((document_url_domain != '' AND page_domain=document_url_domain) OR 
                (referer_domain != '' AND page_domain=referer_domain))
            ),

            pages_2 AS (
                SELECT *
                FROM requests
                WHERE date = %s and
                archive_hash is not NULL AND
                (document_url is not NULL OR referer is not NULL) AND
                page_domain != url_domain AND
                ((document_url_domain != '' AND page_domain=document_url_domain) OR 
                (referer_domain != '' AND page_domain=referer_domain))
                )

            SELECT 
                p1.page,
                p1.url,
                p1.archive_hash AS archive_hash_1,
                p2.archive_hash AS archive_hash_2,
                p1.document_url AS document_url_1,
                p2.document_url AS document_url_2,
                p1.referer AS referer_1,
                p2.referer AS referer_2
                
            FROM pages_1 p1
            INNER JOIN pages_2 p2 ON p1.page = p2.page AND p1.url = p2.url
            WHERE
                (p1.document_url IS NOT NULL AND 
                 p1.document_url != '' AND 
                 p1.document_url = p2.document_url) 
                OR
                (p1.referer IS NOT NULL AND 
                 p2.referer != '' AND 
                 p1.referer = p2.referer)
            WITH DATA;
        """
    try:
        cursor.execute(query, (date1, date2)) 
        
    except psycopg2.Error as e:
        print(f"SQL query error: {e}")

    
    
         
