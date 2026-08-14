
import os
import pandas as pd 
from pathlib import Path
import psycopg2
import psycopg2.extras as extras
import sys
sys.path.append(str(Path(f"../../global_helpers/").resolve()))

from generate_httparchive_dates import generate_crawl_identifiers

from connecttodb import connect_to_db


crawl_identifiers = generate_crawl_identifiers()

crawl_identifiers.reverse()

conn = connect_to_db()
conn.autocommit = True
cursor = conn.cursor()


scale = 1000

for date in crawl_identifiers:
    print(date)
    outfile = Path(f"../../../data/httparchive/scripts/{date}_{scale}_httparchive_scripts.csv").resolve()
    
    
    # query = "SELECT count(date) FROM requests WHERE date = %s;"
    # cursor.execute(query, (date,)) 
    # records = cursor.fetchall()
    if os.path.isfile(outfile):
        result = pd.read_csv(outfile).iterrows()
        tuples = []
        for index, row in result:
            
            tuples.append((row["response_body_hash"], 
                           row["response_body"]))

        query ='INSERT INTO script_contents (hash, content) values (%s, %s) ON CONFLICT (hash) DO NOTHING;'      
        try:
            extras.execute_batch(cursor, query, tuples, 2000)
            conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error: {error}")