
import gzip
import io
import multiprocessing
import networkx
import os
from pathlib import Path
from packaging.version import parse, Version
import re
import sys
from datetime import datetime

sys.path.append(str((Path(__file__).resolve().parent/'pagegraph-query' / 'src').resolve()))

from pagegraph.types import  Url, ResourceType, PageGraphInput
from pagegraph.graph import PageGraph
from pagegraph.versions import Feature, min_version_for_feature
    

#all modified from pagegraph-query/src/pagegraph/graphml.py

def pagegraph_version_from_graphml_file_compressed(input_path: Path) -> Version:
    pattern = r"<version>(\d+\.\d+\.\d+)<\/version>"

    graph_version = None

    with gzip.open(input_path, 'rb') as gzipped_file:
        with io.TextIOWrapper(gzipped_file, encoding='utf-8') as f:
            for line in f:
                match = re.search(pattern, line, re.ASCII)
                if match:
                    graph_version = parse(match.group(1))
                    break

    if not graph_version:
        raise ValueError("Unable to determine version of PageGraph file at.")
    return graph_version

def url_from_graphml_file_compressed(input_path: Path) -> Url:
    xml_url_pattern = r'<desc>.*?<url>(.*?)</url>.*?</desc>'
    xml_url_matcher = re.compile(xml_url_pattern, flags=re.U)

    xml_empty_url_pattern = r'<desc>.*?<url/>.*?</desc>'
    xml_empty_url_matcher = re.compile(xml_empty_url_pattern, flags=re.U)
    
    with gzip.open(input_path, 'rb') as gzipped_file:
        with io.TextIOWrapper(gzipped_file, encoding='utf-8') as f:
            for line in f:
                if with_url_match := xml_url_matcher.search(line):
                    return with_url_match.group(1)
                # If we couldn't find a proper URL in the PageGraph file,
                # see if we instead have a closed <url/> tag, which would indicate
                # that the graph was recorded correctly, but the top level frame's
                # URL was empty (this shouldn't happen, but may be present in
                # v0.7.x versions of PageGraph files).
                if xml_empty_url_matcher.search(line) is not None:
                    return ""
    raise ValueError("Could not find <url>...</url> in graph file")
  
  
def date_from_graphml_file_compressed(input_path: Path) -> Url:
    date_pattern = r"<date>(\d+\.\d+)<\/date>"
    date_matcher = re.compile(date_pattern)
    
    with gzip.open(input_path, 'rb') as gzipped_file:
        with io.TextIOWrapper(gzipped_file, encoding='utf-8') as f:
            for line in f:
                if match := date_matcher.search(line):
                    # The <date> in the pagegraph recording is in milliseconds
                    date = datetime.fromtimestamp(float(match.group(1)))
                    return date
    raise ValueError(f"Unable to find 'date' in file: {input_path}")
  

  
    
def load_from_path_compressed(input_path) -> PageGraphInput:
    """Loads a networkx instance from a graphml file.

    This indirection step exists as a chance to do preprocess and modify
    networkx instances before they're consumed by the PageGraph class."""
    
    try:
        version = pagegraph_version_from_graphml_file_compressed(input_path)
    except:
        version = None
    try:
        url = url_from_graphml_file_compressed(input_path)
    except:
        url = ""
    try:    
        date = date_from_graphml_file_compressed(input_path)
    except:
        date = None
    
        
    try:
        if not url:
            print(f"Could not find 'url' in file: {input_path}")
            #raise ValueError(f"Could not find 'url' in file: {input_path}")
        if not version:
            print(f"Unable to find 'version' in file: {input_path}")
            #raise ValueError(f"Unable to find 'version' in file: {input_path}")
        if not date and min_version_for_feature(Feature.GRAPH_TIMESTAMP) < version:
            print(f"Unable to find 'date' in file: {input_path}")
            #raise ValueError(f"Unable to find 'date' in file: {input_path}")
        
        
        
        graph = networkx.read_graphml(input_path)
        # processed_graph = remove_intermediate_subgraphs(graph)
        reverse_graph = networkx.reverse_view(graph)
        return PageGraphInput(url, version, date = date, graph = graph, reverse_graph=reverse_graph)
    except ValueError as exc:
        print(exc)
        raise ValueError(
            f"Unable to parse PageGraph file at {input_path}") from exc
 