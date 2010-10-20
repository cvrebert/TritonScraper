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
This module fetches and holds data on TritonLink course restriction codes.

:copyright: (c) 2010 by Christopher Rebert.
:license: MIT, see :file:`LICENSE.txt` for more details.
"""

from triton_scraper.util import *
from triton_scraper.config import RESTRICTION_CODE_URL as _RESTRICTION_CODE_URL
from triton_scraper.fetchparse import make_tree4url

restriction_codes_and_descriptions = XPath(RELATIVE_PREFIX+"/tr[not(@bgcolor)]/td/text()")

tree, _url = make_tree4url()(_RESTRICTION_CODE_URL)
# if .strip() needed to ignore blank row
_CODE2DESCRIPTION = dict((code, desc) for code, desc in grouper(2, restriction_codes_and_descriptions(tree)) if code.strip())
del tree, _url

def restriction_code2description(code):
    try:
        return _CODE2DESCRIPTION[code]
    except KeyError:
        # The webpage listing the codes is outdated/non-exhaustive
        return '"%s"' % code
