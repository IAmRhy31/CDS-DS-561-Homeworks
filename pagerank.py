from bs4 import BeautifulSoup
import numpy as np
import urllib.request
import re
from google.oauth2 import service_account
from google.cloud import storage

credentials = service_account.Credentials.from_service_account_file("ds-561-project-1-fa357d14ef90.json")
storage_client = storage.Client(project="ds-561-project-1", credentials=credentials)
                
def calculate_pagerank(graph_outlinks, graph_inlinks, pagerank_values):

    pagerank_difference = 1.0
    iteration_count = 0
    
    while pagerank_difference > 0.5:
        previous_pagerank_sum = sum(pagerank_values)
        
        for page_index in range(10000):
            new_pagerank = 0.0
            
            for inlink in graph_inlinks[page_index]:
                new_pagerank += pagerank_values[inlink] / len(graph_outlinks[inlink])

            pagerank_values[page_index] = 0.15 + 0.85 * (new_pagerank)

        current_pagerank_sum = sum(pagerank_values)
        pagerank_difference = (abs(previous_pagerank_sum - current_pagerank_sum) / previous_pagerank_sum) * 100
        iteration_count = iteration_count + 1

    pagerank_values.sort()
    return pagerank_values

def main():

    print("PageRank Program: ")

    dir = "./generated-content/"

    graph_outlinks = [[] for _ in range(10000)]
    graph_inlinks = [[] for _ in range(10000)]
    pagerank_values = [1.0] * 10000
    page_stats = [[0, 0] for _ in range(10000)]

    for page_id in range(10000):
        filename = str(page_id) + ".html"
        file_dir = dir + filename

        with open(file_dir, 'r', encoding="utf-8") as file:
            page_index = int(filename[:-5])
            html_content = file
            soup = BeautifulSoup(html_content, "html.parser")

            for link in soup.findAll('a'):
                href = link.get('href')
                linked_page_index = int(href[:-5])

                graph_outlinks[page_index].append(linked_page_index)
                graph_inlinks[linked_page_index].append(page_index)
                page_stats[page_index][1] += 1 #out
                page_stats[linked_page_index][0] += 1 #in

                print(href)
                print(page_id)


    print(calculate_pagerank(graph_outlinks, graph_inlinks, pagerank_values))

    sorted_pages_by_pagerank = sorted(enumerate(pagerank_values), key=lambda x: x[1], reverse=True)

    print("Top 5 Pages by PageRank Score:")
    for i, (page_index, score) in enumerate(sorted_pages_by_pagerank[:5], start=1):
        print(f"{i}. Page {page_index}: PageRank Score = {score}")
    
    # Calculate metrics for incoming links
    incoming_links_counts = [stats[0] for stats in page_stats]
    incoming_avg = np.mean(incoming_links_counts)
    incoming_median = np.median(incoming_links_counts)
    incoming_max = max(incoming_links_counts)
    incoming_min = min(incoming_links_counts)
    incoming_quintiles = np.percentile(incoming_links_counts, [20, 40, 60, 80])

    # Calculate metrics for outgoing links
    outgoing_links_counts = [stats[1] for stats in page_stats]
    outgoing_avg = np.mean(outgoing_links_counts)
    outgoing_median = np.median(outgoing_links_counts)
    outgoing_max = max(outgoing_links_counts)
    outgoing_min = min(outgoing_links_counts)
    outgoing_quintiles = np.percentile(outgoing_links_counts, [20, 40, 60, 80])

    print("Incoming Links Statistics:")
    print(f"Average: {incoming_avg}")
    print(f"Median: {incoming_median}")
    print(f"Max: {incoming_max}")
    print(f"Min: {incoming_min}")
    print(f"Quintiles: {incoming_quintiles}")

    print("Outgoing Links Statistics:")
    print(f"Average: {outgoing_avg}")
    print(f"Median: {outgoing_median}")
    print(f"Max: {outgoing_max}")
    print(f"Min: {outgoing_min}")
    print(f"Quintiles: {outgoing_quintiles}")

if __name__ == "__main__":
    main()