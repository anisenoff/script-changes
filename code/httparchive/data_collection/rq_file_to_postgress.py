import numpy as np
import os
import pandas as pd
from pathlib import Path
import psycopg2
import psycopg2.extras as extras
import sys
sys.path.append(str(Path(f"../../global_helpers/").resolve()))
import tldextract
from generate_httparchive_dates import generate_crawl_identifiers

from connecttodb import connect_to_db


crawl_identifiers = generate_crawl_identifiers()



conn = connect_to_db()
conn.autocommit = True
cursor = conn.cursor()


scale = 100000

for date in crawl_identifiers:
    print(date)
    
    outfile = Path(f"../../../data/httparchive/requests/{date}_{scale}_httparchive_requests.csv").resolve()
    
    query = "SELECT count(date) FROM requests WHERE date = %s;"
    cursor.execute(query, (date,)) 
    records = cursor.fetchall()
    print(records)
    if records[0][0]!=0:
       # records already in database
       continue
    if os.path.isfile(outfile):
        if date=="2025-10-1" or date=="2026-5-1": 
            # these files cause a segfault if read with the C engine
            # the python engine is slower so it is only used for this file
            result = pd.read_csv(outfile, engine='python')
        else:
            result = pd.read_csv(outfile)
            
        result = result.replace({np.nan: None})
            
        tuples = []
        for index, row in result.iterrows():
            try:
                tuples.append((date, 
                           row["rank"], 
                           row["page"], 
                           tldextract.extract(row["page"]).top_domain_under_public_suffix,
                           row["url"], 
                           tldextract.extract(row["url"]).top_domain_under_public_suffix,
                           row["payload_hash"],
                           row.get("req_index",-1), 
                           row.get("referer",None),
                           tldextract.extract(row["referer"]).top_domain_under_public_suffix if row.get("referer",None) != None else None,
                           row["frame_id"], 
                           int(row.get("respBodySize",-1)), 
                           row["document_url"] if row["document_url"] else None,
                           tldextract.extract(row["document_url"]).top_domain_under_public_suffix if row.get("document_url", None) != None else None
                           ))
            except:
                print(tldextract.extract(row["referer"]).top_domain_under_public_suffix if row.get("referer", None) != None else None)
                print(tldextract.extract(row["document_url"]).top_domain_under_public_suffix if row.get("document_url", None) != None else None)
                raise Exception
        query = '''INSERT INTO requests (date, rank, page, page_domain, url, url_domain, archive_hash, req_index, referer, referer_domain, frame_id, respBodySize, document_url, document_url_domain) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
        try:
            extras.execute_batch(cursor, query, tuples, 20000)
            conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"error writing to db: {error}")
            conn.rollback()  
