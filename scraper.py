import re
from urllib.parse import urlparse
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# only crawl the following URLS and paths (valid domains)
VALID_DOMAINS = [".ics.uci.edu", ".cs.uci.edu", ".informatics.uci.edu", ".stat.uci.edu"]

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    try:
        soup = BeautifulSoup(resp.raw_response.content, features="lxml") # raw_response.content gives you the webpage html content, pass additional argument of parser specified to lxml
        links = set() # create empty set to store UNIQUE URLs found on page
        
        # urlparse breaks down URL into its compoentns (scheme, netloc, path, query, etc.)
        base_url = urlparse(url).scheme + "://" + urlparse(url).netloc # netloc aka authority

        for anchor in soup.find_all("a", href=True): # find all anchor tags <a> that define href attributes (hyperlinks)
            # transform relative to absolute URLs
            absolute_url = urljoin(base_url, anchor["href"].strip()) # constructs full url by joining base w/ whatever hyperlinks are found on page
            links.add(absolute_url)

        return list(links) # converts set (uniqueness) to list (return value)
    
    except Exception as e:
        print(f"Error parsing {url}: {e}") # parsing fails
        return [] # returns empty list
    # return list()

def defragment(url): # preserves the original url w/o fragment
    parsed = urlparse(url)
    return parsed.scheme + "://" + parsed.netloc + parsed.path + ("?" + parsed.query if parsed.query else"")

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        
        # defragment URL (removing the fragment part)
        url = defragment(url)
        parsed = urlparse(url)

        # only vaid if scheme is http or https
        if parsed.scheme not in set(["http", "https"]):
            return False
        
        # only valid if domain is in VALID_DOMAINS
        # parse.netloc.lower() returns the domain and port
        domain = parsed.netloc.lower()
        if not any(re.search(valid_domain, domain) for valid_domain in VALID_DOMAINS):
            return False
        
        # not valid if url does not point to a webpage
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise

