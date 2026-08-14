import json
import itertools
import multiprocessing
import glob
import os
from pathlib import Path
import psycopg2
#python3.14 -m pip install --upgrade --force-reinstall psycopg2
import random
import regex as re
import sys
import subprocess

sys.path.append(str(Path(f"../../../global_helpers").resolve()))
from connecttodb import connect_to_db
from generate_httparchive_dates import generate_crawl_identifiers

conn = connect_to_db()
conn.autocommit = True
cursor = conn.cursor()


data_path = Path("../../../../data/httparchive/summary/ast/threshold5/").resolve()
script_path = Path("./script_folder/").resolve()


sample_prop = 1


MAX_PROCESSES = 11
CHUNK_SIZE = 155


threshold = 5
def process_date_combo(date_combo):
    conn = connect_to_db()
    conn.autocommit = True
    cursor = conn.cursor()
    y1, y2 = date_combo
    
    if y1==y2:
        print(f"skipping {y1} == {y2}")
        return
    
    output_file = os.path.join(data_path,f"{y1}_{y2}_ast_data.json")
    
    if os.path.isfile(output_file):
        try:
            with open(output_file) as json_file:
                output = json.load(json_file)
                if sample_prop:
                    sample_num = round((len(output["done"])+len(output["todo"])+len(output["errors"]))*sample_prop)
                    if len(output["todo"])==0 or (sample_prop!=None and len(output["done"])+len(output["errors"])>=sample_num):
                        #print(y1, y2, "file completed")
                        return
                else:
                    sample_num = len(output["done"])+len(output["todo"])+len(output["errors"])
                    if len(output["todo"])==0:
                        print(y1, y2, "file completed")
                        return
        except:
            print(f"error reading json file {date_combo}")
            return
    else:  
        print(y1, y2)
        
        #make json
        output = dict() 
        output["todo"] = list()
        output["done"] = list()
        output["errors"] = list()


        query = '''
            WITH pages_1 AS (
                SELECT page, url, document_url, referer, archive_hash
                FROM requests
                WHERE date = %s AND
                rank <= 1000 AND
                archive_hash is not NULL AND 
                archive_hash != 'NaN' AND
                page_domain != url_domain
            ),

            pages_2 AS (
                SELECT page, url, document_url, referer, archive_hash
                FROM requests
                WHERE date = %s AND
                rank <= 1000 AND
                archive_hash is not NULL AND 
                archive_hash != 'NaN' AND 
                page_domain != url_domain
                )

            SELECT *
            FROM pages_1 
            JOIN pages_2
            using  (page, url)
            WHERE
                (
                    (pages_1.document_url is not NULL AND 
                     pages_2.document_url is not NULL AND
                     pages_1.document_url != 'NaN' AND 
                     pages_2.document_url != 'NaN' AND 
                     pages_1.document_url = pages_2.document_url) OR
                    (pages_1.referer is not NULL AND
                     pages_2.referer is not NULL AND
                     pages_1.referer != 'NaN' AND
                     pages_2.referer != 'NaN' AND
                     pages_1.referer = pages_2.referer)
                ) AND
                pages_1.archive_hash!=pages_2.archive_hash
                
        '''
        try:
            cursor.execute(query, (y1, y2)) 
            records = cursor.fetchall()
            sample_num = round(len(records)*sample_prop)
            
            output["todo"]=records
            random.shuffle(output["todo"])
            
            with open(output_file , 'w') as outfile:
                json.dump(output, outfile)
            
        except psycopg2.Error as e:
            print(f"SQL query error: {e}")
            return

    
    
        
    r = random.randint(0, 100000000)
    while os.path.isfile(os.path.join(script_path, f"s1_{r}")):
        #make sure we don't have any file collisions
        r = random.randint(0, 100000000)
    backup_couner = 0
    backup_rate = 10
    print(y1, y2, f"{sample_num} {(len(output['done'])+len(output['errors']))/sample_num if sample_num else len(output['todo'])}")
    while len(output["todo"])>0 and len(output["done"])+len(output["errors"]) < sample_num:
        backup_couner +=1
        
        if backup_couner%backup_rate==0:
            with open(output_file , 'w') as outfile:
                json.dump(output, outfile)
        next_element = output["todo"].pop(0)
        
        # pull the code for the hashes
        query  = "select content from script_contents where hash = %s"
        try:
            cursor.execute(query, (next_element[4],)) 
            s1 = cursor.fetchall()[0][0]
            with open(os.path.join(script_path, f"s1_{r}") , 'w') as outfile:
                outfile.write(s1)
        except psycopg2.Error as e:
            print(f"SQL query error: {e}")
            output["errors"].append((next_element, str(e)))
            continue
        except Exception as e:
            #print(f"other error: {e}")
            output["errors"].append((next_element, str(e)))
            continue
        
        # pull the code for the hashes
        query  = "select content from script_contents where hash = %s"
        try:
            cursor.execute(query, (next_element[7],)) 
            s2 = cursor.fetchall()[0][0]
            with open(os.path.join(script_path, f"s2_{r}") , 'w') as outfile:
                outfile.write(s2)
                
        except psycopg2.Error as e:
            print(f"SQL query error: {e}")
            output["errors"].append((next_element, str(e)))
            continue
        except Exception as e:
            #print(f"other error: {e}")
            output["errors"].append((next_element, str(e)))
            continue
        
        # run the comparison code one direction
        res = subprocess.run(["python3.14", "-O", "cli.py", "-tloose", "--threshold", str(threshold),
                            os.path.join(script_path, f"s2_{r}"), 
                            os.path.join(script_path, f"s1_{r}")], 
                            capture_output=True, text=True, cwd='./js-compare')
        comp21 = res.stdout
        
        # comp12 = ""
        # if comp21 != "":
        #     res = subprocess.run(["python3.14", "-O", "cli.py", "-tloose", 
        #                         os.path.join(script_path, f"s1_{r}"), 
        #                         os.path.join(script_path, f"s2_{r}")], 
        #                         capture_output=True, text=True, cwd='./js-compare')
        #     comp12 = res.stdout

        # put in the output
        if comp21=="":# or comp21=="":            
            if "BABEL_PARSER_SYNTAX_ERROR" in res.stderr:
                match = re.search(r"reasonCode: '([^']+)'", res.stderr)
                if match:
                    error_code = match.group(1)
                    if error_code == "MissingSemicolon":
                        try:
                            json.loads(s1)
                            #json.loads(s2)
                            is_json = True
                        except:
                            is_json = False
                        output["errors"].append((next_element, str(error_code), is_json))
                    else:
                        output["errors"].append((next_element, str(error_code)))
                else:
                    output["errors"].append((next_element, str(res.stderr)[:400]))
            else:
               output["errors"].append((next_element, str(res.stderr)[:400]))           
        else:
            output["done"].append([next_element, comp21, len(s1), len(s2)]) #comp12, 
           
        try:
            os.remove(os.path.join(script_path, f"s1_{r}"))
            os.remove(os.path.join(script_path, f"s2_{r}"))
        except:
            pass    
        
    with open(output_file , 'w') as outfile:
        json.dump(output, outfile)
    conn.close()
        

if __name__ == '__main__':
    
    crawl_identifiers = generate_crawl_identifiers()
    combos = list(itertools.combinations(crawl_identifiers, 2))
    random.shuffle(combos)
    
    for f in glob.glob(os.path.join(script_path, "s1_*")):
        os.remove(f)
    for f in glob.glob(os.path.join(script_path, "s2_*")):
        os.remove(f)
    
    pool = multiprocessing.Pool()
    pool = multiprocessing.Pool(processes=MAX_PROCESSES)
    for i in range(0, len(combos), CHUNK_SIZE):
        outputs = pool.map(process_date_combo, combos[i:i + CHUNK_SIZE])
        print(outputs)
    
    for f in glob.glob(os.path.join(script_path, "s1_*")):
        os.remove(f)
    for f in glob.glob(os.path.join(script_path, "s2_*")):
        os.remove(f)