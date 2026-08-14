import json
import itertools
import os
from pathlib import Path
import psycopg2
import sys

sys.path.append(str(Path(f"../../../global_helpers").resolve()))
from connecttodb import connect_to_db
from generate_httparchive_dates import generate_crawl_identifiers

conn = connect_to_db()
conn.autocommit = True
cursor = conn.cursor()

out_file = Path(f"../../../../data/httparchive/summary/basic_overlap.json").resolve()


crawl_identifiers = generate_crawl_identifiers()
        
crawl_identifiers.sort(key = lambda date: [int(x) for x in date.split("-")])



if os.path.isfile(out_file):
    with open(out_file) as json_file:
        summary = json.load(json_file)
else:
    summary = dict()
    
    
    
def run_query(query, params):
    try:
        cursor.execute(query, params) 
        return cursor.fetchall()
    except psycopg2.Error as e:
        print(f"SQL query error: {e}")
        return "error"

# collect stats about each month
for date in crawl_identifiers:
    print(date)
    summary[date] = summary.get(date, dict())
    
    
    
    if not summary[date].get("total_pages", None):
        query = "SELECT count(distinct(page)) FROM requests WHERE date = %s;"
        records = run_query(query, (date,))
        if records!="error":
            summary[date]["total_pages"] = records[0][0]
            with open(out_file, 'w') as outfile:
                json.dump(summary, outfile)

    if not summary[date].get("total_requests", None):
        query = "SELECT count(distinct(page, url, document_url, referer, archive_hash)) FROM requests WHERE date = %s;"
        records = run_query(query, (date,))
        if records!="error":
            summary[date]["total_requests"] = records[0][0]
            with open(out_file, 'w') as outfile:
                json.dump(summary, outfile)
            
    if not summary[date].get("requests_w_hash", None):
        query = """SELECT count(distinct(page, url, document_url, referer, archive_hash)) 
                   FROM requests 
                   WHERE date = %s AND
                   archive_hash is NOT NULL;"""
        records = run_query(query, (date,))
        if records!="error":
            summary[date]["requests_w_hash"] = records[0][0]
            with open(out_file, 'w') as outfile:
                json.dump(summary, outfile)
            
    if not summary[date].get("requests_w_ref_better", None):
        query = """SELECT count(distinct(page, url, document_url, referer, archive_hash)) 
                   FROM requests 
                   WHERE date = %s AND
                   ((document_url is NOT NULL AND document_url != '') OR
                   (referer is NOT NULL AND referer != ''));"""
        records = run_query(query, (date,))
        if records!="error":
            summary[date]["requests_w_ref_better"] = records[0][0]
            with open(out_file, 'w') as outfile:
                json.dump(summary, outfile)
    
    if not summary[date].get("requests_3rd_pty", None):
        query = """SELECT count(distinct(page, url, document_url, referer, archive_hash)) 
                   FROM requests 
                   WHERE date = %s AND
                   (page_domain != url_domain);"""
        records = run_query(query, (date,))
        if records!="error":
            summary[date]["requests_3rd_pty"] = records[0][0]
            with open(out_file, 'w') as outfile:
                json.dump(summary, outfile)
            
    if not summary[date].get("requests_not_diff_ref", None):
        query = """SELECT count(distinct(page_domain, document_url_domain, referer_domain, archive_hash)) 
                   FROM requests 
                   WHERE date = %s AND
                   ((document_url_domain != '' AND page_domain=document_url_domain) OR 
                    (referer_domain != '' AND page_domain=referer_domain))
                   ;"""
        records = run_query(query, (date,))
        if records!="error":
            summary[date]["requests_not_diff_ref"] = records[0][0]
            with open(out_file, 'w') as outfile:
                json.dump(summary, outfile)
     
    if not summary[date].get("requests_usable_not_restrict_ref", None):
        query = """SELECT count(distinct(page, url, document_url, referer, archive_hash)) 
                   FROM requests 
                   WHERE date = %s AND
                   (page_domain != url_domain) AND 
                   (document_url is NOT NULL OR
                    referer is NOT NULL) AND 
                    archive_hash is NOT NULL;"""
        records = run_query(query, (date,))
        
        if records!="error":
            summary[date]["requests_usable_not_restrict_ref"] = records[0][0]
            with open(out_file, 'w') as outfile:
                json.dump(summary, outfile)
            
          
    if not summary[date].get("requests_usable", None):
        query = """SELECT count(distinct(page, url, document_url, referer, archive_hash)) 
                   FROM requests 
                   WHERE date = %s AND
                   (page_domain != url_domain) AND 
                   (document_url is NOT NULL OR
                    referer is NOT NULL) AND 
                    archive_hash is NOT NULL AND
                   ((document_url_domain != '' AND page_domain=document_url_domain) OR 
                    (referer_domain != '' AND page_domain=referer_domain));"""
        records = run_query(query, (date,))
        
        if records!="error":
            summary[date]["requests_usable"] = records[0][0]
            with open(out_file, 'w') as outfile:
                json.dump(summary, outfile)
            
           
    

