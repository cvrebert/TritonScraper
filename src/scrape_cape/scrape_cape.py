from contextlib import closing
from time import sleep
from urlparse import urljoin
from urllib import urlencode
from urllib2 import urlopen, Request

from lxml import etree

RELATIVE_PREFIX = "descendant-or-self::node()"

CAPE_SEARCH_URL = "http://www.cape.ucsd.edu/stats.html"

USER_AGENT = "Mozilla/5.0 (Windows NT 5.1; U; en-US; rv:1.9.2) Gecko/20100115 Firefox/3.6"

SOCKET_TIMEOUT = 30
RETRY_DELAY = 30

# HTTP_METHOD = 'method'
# HTTP_GET = 'get'
ACTION = 'action'
VALUE = 'value'
NAME = 'name'

search_forms = etree.XPath(RELATIVE_PREFIX+"/form[@name='searchQuery']")
select_elements = etree.XPath(RELATIVE_PREFIX+"/select")
option_elements = etree.XPath(RELATIVE_PREFIX+"/option")

def url2tree(url):
    req = Request(url)
    req.add_header('User-agent', USER_AGENT)
    while True:
        try:
            with closing(urlopen(req, None, SOCKET_TIMEOUT)) as f:
                parser = etree.HTMLParser()
                tree = etree.parse(f, parser)
                # real_url = f.geturl()
        except IOError:
            try:
                description = "%s: %s" % (type(ioe.reason), list(ioe.reason))
            except (AttributeError, TypeError):
                description = str(ioe)
            print "Encountered IOError:", description, "; Waiting & retrying..."
            sleep(RETRY_DELAY)
        else:
            return tree#, real_url

class CapeBrowser(object):
    def __init__(self):
        pass
    
    @property
    def _submit_url(self):
    
    @property
    def subjects(self):
    
    def capes_for(self, subject):

tree = url2tree(CAPE_SEARCH_URL)
form = search_forms(tree)[0]
select = select_elements(form)[0]
field_name = select.get(NAME)
# method = form.get(HTTP_METHOD)
# if method != HTTP_GET:
    # raise ValueError("Expected GET form submission method; Got "+repr(method))
action = form.get(ACTION)
dest_url = urljoin(CAPE_SEARCH_URL, action)
print dest_url
for opt in option_elements(select):
    val = opt.get(VALUE)
    if not val: continue
    code, name = opt.text.split(" - ")
    print [val, code, name]
print "%s?%s" % (dest_url, urlencode({field_name:val}))
# <form name="searchQuery" method="get" action="scripts/statistics.asp">
