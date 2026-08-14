import json
import itertools
import multiprocessing
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


data_path = Path("../../../../data/httparchive/summary/ast/").resolve()
script_path = Path("./script_folder/").resolve()



MAX_PROCESSES = 3
CHUNK_SIZE = 50

def process_date_combo(next_element):
    conn = connect_to_db()
    conn.autocommit = True
    cursor = conn.cursor()
    r = random.randint(0, 100000000)
    while os.path.isfile(os.path.join(script_path, f"s1_{r}")):
        #make sure we don't have any file collisions
        r = random.randint(0, 100000000)
    # pull the code for the hashes
    query  = "select content from script_contents where hash = %s"
    try:
        cursor.execute(query, (next_element[4],)) 
        s2 = cursor.fetchall()[0][0]
        with open(os.path.join(script_path, f"s1_{r}") , 'w') as outfile:
            outfile.write(s2)
            
    except psycopg2.Error as e:
        print(f"SQL query error: {e}")
        return "error"
    except Exception as e:
        #print(f"other error: {e}")
        
        return "error"
    
    # pull the code for the hashes
    query  = "select content from script_contents where hash = %s"
    try:
        cursor.execute(query, (next_element[7],)) 
        s2 = cursor.fetchall()[0][0]
        with open(os.path.join(script_path, f"s2_{r}") , 'w') as outfile:
            outfile.write(s2)
            
    except psycopg2.Error as e:
        print(f"SQL query error: {e}")
        return "error"
    except Exception as e:
        #print(f"other error: {e}")
        return "error"
    

    # run the comparison code one way
    res1 = subprocess.run(["python3.14", "-O", "cli.py", "-tloose", "--threshold", "1",
                        os.path.join(script_path, f"s2_{r}"), 
                        os.path.join(script_path, f"s1_{r}")], 
                        capture_output=True, text=True, cwd='./js-compare')
    r1 = res1.stdout
    if res1.stderr:
        print(res1.stderr)
        #raise "hfghgj"
        
    res2 = subprocess.run(["python3.14", "-O", "cli.py", "-tloose", "--threshold", "2",
                        os.path.join(script_path, f"s2_{r}"), 
                        os.path.join(script_path, f"s1_{r}")], 
                        capture_output=True, text=True, cwd='./js-compare')
    r2 = res2.stdout   
        
    res3 = subprocess.run(["python3.14", "-O", "cli.py", "-tloose", "--threshold", "3",
                        os.path.join(script_path, f"s2_{r}"), 
                        os.path.join(script_path, f"s1_{r}")], 
                        capture_output=True, text=True, cwd='./js-compare')
    r3 = res3.stdout
        
    res5 = subprocess.run(["python3.14", "-O", "cli.py", "-tloose", "--threshold", "5",
                        os.path.join(script_path, f"s2_{r}"), 
                        os.path.join(script_path, f"s1_{r}")], 
                        capture_output=True, text=True, cwd='./js-compare')
    r5 = res5.stdout  
    
    res10 = subprocess.run(["python3.14", "-O", "cli.py", "-tloose", "--threshold", "10",
                        os.path.join(script_path, f"s2_{r}"), 
                        os.path.join(script_path, f"s1_{r}")], 
                        capture_output=True, text=True, cwd='./js-compare')
    r10 = res10.stdout       
        
        
    try:
        os.remove(os.path.join(script_path, f"s1_{r}"))
        os.remove(os.path.join(script_path, f"s2_{r}"))
    except:
        pass    
        

    conn.close()
    return [r1,r2,r3,r5,r10]   
        
    
    
    
num_comp =  25000
    
    
data_path = Path(f"../../../../data/httparchive/summary/ast/threshold5/").resolve()

if __name__ == '__main__':
    
    conn = connect_to_db()
    conn.autocommit = True
    cursor = conn.cursor()
    #y1, y2 = f"2024-12-1", f"2025-1-1"
    output_file = os.path.join(data_path,f"threshold_testing_ast_data.json")
    
    if os.path.isfile(output_file):
        try:
            with open(output_file) as json_file:
                output = json.load(json_file)
        except:
            print(f"error reading json file {output_file}")
    else:  
        
        
        #make json
        output = dict() 
        output["todo"] = list()
        output["done"] = list()
        output["errors"] = list()

        crawl_identifiers = generate_crawl_identifiers()
        
        threshold_comparisons_list = list()
        all_files = list(itertools.combinations(crawl_identifiers, 2))
        
        for y1, y2 in all_files:
            path = os.path.join(data_path,f"{y1}_{y2}_ast_data.json")
            if os.path.isfile(path):
                try:
                    with open(path) as json_file:
                        ast_data = json.load(json_file)
                        if len(ast_data["done"])<round(num_comp/len(all_files))+5:
                            raise f"not enough completed {y1}, {y2} {len(ast_data['done'])} {round(num_comp/len(all_files))+5}"
                        threshold_comparisons_list = threshold_comparisons_list + [x[0] for x in random.sample(ast_data["done"], round(num_comp/len(all_files))+5)]
                        
                        
                except:pass
        output["todo"] = random.sample(threshold_comparisons_list, num_comp)
        
        random.shuffle(output["todo"])
        print("random scripts selected")  

    
    all_todo = [x for x in output["todo"]]
    
    pool = multiprocessing.Pool()
    pool = multiprocessing.Pool(processes=MAX_PROCESSES)
    for i in range(0, len(all_todo), CHUNK_SIZE):
        outputs = pool.map(process_date_combo, all_todo[i:i + CHUNK_SIZE])
        print(outputs)
        output["todo"] = output["todo"][CHUNK_SIZE:]
        output["done"] = output["done"]+outputs
        with open(output_file , 'w') as outfile:
            json.dump(output, outfile)