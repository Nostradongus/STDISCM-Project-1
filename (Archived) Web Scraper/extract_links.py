"""
STDISCM Parallel Programming Project

Web Scraper

Group 2
- Andre Dominic Ponce
- Joshue Salvador Jadie 

Website scraped: https://www.dlsu.edu.ph
"""

import requests
from urllib.request import urlparse, urljoin
from bs4 import BeautifulSoup

# global variables
URL = 'https://www.dlsu.edu.ph'                                       # the url to extract links on
total_urls_visited = 0                                                # total number of urls already visited
all_urls = set()                                                      # set of all unique internal urls; urls of the same website
match = 'www.dlsu'                                                    # specific substring the url has to match on to be included in the set
not_match = ['pdf', 'doc', 'xls', 'rtf', 'jpg', 'mp3', 'jpeg', 'png'] # specific substring that the url should not have

"""
Checks whether `url` is a valid URL or not. Makes sure that `url` has a proper scheme or protocol (e.g. `http` or `https`) and if `match`
is found in the url. Additionally, `not_match` should also not be included in the url for it to be valid
"""
def is_valid(url):
    # extract components from url
    url_parsed = urlparse(url)
    
    for i in not_match:
        if i in url_parsed.path:
            return False
    
    # check if `match` is found in domain name of url, `not_match` is not found in domain name of url, and if protocol of url is http or https
    return match in url_parsed.netloc and (url_parsed.scheme == 'http' or url_parsed.scheme == 'https')

"""
Returns all internal (same website) URLs that is found on web page linked by 'url'
"""
def get_all_urls(url):
    # set of all URLs in `url`
    urls = set()
    
    # parse URL to get specific components
    url_parsed = urlparse(url)
    print(url) 
    
    if (url_parsed.scheme == 'http' or url_parsed.scheme == 'https'):
        # get HTML content of the web page linked by url as a soup object for parsing
        soup = BeautifulSoup(requests.get(url).content, "html.parser", from_encoding="iso-8859-1")
        
        # get all anchor (<a>) tags and their links from the web page's HTML content
        for a in soup.findAll("a"):
            href = a.attrs.get("href")
            if href != "" or href is not None:
                """
                Join the URL if it is relative (not absolute link)
                
                since link values in some hrefs are not absolute (e.g. /colleges only not https://www.dlsu.edu.ph/colleges)
                """
                href = urljoin(url, href)
                
                # remove `HTTP GET` parameters from the URLs to avoid redundancy in the set of urls
                href_parsed = urlparse(href)
                href = href_parsed.scheme + "://" + href_parsed.netloc + href_parsed.path
                
                # check if url is not valid and if url does not exist yet in the set of all urls
                if is_valid(href) and not href in all_urls:
                    urls.add(href)
                    all_urls.add(href)
                
    # return the urls of the web page
    return urls

"""
Extracts all links from a web page and it's following web pages (recursive).
"""  
def extract_links(url, max_urls=250):
    global total_urls_visited
    
    # current url already visited
    total_urls_visited += 1
    
    # extract all urls from the url's web page
    urls = get_all_urls(url)
    for url in urls:
        # maximum number of urls visited was already reached, stop extraction
        if total_urls_visited > max_urls:
            break;
        # continue url extraction on the next web page
        extract_links(url, max_urls=max_urls)
        
# main function
if __name__ == "__main__":
    # extract all links from `URL`
    extract_links(URL)
    
    # display total number of urls visited and extracted
    print(f'Total number of urls collected: {len(all_urls)}')
    
    # display the urls
    print(all_urls)
    
    # save all collected links to a text file
    with open('dlsu_links.txt', 'w') as f:
        for url in all_urls:
            f.write(f"{url}\n")