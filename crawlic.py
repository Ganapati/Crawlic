#!/usr/bin/env python

from lib.pholcidae import Pholcidae
import argparse
import random
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import string
import json
from urlparse import urlparse
import socket
import time
import re
import sys
import os
import commands

user_agent_list = []

"""
Crawler definition
"""


class Crawlic(Pholcidae):
    """ Base Class for crawler """

    def crawl(self, data):
        """ called every link fetched """
        url = data.url.split("?")[0].split("#")[0]
        for extension in Crawlic.extension_list:
            try:
                response = requests.get(url + extension, verify=False)
                if (response.status_code == 200 and
                        Crawlic.page_not_found_pattern not in response.text):
                    print "   [+] %s" % url + extension
            except requests.exceptions.ConnectionError as e:
                print "[!] %s : %s" % (url, e)

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

"""
Usefull methods
"""


def getPageNotFoundPattern(url):
    """ Get a pattern for 404 page (if server return 200 on 404) """
    if url[:-1] != "/":
        url = url + "/"
    pattern = ""
    rnd = random.randint(5, 30)
    rnd_string = ''.join([random.choice(string.letters) for c in xrange(0,
                                                                        rnd)])
    url = url + rnd_string
    response = requests.get(url,
                            headers={"referer": url,
                                     "User-Agent": getRandomUserAgent()},
                            verify=False)
    if "404" in response.text:
        pattern = "404"
    elif "not found" in response.text:
        pattern = "not found"
    return pattern


def getRandomUserAgent():
    """ return a random user agent from the list loaded in previous method """
    return random.choice(user_agent_list)


def printBanner(banner_file):
    """ Print a fucking awesome ascii art banner """
    banner_length = 0
    for line in [line.rstrip() for line in open(banner_file)]:
        print line
        if len(line) > banner_length:
            banner_length = len(line)

    print "\n" + "#" * banner_length + "\n"


def fetch_repos(repo_type, url, output_path):
    """ Clone remote repo in local folder"""

    crawlic_path = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(crawlic_path,
                               output_path)

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    if repo_type == "git":
        cmd = os.path.join('..', '..',
                           crawlic_path,
                           'external_tools',
                           'dvcs-ripper',
                           'rip-git.pl')
    elif repo_type == "svn":
        cmd = os.path.join('..', '..',
                           crawlic_path,
                           'external_tools',
                           'dvcs-ripper',
                           'rip-svn.pl')

    full_cmd = 'cd %s && %s -u %s' % (output_path, cmd, url)
    commands.getoutput(full_cmd)
    print "        [+] %s repo cloned into %s" % (repo_type, output_path)

"""
Recon methods
"""


def robotsExtract(url, pattern):
    """ Parse robots.txt file """
    if url[:-1] != "/":
        url = url + "/"
    url = url + "robots.txt"
    response = requests.get(url,
                            headers={"referer": url,
                                     "User-Agent": getRandomUserAgent()},
                            verify=False)
    if response.status_code != 404 and pattern not in response.text:
        for line in response.text.split("\n"):
            if (not line.strip().startswith("#") and
                    not line.strip().lower().startswith("sitemap") and
                    not line.strip().lower().startswith("user") and
                    line.strip() != ""):
                line = line.split("#")[0]
                (rule, path) = line.split(":")
                if rule.lower() == "disallow":
                    print "   [+] %s" % path


def searchFolders(url, folders_file, pattern):
    """ Search for interresting folders like /private, /admin etc... """
    if url[:-1] != "/":
        url = url + "/"

    for line in [line.strip() for line in open(folders_file)]:
        response = requests.get(url + line,
                                headers={"referer": url,
                                         "User-Agent": getRandomUserAgent()},
                                verify=False)
        if response.status_code != 404 and pattern not in response.text:
            print "   [+] /%s" % line
            if '.git' in line:
                fetch_repos('git', url + line, 'output/%s/' % url.replace('/', ''))
            elif '.svn' in line:
                fetch_repos('svn', url + line, 'output/%s/' % url.replace('/', ''))


def googleDorks(url, google_dorks):
    """ Use google dorks to retrieve informations on target """
    for google_dork in google_dorks:
        dork = google_dork % url
        google_url = 'http://ajax.googleapis.com/ajax/services/search/' \
                     'web?v=1.0&q=%s' % dork
        response = requests.get(google_url,
                                headers={"referer": "http://google.com/",
                                         "User-Agent": getRandomUserAgent()},
                                verify=False)
        parsed_response = json.loads(response.text)
        try:
            for result in parsed_response['responseData']['results']:
                print "   [+] %s" % result['url']
        except TypeError:
            # Silently pass if google dorking fail
            pass


def reverseDns(ip, query_numbers):
        page_counter = 1
        domains = []
        while page_counter < query_numbers:
            try:
                bing_url = 'http://www.bing.com/search?q=ip%3a'+str(ip)+'&go' \
                           '=&filt=all&first=' + repr(page_counter) + '&' \
                           'FORM=PERE'
                response = requests.get(bing_url,
                                        headers={"User-Agent": getRandomUserAgent()})
                names = (re.findall('\/\/\w+\.\w+\-{0,2}\w+\.\w{2,4}',
                                    response.text))
                for name in names:
                    get_ip = socket.gethostbyname_ex(name[2:])
                    if get_ip[2][0] == ip and name[2:] not in domains:
                        domains.append(name[2:])
            except:
                pass
            page_counter += 10
            time.sleep(0.5)
        return domains

