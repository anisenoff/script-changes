import json
import itertools
import os
from pathlib import Path
import psycopg2
import sys
from datetime import datetime

sys.path.append(str(Path(f"../../../global_helpers").resolve()))
from generate_httparchive_dates import generate_crawl_identifiers

out_file = Path(f"../../../../data/httparchive/summary/ast/window_overlap.json").resolve()

ast_data_path = Path(f"../../../../data/httparchive/summary/ast/threshold5/").resolve()



crawl_identifiers = generate_crawl_identifiers()


if os.path.isfile(out_file):
    with open(out_file) as json_file:
        summary = json.load(json_file)
else:
    summary = dict()


for time_period in [1,2, 3, 6, 12, 100]:
    if str(time_period) in summary:
        print(f"time period: {time_period} completed")
        continue
    else:
        print(f"starting time period: {time_period}")
    summary[str(time_period)] = dict()
    
    ast_comps_for_time_period = []
    
    for date1, date2 in list(itertools.combinations(crawl_identifiers, 2)):
        
        d1 = datetime.strptime(date1,"%Y-%m-%d")
        d2 = datetime.strptime(date2,"%Y-%m-%d")
        months_diff = (d2.year - d1.year) * 12 + (d2.month - d1.month)

        if months_diff<=time_period:
            # read in json
            path = os.path.join(ast_data_path,f"{date1}_{date2}_ast_data.json")
            if not os.path.isfile(path):
                print(f"file does not exist: {str(path)}")
                continue
            
            with open(path) as json_file:
                ast_data = json.load(json_file)
                for r in ast_data["done"]:
                    
                    page = r[0][0]
                    url = r[0][1]
                    document_url_1 = r[0][2] if r[0][2] else ""
                    document_url_2 = r[0][5] if r[0][5] else ""
                    referer_1 = r[0][3] if r[0][3] else ""
                    referer_2 = r[0][6] if r[0][6] else ""
                    audit_inverted = 1 - json.loads(r[1].rstrip())["normalized"]
                    simplified_comp_data = (page, url, document_url_1, document_url_2, referer_1, referer_2, audit_inverted)
                    ast_comps_for_time_period.append(simplified_comp_data)
    
    
    # sort entries
    ast_comps_for_time_period.sort()
    print(f"time period {time_period}, num comp: {len(ast_comps_for_time_period)}")
    min_values = list()
    max_values = list()
    all_uniq_comp = 0
    
    
    total_url_page_pairs = set()
    
    current_page = None
    current_url = None
    
    doc_url_ref_groups = dict()
    for r in ast_comps_for_time_period:
        page, url, document_url_1, document_url_2, referer_1, referer_2, audit_inverted = r
        total_url_page_pairs.add((page, url))
        if current_page == None:
            current_page = page
        if current_url == None:
            current_url = url
        
        if document_url_1==document_url_2 and document_url_1:
            thing_in_common = document_url_1
        elif referer_1 == referer_2 and referer_1:
            thing_in_common = referer_1
        else: 
            raise str(r)
        
        
            
        if current_page != page or current_url != url:
            #do all the change over stuff 
            for frame in doc_url_ref_groups:
                all_uniq_comp +=1
                min_values.append(min(doc_url_ref_groups[frame]))
                max_values.append(max(doc_url_ref_groups[frame]))
            
            doc_url_ref_groups = dict()
            current_page = page
            current_url = url
        
        doc_url_ref_groups[thing_in_common] = doc_url_ref_groups.get(thing_in_common, set())
        doc_url_ref_groups[thing_in_common].add(audit_inverted)
        
    
    for frame in doc_url_ref_groups:
        all_uniq_comp +=1
        min_values.append(min(doc_url_ref_groups[frame]))
        max_values.append(max(doc_url_ref_groups[frame])) 


    summary[str(time_period)]["total_url_page_pairs"] = len(total_url_page_pairs)
    summary[str(time_period)]["all_uniq_comp"] = all_uniq_comp
    summary[str(time_period)]["min_values"] = min_values
    summary[str(time_period)]["max_values"] = max_values
    print("all_uniq_comp", summary[str(time_period)]["all_uniq_comp"])
    
    with open(out_file, 'w') as outfile:
        json.dump(summary, outfile)
    
    
    # Note ("page2", "url2", "docurl1", "docurl1", "ref1", "ref1", False),
    #     ("page2", "url2", "ref1", "ref1", "ref1", "ref1", False)
    # would count as diff comparisons. i think this is reasonable