
def generate_crawl_identifiers():
    crawl_identifiers = []
    for month in range(11,13):
        crawl_identifiers.append(f"2024-{month}-1")
    for month in range(1,13):
        crawl_identifiers.append(f"2025-{month}-1")
    for month in range(1,7):
        crawl_identifiers.append(f"2026-{month}-1")
    crawl_identifiers.sort(key = lambda date: [int(x) for x in date.split("-")])
    return crawl_identifiers