"""
Scannings methods
"""


def scanRobots(url, page_not_found_pattern):
    """ Start scan using robots.txt """
    print "[*] Starting robots.txt search"
    try:
        robotsExtract(url, page_not_found_pattern)
    except KeyboardInterrupt:
        print "[!] Skip robots.txt parsing"
    except requests.exceptions.ConnectionError:
        print "[!] Connection error during robots.txt parsing"



def scanFolders(url, folders, page_not_found_pattern):
    """ Start scan using folder list """
    print "[*] Starting folder search"
    try:
        searchFolders(url, folders, page_not_found_pattern)
    except KeyboardInterrupt:
        print "[!] Skip folder search"
    except requests.exceptions.ConnectionError:
        print "[!] Connection error during folders search"


def scanTemporaryFiles(url):
    """ Start scan using temporary files extensions """
    print "[*] Starting temp file search"
    try:
        crawlic = Crawlic()
        crawlic.start()
    except KeyboardInterrupt:
        print "[!] Skip temp file search"
    except requests.exceptions.ConnectionError:
        print "[!] Connection error during temporary files search"


def scanGoogleDorks(url, google_dorks):
    """ Start scan using google dorks """
    print "[*] Starting Google dorking"
    try:
        googleDorks(url, google_dorks)
    except KeyboardInterrupt:
        print "[!] Skip Google dorking"
    except requests.exceptions.ConnectionError:
        print "[!] Connection error during google dorking"


def scanReverseDns(url):
    """ Start reverse DNS search by bing """
    print "[*] Searching domains on same server"
    try:
        ip = socket.gethostbyname(urlparse(url).netloc)
        for domain in reverseDns(ip, 50):
            print "   [+] %s" % domain
    except KeyboardInterrupt:
        print "[!] Skip reverse dns search"


"""
Entry point
"""


def main():
    path = os.path.dirname(__file__)
    printBanner(os.path.join(path, "banner.txt"))
    parser = argparse.ArgumentParser(description='Crawl website for'
                                                 'temporary files')
    parser.add_argument('-u',
                        '--url',
                        action="store",
                        dest="url",
                        required=True,
                        help='url')
    parser.add_argument('-e',
                        '--extensions',
                        action="store",
                        dest="extensions",
                        default=os.path.join(path, "lists", "extensions.lst"),
                        help='extensions')
    parser.add_argument('-d',
                        '--dorks',
                        action="store",
                        dest="dorks",
                        default=os.path.join(path, "lists", "dorks.lst"),
                        help='dorks')
    parser.add_argument('-f',
                        '--folders',
                        action="store",
                        dest="folders",
                        default=os.path.join(path, "lists", "folders.lst"),
                        help='folders')
    parser.add_argument('-a',
                        '--agent',
                        action="store",
                        dest="user_agent",
                        default=os.path.join(path, "lists", "user_agent.lst"),
                        help='user agent file')
    parser.add_argument('-g',
                        '--google',
                        action="store",
                        dest="google_dorks",
                        default=os.path.join(path, "lists", "google_dorks.lst"),
                        help='google dorks file')
    parser.add_argument('-t',
                        '--techniques',
                        action="store",
                        dest="techniques",
                        default="rtfgd",
                        help='scan techniques (r: robots.txt t: temp files,'
                             ' f: folders, g: google dorks, d: reverse dns)')
    parser.add_argument('-k',
                        '--insecure',
                        action="store_true",
                        dest="insecure",
                        help='suppress invalid certificate warnings')
    args = parser.parse_args()

    print "[*] Scan %s using techniques %s" % (args.url, args.techniques)

    if args.insecure:
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    url = urlparse(args.url)
    if not url.scheme:
        args.url = 'http://' + args.url
        url = urlparse(args.url)

    protocol, domain = url.scheme, url.netloc

    # Make sure the host is up
    print "[*] Probe host %s" % args.url
    try:
        requests.head(args.url)
    except requests.exceptions.ConnectionError:
        print '[!] Url %s not reachable or is down. Aborting' % args.url
        sys.exit(0)

    # Load configuration from files
    loadUserAgents(args.user_agent)
    Crawlic.extension_list = loadDorks(args.dorks)
    page_not_found_pattern = getPageNotFoundPattern(args.url)
    google_dorks = loadGoogleDorks(args.google_dorks)

    # Configure crawler
    Crawlic.page_not_found_pattern = page_not_found_pattern
    Crawlic.settings = {'domain': domain,
                        'start_page': '/',
                        'stay_in_domain': True,
                        'protocol': protocol + "://",
                        'valid_links': loadExtensions(args.extensions),
                        'headers': {'Referer': domain,
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
        elif technique == "d":
            scanReverseDns(args.url)
        else:
            print "[*] unknown technique : %s" % technique
    print "[*] Crawling finished"


if __name__ == "__main__":
    main()
