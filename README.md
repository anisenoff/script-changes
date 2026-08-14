# script-changes

These instructions assume that you have Python, python virtual environments, and nvm installed on your machine.

## Initial Set Up
1) Clone the repo 
* Use the --recurse-submodules flag to ensure that all nested repositories are installed

2) Create all tables as described in the DatabaseSchema.md file
* the scripts assume that these tables exist in a psql database named downstream

3) Create main virtual environment in base dir of folder
* create a python 3.12.3 virtual environment with the requirements.txt file in the root folder
* activate that virtual environment





## HTTP Archive

* replace BIGQUERY_PROJECT value in global_helpers/constants.py with big query project name
* set up google big query credentials and run ```export GOOGLE_APPLICATION_CREDENTIALS="[path/to/credentials]"```
* activate the virtual environment

* Get info from big query
    * run python3 pull_rq_bigdb_for_postgress.py
    * run python3 pull_script_bigdb_for_postgress.py
* Get info from big query files to postgress
    * run python3 rq_file_to_postgress.py
    * run python3 script_file_to_postgress.py

Note: if you run into issues with the dependencies try running the following code but replace pandas withe the library that is causing issues ```pip install google-cloud-bigquery[pandas]```


### general analysis


* run python3 make_materialized_views.py
* run python3 generate_overlap_summary.py
* run python3 generate_overlap_window_change_counts.py
* run python3 other_db_searches.py

* run overlap_plotting.ipynb
* run summary_stats.ipynb

### sat analysis

* create a python 3.14 virtual environment using the requirements in the /code/httparchive/analysis/ast/requirements.txt file and activate that 
* in this virtual enviormnent run ```nvm install 22``` and then  ```nvm use 22``` 