for date1, date2 in list(itertools.combinations(crawl_identifiers, 2)):
    print(date1, date2)
    summary[date1][date2] = summary[date1].get(date2, dict())
    summary[date2][date1] = summary[date2].get(date1, dict())
    
    if summary[date1][date2].get("page_overlap", None)==None:
        # page overlap
        query = '''
            WITH pages_1 AS (
                SELECT distinct page
                FROM requests
                WHERE date = %s
            ),
            pages_2 AS (
                SELECT distinct page
                FROM requests
                WHERE date = %s
                )
            SELECT count(*)
            FROM pages_1 
            JOIN pages_2
            using  (page)
        '''
        records = run_query(query, (date1, date2))
        if records!="error":
            summary[date1][date2]["page_overlap"] = records[0][0]
            summary[date2][date1]["page_overlap"] = records[0][0]
            with open(out_file, 'w') as outfile:
                json.dump(summary, outfile)
        
    key = "req_overlap_not_iframe"
    if summary[date1][date2].get(key, None)==None:    
        #request overlap 
        query = '''
            WITH pages_1 AS (
                SELECT distinct page, url, document_url, referer, archive_hash
                FROM requests
                WHERE date = %s AND
                archive_hash is not NULL AND
                (document_url is not NULL OR referer is not NULL) AND
                page_domain != url_domain AND
                ((document_url_domain != '' AND page_domain=document_url_domain) OR 
                (referer_domain != '' AND page_domain=referer_domain))
            ),

            pages_2 AS (
                SELECT distinct page, url, document_url, referer, archive_hash
                FROM requests
                WHERE date = %s and
                archive_hash is not NULL AND
                (document_url is not NULL OR referer is not NULL) AND
                page_domain != url_domain AND
                ((document_url_domain != '' AND page_domain=document_url_domain) OR 
                (referer_domain != '' AND page_domain=referer_domain))
                )

            SELECT count(*)
            FROM pages_1 
            JOIN pages_2
            using  (page, url)
            WHERE
                ((pages_1.document_url is not NULL and 
                 pages_2.document_url is not NULL and 
                 pages_1.document_url = pages_2.document_url) or
                (pages_1.referer is not NULL and 
                 pages_2.referer is not NULL and 
                 pages_1.referer = pages_2.referer)) 
        '''
        records = run_query(query, (date1, date2))
        if records!="error":
            summary[date1][date2][key] = records[0][0]
            summary[date2][date1][key] = records[0][0]
            with open(out_file, 'w') as outfile:
                json.dump(summary, outfile)
     
        
    if summary[date1][date2].get("req_overlap", None)==None:    
        #request overlap 
        query = '''
            WITH pages_1 AS (
                SELECT distinct page, url, document_url, referer, archive_hash
                FROM requests
                WHERE date = %s AND
                archive_hash is not NULL AND
                (document_url is not NULL OR referer is not NULL) AND
                page_domain != url_domain
            ),

            pages_2 AS (
                SELECT distinct page, url, document_url, referer, archive_hash
                FROM requests
                WHERE date = %s and
                archive_hash is not NULL AND
                (document_url is not NULL OR referer is not NULL) AND
                page_domain != url_domain
                )

            SELECT count(*)
            FROM pages_1 
            JOIN pages_2
            using  (page, url)
            WHERE
                ((pages_1.document_url is not NULL and 
                 pages_2.document_url is not NULL and 
                 pages_1.document_url = pages_2.document_url) or
                (pages_1.referer is not NULL and 
                 pages_2.referer is not NULL and 
                 pages_1.referer = pages_2.referer)) 
        '''
        records = run_query(query, (date1, date2))
        if records!="error":
            summary[date1][date2]["req_overlap"] = records[0][0]
            summary[date2][date1]["req_overlap"] = records[0][0]
            with open(out_file, 'w') as outfile:
                json.dump(summary, outfile)
        
    key = "req_union"  
    if summary[date1][date2].get(key, None)==None:  
        print(key)   
        query = '''
            SELECT count(distinct(page, url, document_url, referer, archive_hash, date))
                FROM requests
                WHERE (date = %s or date = %s) AND
                archive_hash is not NULL AND
                (document_url is not NULL OR referer is not NULL) AND
                page_domain != url_domain
            
        '''
        records = run_query(query, (date1, date2))
        if records!="error":
            summary[date1][date2][key] = records[0][0]
            summary[date2][date1][key] = records[0][0]
            with open(out_file, 'w') as outfile:
                json.dump(summary, outfile)
    
    key = "req_union_not_iframe"  
    if summary[date1][date2].get(key, None)==None:  
        print(key)   
        query = '''
            SELECT count(distinct(page, url, document_url, referer, archive_hash, date))
                FROM requests
                WHERE (date = %s or date = %s) AND
                archive_hash is not NULL AND
                (document_url is not NULL OR referer is not NULL) AND
                page_domain != url_domain AND
                ((document_url_domain != '' AND page_domain=document_url_domain) OR 
                (referer_domain != '' AND page_domain=referer_domain))
            
        '''
        records = run_query(query, (date1, date2))
        if records!="error":
            summary[date1][date2][key] = records[0][0]
            summary[date2][date1][key] = records[0][0]
            with open(out_file, 'w') as outfile:
                json.dump(summary, outfile)    
        
    key = "req_overlap_hash_diff"
    if summary[date1][date2].get(key, None)==None:
        print(key)
            #request unique 
        query = '''
            WITH pages_1 AS (
                SELECT distinct page, url, document_url, referer, archive_hash
                FROM requests
                WHERE date = %s AND
                archive_hash is not NULL AND
                (document_url is not NULL OR referer is not NULL) AND
                page_domain != url_domain
            ),

            pages_2 AS (
                SELECT distinct page, url, document_url, referer, archive_hash
                FROM requests
                WHERE date = %s and
                archive_hash is not NULL AND
                (document_url is not NULL OR referer is not NULL) AND
                page_domain != url_domain
                )

            SELECT count(*)
            FROM pages_1 
            JOIN pages_2
            using  (page, url)
            WHERE
                ((pages_1.document_url is not NULL and 
                 pages_2.document_url is not NULL and 
                 pages_1.document_url = pages_2.document_url) or
                (pages_1.referer is not NULL and 
                 pages_2.referer is not NULL and 
                 pages_1.referer = pages_2.referer))  and
                pages_1.archive_hash!=pages_2.archive_hash
                
        '''
        records = run_query(query, (date1, date2))
        if records!="error":
            summary[date1][date2][key] = records[0][0]
            summary[date2][date1][key] = records[0][0]
            with open(out_file, 'w') as outfile:
                json.dump(summary, outfile)
            

    key = "req_overlap_hash_diff_not_iframe"
    if summary[date1][date2].get(key, None)==None:
            #request unique 
        query = '''
            WITH pages_1 AS (
                SELECT distinct page, url, document_url, referer, archive_hash
                FROM requests
                WHERE date = %s AND
                archive_hash is not NULL AND
                (document_url is not NULL OR referer is not NULL) AND
                page_domain != url_domain AND
                   ((document_url_domain != '' AND page_domain=document_url_domain) OR 
                    (referer_domain != '' AND page_domain=referer_domain))
            ),

            pages_2 AS (
                SELECT distinct page, url, document_url, referer, archive_hash
                FROM requests
                WHERE date = %s and
                archive_hash is not NULL AND
                (document_url is not NULL OR referer is not NULL) AND
                page_domain != url_domain AND
                   ((document_url_domain != '' AND page_domain=document_url_domain) OR 
                    (referer_domain != '' AND page_domain=referer_domain))
                )

            SELECT count(*)
            FROM pages_1 
            JOIN pages_2
            using  (page, url)
            WHERE
                ((pages_1.document_url is not NULL and 
                 pages_2.document_url is not NULL and 
                 pages_1.document_url = pages_2.document_url) or
                (pages_1.referer is not NULL and 
                 pages_2.referer is not NULL and 
                 pages_1.referer = pages_2.referer))  and
                pages_1.archive_hash!=pages_2.archive_hash
                
        '''
        records = run_query(query, (date1, date2))
        if records!="error":
            summary[date1][date2][key] = records[0][0]
            summary[date2][date1][key] = records[0][0]
            with open(out_file, 'w') as outfile:
                json.dump(summary, outfile)
            
    #note this is for not in iframe stuff
    key = "rank_split_hash_diff_not_iframe"
    if summary[date1][date2].get(key, None)==None:
            #request unique 
        query = '''
            WITH pages_1 AS (
                SELECT distinct rank, page, url, document_url, referer, archive_hash
                FROM requests
                WHERE date = %s AND
                archive_hash is not NULL AND
                (document_url is not NULL OR referer is not NULL) AND
                page_domain != url_domain AND
                   ((document_url_domain != '' AND page_domain=document_url_domain) OR 
                    (referer_domain != '' AND page_domain=referer_domain))
            ),

            pages_2 AS (
                SELECT distinct rank, page, url, document_url, referer, archive_hash
                FROM requests
                WHERE date = %s and
                archive_hash is not NULL AND
                (document_url is not NULL OR referer is not NULL) AND
                page_domain != url_domain AND
                   ((document_url_domain != '' AND page_domain=document_url_domain) OR 
                    (referer_domain != '' AND page_domain=referer_domain))
                )

            SELECT pages_1.rank, pages_2.rank, count(*)  AS total_count
            FROM pages_1 
            JOIN pages_2
            using  (page, url)
            WHERE
                ((pages_1.document_url is not NULL and 
                 pages_2.document_url is not NULL and 
                 pages_1.document_url = pages_2.document_url) or
                (pages_1.referer is not NULL and 
                 pages_2.referer is not NULL and 
                 pages_1.referer = pages_2.referer))  and
                pages_1.archive_hash!=pages_2.archive_hash
            GROUP BY 
                pages_1.rank, 
                pages_2.rank
        '''
        records = run_query(query, (date1, date2))
        if records!="error":
            summary[date1][date2][key] = records
            summary[date2][date1][key] = records
            with open(out_file, 'w') as outfile:
                json.dump(summary, outfile)

