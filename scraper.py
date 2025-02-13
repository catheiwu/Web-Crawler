import re
import simhash # for near duplicate detection
from urllib.parse import urlparse
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from collections import Counter # for question 3
from collections import defaultdict 
import os # reads in stop_words.txt for question 3

# only crawl the following URLS and paths (valid domains)
VALID_DOMAINS = [".ics.uci.edu", ".cs.uci.edu", ".informatics.uci.edu", ".stat.uci.edu"]

# question 1: how many unique pages did you find? (discarding the fragment part)
unique_pages = set()
# question 2: longest_page is a map (link, word count) of the link with the highest word count
longest_page = (None, 0)
# question 3: what are the 50 most common words in entire set of pages crawled under these domains?
word_counter = Counter() 
# question 4: mapping subdomains in the ics.uci.edu domain to number of pages
subdomain_count = {}
# global variable to keep track of the checksums of pages crawled
seen_checksums = set()
# global variable to keep track of the simhash fingerprints of pages crawled
seen_simhash = set()

def stop_word_file(filename):
    with open(filename, 'r') as file: # read in English stop words into a file
        stop_words_list = (line.strip() for line in file.readlines())
    return stop_words_list

STOP_WORDS = stop_word_file('stop_words.txt')

def scraper(url, resp):

    # only scrape from links with status = 200
    if resp.status != 200 or resp.raw_response is None:
        return []
    
    # checksum is sum of bytes in the document file (from lecture notes)
    # note that some documents that are not exact can have same sum of bytes
    curr_checksum = sum(resp.raw_response.content)

    # if exact duplicate, then do not scrape url
    if curr_checksum in seen_checksums:
        return []

    # compute simhash of the url's content (resp.raw_response.content)
    curr_simhash = compute_simhash(resp.raw_response.content)
    
    # if curr_simhash is a near duplicate, then do not scrape
    # if not a near duplicate, add it to set of seen_simhash
    if near_duplicate(curr_simhash):
        return []
    else:
        seen_simhash.add(curr_simhash)

    global longest_page

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
                
            # for the link, count it as a unique page if it is a subdomain in ics.uci.edu
            count_subdomain_pages(link)

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
        if resp.status != 200:
            return []

        soup = BeautifulSoup(resp.raw_response.content, features="lxml") # raw_response.content gives you the webpage html content, pass additional argument of parser specified to lxml
        links = set() # create empty set to store UNIQUE URLs found on page

        # defragment URL (removing the fragment part)
        url = defragment(url)
        
        # urlparse breaks down URL into its compoentns (scheme, netloc, path, query, etc.)
        base_url = urlparse(url).scheme + "://" + urlparse(url).netloc # netloc aka authority

        path_counts =  defaultdict(int) # create map to store the key: path and the value: count
        absolute_urls = set() # create empty set of absolute urls

        for anchor in soup.find_all("a", href=True): # find all anchor tags <a> that define href attributes (hyperlinks)
            # transform relative to absolute URLs
            absolute_url = urljoin(base_url, anchor["href"].strip()) # constructs full url by joining base w/ whatever hyperlinks are found on page
            # defragment the absolute_url
            absolute_url = defragment(absolute_url)
            
            # keep track of how many absolute_urls there are with a path that is extracted less than 20 times
            path = urlparse(absolute_url).netloc
            path_counts[path] += 1
            # if the url has a path that is the same as less than 20 other urls, add it to absolute_urls
            if path_counts[path] <= 20:
                absolute_urls.add(absolute_url)

        # only extract links that does not have paths similar to 20 other links
        for link in absolute_urls:
            if path_counts[urlparse(link).netloc] <= 20:
                links.add(link)

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
        
        # Reject if the subdomain is in this set
        if domain in set(["grape.ics.uci.edu", "sli.ics.uci.edu", "wiki.ics.uci.edu", "swiki.ics.uci.edu"]):
            return False
        
        # not valid if url does not point to a webpage
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico|pdf|zip"
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

def count_subdomain_pages(link):
    parsed = urlparse(link)
    if "ics.uci.edu" in parsed.netloc:
        subdomain = parsed.scheme + "://" + parsed.netloc
        if subdomain in subdomain_count:
            subdomain_count[subdomain] += 1
        else:
            subdomain_count[subdomain] = 1

def compute_simhash(content):
    soup = BeautifulSoup(content, features="lxml")
    content = soup.get_text()
    # use regular expression to count alphanumeric words and words with special characters
    words = re.findall(r"\b[\w'-]+\b", content.lower())
    return (simhash.Simhash(words)).value

def similarity(curr_simhash, compare_simhash, bit_length=64):
    # apply xor operation = 1's is number of different bits
    # negate = 0's is number of same bits
    new_xor = curr_simhash ^ compare_simhash

    # how many bits that are 0 in new_xor = intersection of bits
    num_zeroes = bin(new_xor).count('0') - 1
    # return similarity
    return num_zeroes / bit_length

def near_duplicate(curr_simhash, threshold = 0.90):
    # compare with all seen_simhash set
    for compare_simhash in seen_simhash:
        # similarity = fraction of bits that are the same over all n bits of representation
        if similarity(curr_simhash, compare_simhash) >= threshold:
            return True
    return False
    
def write_report():
    with open('report.txt', 'w') as report_file:

        # Question 1: how many unique pages did you find? (as established by the URL, discarding the fragment part)
        report_file.write(f"Question 1: {len(unique_pages)} unique pages found\n\n")

        # Question 2: What is the longest page in terms of the number of words?
        report_file.write(f"Question 2: The longest page was {longest_page[0]} with {longest_page[1]} words\n\n")

        # Question 3: 50 most common words in the entire set of pages crawled under these domains
        report_file.write("Question 3: 50 most common words crawled under these domains\n")
        common_words = word_counter.most_common(50)
        for word, count in common_words:
            report_file.write(f"{word}: {count}\n")
        report_file.write("\n")

        # Question 4: Subdomains found in the ics.uci.edu domain
        report_file.write("Question 4: Subdomains found in the ics.uci.edu domain\n")
        for subdomain, count in sorted(subdomain_count.items()):
            report_file.write(f"{subdomain}, {count}\n")