import re
from urllib.parse import urlparse
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from collections import Counter # for question 3
import os # reads in stop_words.txt for question 3

# only crawl the following URLS and paths (valid domains)
VALID_DOMAINS = [".ics.uci.edu", ".cs.uci.edu", ".informatics.uci.edu", ".stat.uci.edu"]

# question 1: how many unique pages did you find? (discarding the fragment part)
unique_pages = set()
# question 2: longest_page is a map (link, word count) of the link with the highest word count
longest_page = (None, 0)
#question 3: what are the 50 most common words in entire set of pages crawled under these domains?
word_counter = Counter() 
STOP_WORDS = stop_word_file('stop_words.txt')

def scraper(url, resp):
    links = extract_next_links(url, resp)

    valid_links = [] # initialize empty list to store urls that will be added to the frontier
    for link in links:
        if is_valid(link):
            unique_pages.add(defragment(link)) # add unique pages to set
            valid_links.append(link) # add all links (including the ones within each page) to list

            # count words for each url
            curr_count = count_words(resp.raw_response.content)
            # if the current count of url is greater than highest word count, update longest_page
            if curr_count > longest_page[1]:
                longest_page = (link, curr_count)


    return valid_links

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

        # defragment URL (removing the fragment part)
        url = defragment(url)
        
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

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
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


def defragment(url): # preserves the original url w/o fragment
    parsed = urlparse(url)
    return parsed.scheme + "://" + parsed.netloc + parsed.path + ("?" + parsed.query if parsed.query else"")

def count_words(url_content): # question 2
    soup = BeautifulSoup(url_content, features="lxml")
    # excludes html markup because html markup does not count as words
    content = soup.get_text()
    # use regular expression to count alphanumeric words and words with special characters
    words = re.findall(r"\b[\w'-]+\b", content.lower())
    fifty_common(words)
    return len(words)

def fifty_common(words): # question 3 (void function)
    not_stop_word = [] # initialize list to store remaining words after filtering out stop words
    for word in words:
        if word not in STOP_WORDS:
            not_stop_word.append(word)

    word_counter.update(not_stop_word) # word count should be smaller now without the stop words

def stop_word_file(filename):
    with open(filename, 'r') as file: # read in English stop words into a file
        stop_words_list = (line.strip() for line in file.readlines())
    return stop_words_list