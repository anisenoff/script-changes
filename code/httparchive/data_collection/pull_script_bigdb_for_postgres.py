
from google.cloud import bigquery
import os
from pathlib import Path
import sys
sys.path.append(str(Path(f"../../global_helpers/").resolve()))
from generate_httparchive_dates import generate_crawl_identifiers
import constants
test = False

crawl_identifiers = generate_crawl_identifiers() 
client = bigquery.Client(project=constants.BIGQUERY_PROJECT)

scale = 1000

for date in crawl_identifiers:
    print(date)
    outfile = Path(f"../../../data/httparchive/scripts/{date}_{scale}_httparchive_scripts.csv").resolve()
    
    
    if os.path.isfile(outfile):
        continue
         
    else:
        query = f"""
        SELECT 
            TO_HEX(SHA256(response_body)) as response_body_hash,
            response_body
        FROM
            `httparchive.crawl.requests`
        WHERE
            date = "{date}" AND
            client = 'desktop' AND
            rank <= {scale} AND 
            type = "script"
        """
        
        query_job = client.query(query) 
        result = query_job.result()
        query_job.to_dataframe().to_csv(outfile)
    
    if test:
        break
        