# Copyright (c) 2010 Christopher Rebert <code@rebertia.com>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from contextlib import closing
import errno
from socket import error as SocketError
from time import sleep
from cStringIO import StringIO
import re
from cookielib import CookieJar
from urllib import urlencode
from urllib2 import build_opener, HTTPCookieProcessor, Request, URLError
from httplib import BadStatusLine
from logging import getLogger

from lxml import etree

from triton_scraper import config
from triton_scraper.util import LOGGER

### HTML parsing utility functions

BR_TAGS = re.compile("<br>", re.IGNORECASE)
def without_brs(html):
    """Remove <br> tags, which merely complicate our scraping."""
    return BR_TAGS.sub(' ', html)

def parse_html(filelike, hack_around_broken_html=False):
    parser = etree.HTMLParser()
    html = without_brs(filelike.read())
    if hack_around_broken_html:# HACK: Damn you, TritonLink! You made lxml barf.
        html = html.replace('question.gif"', 'question.gif">').replace("')\";", "');\"")
    # print "="*40
    # from BeautifulSoup import BeautifulSoup
    # print BeautifulSoup(StringIO(html)).prettify()
    return etree.parse(StringIO(html), parser)

# url_count = 0
def make_tree4url():
    opener = build_opener(HTTPCookieProcessor(CookieJar()))
    def tree4url(url, post_args=None, hack_around_broken_html=False):
        global url_count
        req = Request(url)
        req.add_header('User-agent', config.USER_AGENT)
        data = urlencode(post_args, doseq=True) if post_args is not None else None
        LOGGER.debug("Browsing URL %s with POST data %s", url, post_args)
        while True:
            try:
                with closing(opener.open(req, data, config.SOCKET_TIMEOUT)) as f:
                    tree = parse_html(f, hack_around_broken_html)
                    # fname = str(url_count) + ".html"
                    # with open(fname, 'w') as log:
                    #     log.write(page)
                    real_url = f.geturl()
                    # url_count += 1
                    return tree, real_url
            except IOError as ioe:
                try:
                    description = "%s: %s" % (type(ioe.reason), list(ioe.reason))
                except (AttributeError, TypeError):
                    description = str(ioe)
                LOGGER.error("Encountered I/O-related error (%s: %s) when trying to open URL %s with POST data %s; waiting & retrying...", type(ioe), description, repr(url), data)
                sleep(config.RETRY_DELAY)
                continue
            except BadStatusLine:
                LOGGER.error("Encountered bad HTTP status line when trying to open URL %s with POST data %s; waiting & retrying...", repr(url), data)
                sleep(config.RETRY_DELAY)
                continue
    return tree4url
