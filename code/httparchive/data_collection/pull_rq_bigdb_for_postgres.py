
from google.cloud import bigquery
import os
import pandas
from pathlib import Path
import sys
sys.path.append(str(Path(f"../../global_helpers/").resolve()))
from generate_httparchive_dates import generate_crawl_identifiers
import constants
test = False

crawl_identifiers = generate_crawl_identifiers()
        
client = bigquery.Client(project=constants.BIGQUERY_PROJECT)

scale = 100000


for date in crawl_identifiers:
    print(date)
    outfile = Path(f"../../../data/httparchive/requests/{date}_{scale}_httparchive_requests.csv").resolve()
    
    if os.path.isfile(outfile):
        continue 
    else:
        query = f"""
        SELECT 
            rank,
            page,
            url, 
            JSON_VALUE(payload, '$._body_hash') AS payload_hash, 
            index,
            (SELECT h.value
                FROM UNNEST(request_headers) AS h
                WHERE LOWER(h.name) = 'referer'
                LIMIT 1
            ) AS referer,
            JSON_VALUE(payload, '$._frame_id') AS frame_id,
            JSON_VALUE(summary, '$.respBodySize') AS resp_body_size,    
            JSON_VALUE(payload, '$._documentURL') AS document_url,
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
    
    
    