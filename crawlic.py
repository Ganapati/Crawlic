#!/usr/bin/python

from pholcidae import Pholcidae
import argparse
import random
import requests
import itertools
import string
import json

user_agent_list = []

class Crawlic(Pholcidae):
    """ Base Class for crawler """

    def crawl(self, data):
        """ called every link fetched """
        url = data.url.split("?")[0].split("#")[0]
        for extension in Crawlic.extension_list:
            response = requests.get(url + extension, verify=False)
            if response.status_code == 200 and Crawlic.page_not_found_pattern not in response.text:
                print "   [!] %s" % url + extension

def getPageNotFoundPattern(url):
    """ Get a pattern for 404 page (if server return 200 on 404) """
    if url[:-1] != "/":
        url = url + "/"
    pattern = ""
    random_string = ''.join([random.choice(string.letters) for c in xrange(0, random.randint(5,30))])
    url = url + random_string
    response = requests.get(url, headers={"referer" : url, "User-Agent" : getRandomUserAgent()}, verify=False)
    if "404" in response.text:
        pattern = "404"
    elif "not found" in response.text:
        pattern = "not found"
    return pattern

def robotsExtract(url, pattern):
    """ Parse robots.txt file """
    if url[:-1] != "/":
        url = url + "/"
    url = url + "robots.txt"
    response = requests.get(url, headers={"referer" : url, "User-Agent" : getRandomUserAgent()}, verify=False)
    if response.status_code == 200 and pattern not in response.text:
        for line in response.text.split("\n"):
            if not line.strip().startswith("#") and not line.strip().lower().startswith("sitemap") and not line.strip().lower().startswith("user") and line.strip() != "":
                line = line.split("#")[0]
                (rule, path) = line.split(":")
                if rule.lower() == "disallow":
                    print "   [!] %s" % path

def printBanner(banner_file):
    """ Print a fucking awesome ascii art banner """
    banner_length = 0
    for line in [line.rstrip() for line in open(banner_file)]:
        print line
        if len(line) > banner_length:
            banner_length = len(line)

    print "\n" + "#" * banner_length + "\n"

"""
Load configuration files
"""

def loadDorks(dorks_file):
    """ Load dorks from dorks file """
    dorks_list = []
    for line in [line.strip() for line in open(dorks_file)]:
        dorks_list.append(line)
    return dorks_list

def loadExtensions(extensions_file):
    """ Load extensions from extensions file """
    extensions_list = []
    for line in [line.strip() for line in open(extensions_file)]:
        extensions_list.append("(.*)%s" % line)
    return extensions_list

def loadUserAgents(user_agent_file):
    """ Load user agents from user_agent file """
    for line in [line.strip() for line in open(user_agent_file)]:
        user_agent_list.append(line)

def loadGoogleDorks(google_dorks_file):
    """ Load google dorks from google_dorks_file """
    google_dorks_list = []
    for line in [line.strip() for line in open(google_dorks_file)]:
        google_dorks_list.append(line)
    return google_dorks_list

def getRandomUserAgent():
    """ return a random user agent from the list loaded in previous method """
    return random.choice(user_agent_list)

def searchFolders(url, folders_file, pattern):
    """ Search for interresting folders like /private, /admin etc... """
    if url[:-1] != "/":
        url = url + "/"

    for line in [line.strip() for line in open(folders_file)]:
        response = requests.get(url + line, headers={"referer" : url, "User-Agent" : getRandomUserAgent()}, verify=False)
        if response.status_code == 200 and pattern not in response.text:
            print "   [!] /%s" % line

def googleDorks(url, google_dorks):
    for google_dork in google_dorks:
        dork = google_dork % url
        google_url = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&q=%s' % dork
        response = requests.get(google_url, headers={"referer" : "http://google.com/", "User-Agent" : getRandomUserAgent()}, verify=False)
        parsed_response = json.loads(response.text)
        for result in parsed_response['responseData']['results']:
            print "   [!] %s" % result['url']

"""
Scannings methods
"""

def scanRobots(url, page_not_found_pattern):
    print "[*] Starting robots.txt search"
    try:
        robotsExtract(url, page_not_found_pattern)
    except KeyboardInterrupt:
        print "[*] Skip robots.txt parsing"

def scanFolders(url, folders, page_not_found_pattern):
    print "[*] Starting folder search"
    try:
        searchFolders(url, folders, page_not_found_pattern)
    except KeyboardInterrupt:
        print "[*] Skip folder search"

def scanTemporaryFiles(url):
    print "[*] Starting temp file search"
    try:
        crawlic = Crawlic()
        crawlic.start()
    except KeyboardInterrupt:
        print "[*] Skip temp file search"

def scanGoogleDorks(url, google_dorks):
    print "[*] Starting Google dorking"
    try:
        googleDorks(url, google_dorks)
    except KeyboardInterrupt:
        print "[*] Skip Google dorking"

if __name__ == "__main__":

    printBanner("./banner.txt")
    parser = argparse.ArgumentParser(description='Crawl website for temporary files')
    parser.add_argument('-u', '--url', action="store", dest="url", required=True, help='url')
    parser.add_argument('-e', '--extensions', action="store", dest="extensions", default="extensions.lst", help='extensions')
    parser.add_argument('-d', '--dorks', action="store", dest="dorks", default="dorks.lst", help='dorks')
    parser.add_argument('-f', '--folders', action="store", dest="folders", default="folders.lst", help='folders')
    parser.add_argument('-a', '--agent', action="store", dest="user_agent", default="user_agent.lst", help='user agent file')
    parser.add_argument('-g', '--google', action="store", dest="google_dorks", default="google_dorks.lst", help='google dorks file')
    parser.add_argument('-t', '--techniques', action="store", dest="techniques", default="rtfg", help='scan techniques (r: robots.txt t: temp files, f: folders, g: google dorks)')
    args = parser.parse_args()

    print "[*] Scan %s using techniques %s" % (args.url, args.techniques)

    (protocol, domain) = args.url.split("://")

    # Load configuration from files
    loadUserAgents(args.user_agent)
    Crawlic.extension_list = loadDorks(args.dorks)
    page_not_found_pattern = getPageNotFoundPattern(args.url)
    google_dorks = loadGoogleDorks(args.google_dorks)

    # Configure crawler
    Crawlic.page_not_found_pattern = page_not_found_pattern
    Crawlic.settings = {
            'domain': domain,
            'start_page': '/',
            'stay_in_domain' : True,
            'protocol': protocol + "://",
            'valid_links': loadExtensions(args.extensions),
            'headers' : {
                'Referer': domain,
                'User-Agent': getRandomUserAgent()
                }
            }

    # Start recon here
    for technique in args.techniques:
        if technique == "r":
            scanRobots(args.url, page_not_found_pattern)
        elif technique == "f":
            scanFolders(args.url, args.folders, page_not_found_pattern)
        elif technique == "t":
            scanTemporaryFiles(args.url)
        elif technique == "g":
            scanGoogleDorks(args.url, google_dorks)
        else :
            print "[*] unknown technique : %s" % technique
    print "[*] Crawling finished"
