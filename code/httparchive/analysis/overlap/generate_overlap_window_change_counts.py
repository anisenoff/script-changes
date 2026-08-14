import json
import itertools
import os
from pathlib import Path
import psycopg2
import sys
from datetime import datetime

sys.path.append(str(Path(f"../../../global_helpers").resolve()))
from connecttodb import connect_to_db
from generate_httparchive_dates import generate_crawl_identifiers

conn = connect_to_db()
conn.autocommit = True
cursor = conn.cursor()

out_file = Path(f"../../../../data/httparchive/summary/window_overlap_change_counts_new.json").resolve()


def run_query(query, params):
    try:
        cursor.execute(query, params) 
        return cursor.fetchall()
    except psycopg2.Error as e:
        print(f"SQL query error: {e}")
        return "error"


crawl_identifiers = generate_crawl_identifiers()


if os.path.isfile(out_file):
    with open(out_file) as json_file:
        summary = json.load(json_file)
else:
    summary = dict()


for time_period in [1,3,6,12,100]:
    if str(time_period) in summary:
        print(f"time period: {time_period} completed")
        continue
    else:
        print(f"starting time period: {time_period}")
    summary[str(time_period)] = dict()
    
    valid_time_periods_query = ""
    
    for date1, date2 in list(itertools.combinations(crawl_identifiers, 2)):
        
        d1 = datetime.strptime(date1,"%Y-%m-%d")
        d2 = datetime.strptime(date2,"%Y-%m-%d")
        months_diff = (d2.year - d1.year) * 12 + (d2.month - d1.month)

        if months_diff<=time_period:
            overlap_view = f"view{date1.replace('-', '')}to{date2.replace('-', '')}"
            
            if valid_time_periods_query:
                valid_time_periods_query+= " UNION "
            valid_time_periods_query += f""" SELECT page, url, document_url_1, document_url_2, referer_1, referer_2, archive_hash_1 != archive_hash_2 AS hash_diff, {months_diff}
                                            FROM {overlap_view} """
        #break
    valid_time_periods_query += """
        ORDER BY page, url, document_url_1, document_url_2, referer_1, referer_2;
    """
    try:
        cursor.execute(valid_time_periods_query) 
        res = cursor.fetchall()
    except psycopg2.Error as e:
        print(f"SQL query error: {e}")
        res = []

    print(f"Query complete time period: {time_period}")
    
    any_change = 0
    all_uniq_comp = 0
    
    
    current_page = None
    current_url = None
    current_changes = dict()
    current_changes_list = list()
    current_counts = dict()
    current_counts_list = list()
    print(f"len of results: {len(res)}")
    doc_url_ref_groups = dict()
    
    current_timeperiods = dict()
    current_timeperiods_list = list()
    current_timeperiods_change = dict()
    current_timeperiods_change_list=list()
    for r in res:
        page, url, document_url_1, document_url_2, referer_1, referer_2, hash_is_diff, months_diff = r
        
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
          
        
        #do all the change over stuff if we have reached a new page_url combo  
        if current_page != page or current_url != url:
            #switch over current page and url
            current_page = page
            current_url = url
            
            # record how many unique scripts there were and how many changed
            for frame in doc_url_ref_groups:
                all_uniq_comp +=1
                if doc_url_ref_groups[frame]:
                    any_change+=1
            
            # reset for next url/page set
            doc_url_ref_groups = dict()
            
            #record for first instance of ne url and page
            doc_url_ref_groups[thing_in_common] = hash_is_diff
            
            
            list_of_frames = current_counts.keys()
            
            for frame in list_of_frames:
                current_counts_list.append(current_counts[frame])
            current_counts = dict()
            
            
            for frame in list_of_frames:
                current_changes_list.append(current_changes[frame])
            current_changes = dict()
            
            
            if time_period==100:
                for frame in list_of_frames:
                    current_timeperiods_list.append(list(current_timeperiods[frame]))
                current_timeperiods = dict()
                
                for frame in list_of_frames:
                    current_timeperiods_change_list.append(list(current_timeperiods_change[frame]))
                current_timeperiods_change = dict()
                
            
        
        # how many views per uniq script
        current_counts[thing_in_common] = current_changes.get(thing_in_common, 0) + 1
        
        # how many changes per uniq script
        current_changes[thing_in_common] = current_changes.get(thing_in_common, 0)  
        if hash_is_diff:
            current_changes[thing_in_common]+=1
            
        # if uniq script has changed at all
        doc_url_ref_groups[thing_in_common] = doc_url_ref_groups.get(thing_in_common, False) or hash_is_diff
        
        
        if time_period==100:
            # what time period it appeard in
            current_timeperiods[thing_in_common] = current_timeperiods.get(thing_in_common, set())  
            current_timeperiods[thing_in_common].add(months_diff)
            
            # what time period it changed in
            current_timeperiods_change[thing_in_common] = current_timeperiods_change.get(thing_in_common, set()) 
            if hash_is_diff: 
                current_timeperiods_change[thing_in_common].add(months_diff)
                
    
    for frame in doc_url_ref_groups:
        all_uniq_comp +=1
        if doc_url_ref_groups[frame]:
           any_change +=1   

    for frame in list_of_frames:
        current_counts_list.append(current_counts[frame])
            
    for frame in list_of_frames:
        current_changes_list.append(current_changes[frame])

    

    summary[str(time_period)]["len_query"] = len(res)
    summary[str(time_period)]["all_uniq_comp"] = all_uniq_comp
    summary[str(time_period)]["any_change"] = any_change
    summary[str(time_period)]["num_changes_per_script"] = current_changes_list
    summary[str(time_period)]["num_event_per_script"] = current_counts_list
    
    if time_period==100:

        for frame in list_of_frames:
            current_timeperiods_list.append(list(current_timeperiods[frame]))
        for frame in list_of_frames:
            current_timeperiods_change_list.append(list(current_timeperiods_change[frame]))

        summary[str(time_period)]["current_timeperiods"] = current_timeperiods_list
        summary[str(time_period)]["current_timeperiods_change"] = current_timeperiods_change_list
        

    #print(summary[str(time_period)])
    
    with open(out_file, 'w') as outfile:
        json.dump(summary, outfile)
    
    
    # Note ("page2", "url2", "docurl1", "docurl1", "ref1", "ref1", False),
    #     ("page2", "url2", "ref1", "ref1", "ref1", "ref1", False)
    # would count as diff comparisons. i think this is reasonable