for date1, date2 in list(itertools.combinations(crawl_identifiers, 2)):
    print(date1, date2)
    key = "rank_split_hash_diff"
    if summary[date1][date2].get(key, None)==None:
            #request unique 
        query = '''
            WITH pages_1 AS (
                SELECT distinct rank, page, url, document_url, referer, archive_hash
                FROM requests
                WHERE date = %s AND
                archive_hash is not NULL AND
                (document_url is not NULL OR referer is not NULL) AND
                page_domain != url_domain AND
                   ((document_url_domain != '' AND page_domain=document_url_domain) OR 
                    (referer_domain != '' AND page_domain=referer_domain))
            ),

            pages_2 AS (
                SELECT distinct rank, page, url, document_url, referer, archive_hash
                FROM requests
                WHERE date = %s and
                archive_hash is not NULL AND
                (document_url is not NULL OR referer is not NULL) AND
                page_domain != url_domain 
                )

            SELECT pages_1.rank, pages_2.rank, count(*)  AS total_count
            FROM pages_1 
            JOIN pages_2
            using  (page, url)
            WHERE
                ((pages_1.document_url is not NULL and 
                 pages_2.document_url is not NULL and 
                 pages_1.document_url = pages_2.document_url) or
                (pages_1.referer is not NULL and 
                 pages_2.referer is not NULL and 
                 pages_1.referer = pages_2.referer))  and
                pages_1.archive_hash!=pages_2.archive_hash
            GROUP BY 
                pages_1.rank, 
                pages_2.rank
        '''
        records = run_query(query, (date1, date2))
        if records!="error":
            summary[date1][date2][key] = records
            summary[date2][date1][key] = records
            with open(out_file, 'w') as outfile:
                json.dump(summary, outfile)
