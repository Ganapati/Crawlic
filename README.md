Crawlic
=======

web crawler (find temporary files, parse robots.txt and search some folders)

Usage :
-------
### start scan :
./crawlic.py -u http://site.tld/

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

License
=======

"THE BEER-WARE LICENSE" (Revision 42):
<phk@FreeBSD.ORG> wrote this file. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp
