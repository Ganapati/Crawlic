Crawlic
=======

web crawler (find temporary files, parse robots.txt and search some folders)

Usage :
-------
### start scan :
./crawlic.py -u http://site.tld/ -t rtf

-t : techniques to use for scanning (default rtfg):
    - r : robots.txt
    - t : temporary files (~, .bak, etc)
    - f : folders
    - g : google dorks

### Output :

    [*] Starting robots.txt search on http://site.tld
       [!]  /hidden_file.php
    [*] Starting folder search on http://site.tld
       [!] http://site.tld/admin/
       [!] http://site.tld/private/
    [*] Starting temp file search on http://site.tld
       [!] http://site.tld/index.php~
    [*] Crawling finished

Configuration :
---------------

### Change user-agent :

Edit user_agent.lst, one user agent per line

### Change folders to find :

Edit folders.lst, one directory per line

### Change files to scan :

Edit extensions.lst, one file extension per line

### Change dorks list :

Edit dorks.lst, one dork per line

### Change google dorks list :

Edit google_dorks, one dork per line, use %s as target url

License
=======

"THE BEER-WARE LICENSE" (Revision 42):
Ganapati wrote this file. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return.
