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

"""
This module handles fetching webpages from the internet and parsing them into :class:`lxml.etree.ElementTree`-s

:copyright: (c) 2010 by Christopher Rebert.
:license: MIT, see :file:`LICENSE.txt` for more details.
"""

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
def _without_brs(html):
    """Remove <br> tags which merely complicate our scraping."""
    return BR_TAGS.sub(' ', html)

def _parse_html(filelike, hack_around_broken_html=False):
    """Parses the HTML in the given file-like object, compensating for TritonLink's broken HTML if necessary, and returning the resulting ElementTree."""
    parser = etree.HTMLParser()
    html = _without_brs(filelike.read())
    if hack_around_broken_html:# HACK: Damn you, TritonLink! You made lxml barf.
        html = html.replace('question.gif"', 'question.gif">').replace("')\";", "');\"")
    # print "="*40
    # from BeautifulSoup import BeautifulSoup
    # print BeautifulSoup(StringIO(html)).prettify()
    return etree.parse(StringIO(html), parser)

# url_count = 0
def make_tree4url():
    """
    :returns: a new :func:`tree4url` function with its own fresh associated :class:`CookieJar`
    :rtype: function
    """
    opener = build_opener(HTTPCookieProcessor(CookieJar()))
    def tree4url(url, post_args=None, hack_around_broken_html=False):
        """Fetches and parses the webpage at the given URL.
        Cookies are accepted and presented to the server when necessary. Cookies are persistent across calls to the same tree4url.
        Identifies itself using the User-agent string specified in the TritonScraper configuration file.
        
        :param url: URL to fetch
        :type url: string
        :param post_args: HTTP POST data to send
        :type post_args: dict of strings to (possibly lists of) strings
        :param hack_around_broken_html: do we need to use our hack to fix TritonLink's broken HTML so that :mod:`lxml` can parse it?
        :type hack_around_broken_html: bool
        :returns: HTML element tree of the webpage and actual URL browsed to (after redirects etc.)
        :rtype: tuple of :class:`lxml.etree.ElementTree` and string
        """
        # global url_count
        req = Request(url)
        req.add_header('User-agent', config.USER_AGENT)
        data = urlencode(post_args, doseq=True) if post_args is not None else None
        LOGGER.debug("Browsing URL %s with POST data %s", url, post_args)
        while True:
            try:
                with closing(opener.open(req, data, config.SOCKET_TIMEOUT)) as f:
                    tree = _parse_html(f, hack_around_broken_html)
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
