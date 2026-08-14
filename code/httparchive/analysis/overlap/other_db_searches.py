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

out_file = Path(f"../../../../data/httparchive/summary/other_searches.json").resolve()


def run_query(query, params):
    try:
        cursor.execute(query, params) 
        return cursor.fetchall()
    except psycopg2.Error as e:
        print(f"SQL query error: {e}")
        return "error"
    
    
if os.path.isfile(out_file):
    with open(out_file) as json_file:
        summary = json.load(json_file)
else:
    summary = dict()
    
    
if not summary.get("unique_pages", None):
    query = "SELECT count(distinct(page)) FROM requests;"
    try:
        cursor.execute(query) 
        records = cursor.fetchall()
    except psycopg2.Error as e:
        print(f"SQL query error: {e}")
        records = "error"
    if records!="error":
        summary["unique_pages"] = records[0][0]
        with open(out_file, 'w') as outfile:
            json.dump(summary, outfile)

k = "total_pages"
if not summary.get(k, None):
    print(k)
    query = "SELECT count(distinct(page, date)) FROM requests;"
    try:
        cursor.execute(query) 
        records = cursor.fetchall()
    except psycopg2.Error as e:
        print(f"SQL query error: {e}")
        records = "error"
    if records!="error":
        summary[k] = records[0][0]
        with open(out_file, 'w') as outfile:
            json.dump(summary, outfile)

k = "unique_urls"
if not summary.get(k, None):
    print(k)
    query = "SELECT count(distinct(url)) FROM requests;"
    try:
        cursor.execute(query) 
        records = cursor.fetchall()
    except psycopg2.Error as e:
        print(f"SQL query error: {e}")
        records = "error"
    if records!="error":
        summary[k] = records[0][0]
        with open(out_file, 'w') as outfile:
            json.dump(summary, outfile)

k = "all_urls"
if not summary.get(k, None):
    print(k)
    query = "SELECT count(url) FROM requests;"
    try:
        cursor.execute(query) 
        records = cursor.fetchall()
    except psycopg2.Error as e:
        print(f"SQL query error: {e}")
        records = "error"
    if records!="error":
        summary[k] = records[0][0]
        with open(out_file, 'w') as outfile:
            json.dump(summary, outfile)
                        
