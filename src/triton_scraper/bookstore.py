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
This module parses course textbook information from the `UCSD Bookstore's website <http://bookstore.ucsd.edu/>`_.

:copyright: (c) 2010 by Christopher Rebert.
:license: MIT, see :file:`LICENSE.txt` for more details.
"""

from decimal import Decimal

from triton_scraper.fetchparse import make_tree4url
from triton_scraper.util import *
from triton_scraper import config

class BookList(object):
    def __init__(self, required=None, optional=None, as_soft_reserves=False, unknown=False):
        #: Required books
        #:
        #: :type: list of :class:`Book`-s
        self.required = required or []
        #: Optional books
        #:
        #: :type: list of :class:`Book`-s
        self.optional = optional or []
        #: Is a course reader from A.S. Soft Reserves required?
        #:
        #: :type: bool
        self.as_soft_reserves = as_soft_reserves
        #: Indicates whether the UCSD Bookstore has yet to receive a booklist for the associated course
        #:
        #: :type: bool
        self.unknown = unknown
    
    def __repr__(self):
        if self.unknown:
            return "The UCSD Bookstore has not yet been given a book list."
        requireds = ["Required:"] + self.required
        if self.as_soft_reserves:
            requireds.append("Custom reader from A.S. Soft Reserves")
        requireds = "\n\t".join(str(entry) for entry in requireds)
        optionals = "\n\t".join(str(entry) for entry in ["Optional:"]+self.optional)
        string = '\n'.join([(requireds if self.any_required else ''), (optionals if self.optional else '')])
        return string
    
    @property
    def any_required(self):
        """Are any materials on this booklist required?
        
        :type: bool
        """
        return self.as_soft_reserves or self.required
    
    def add_book(self, book, required):
        """Add the given *book* to the booklist.
        
        :param book: textbook to add
        :type book: :class:`Book`
        :param required: is the textbook required?
        :type required: bool
        """
        (self.required if required else self.optional).append(book)
        

class Book(object):
    """Textbook from the UCSD Bookstore."""
    __FORMAT = u'ISBN {0.isbn}: "{0.title}" by {0.author}; ${0.used_price} Used, ${0.new_price} New; '
    def __init__(self, isbn, new_price=NaN, used_price=NaN, title='', author=''):
        #: Author of book
        #:
        #: :type: string
        self.author = author
        #: Title of book
        #:
        #: :type: string
        self.title = title
        #: International Standard Book Number
        #:
        #: :type: string
        self.isbn = isbn
        #: Price of a new copy at the UCSD Bookstore; NaN if new copies unavailable.
        #:
        #: :type: :class:`decimal.Decimal`
        self.new_price = new_price
        #: Price of a used copy at the UCSD Bookstore; NaN if used copies unavailable.
        #:
        #: :type: :class:`decimal.Decimal`
        self.used_price = used_price
    
    def __repr__(self):
        return self.__FORMAT.format(self).encode('utf8')

book_cells = XPath(RELATIVE_PREFIX+"/table[@border='1']/tr/td/font[not(@align='right')]")
discounted_price = XPath(RELATIVE_PREFIX+"/font[@color='#008000']")
def _availability2price(availability): # New Books, In Stock, Retail Price: $62.50
    return Decimal(availability.split("$")[1]) if config.IN_STOCK in availability else NaN
def _skipping_availability_side_headers(cells):
    for cell in cells:
        if cell.text:
            yield cell
def books_on(bookstore_url_from_tritonlink):
    """Returns book list based on the given course page at the UCSD Bookstore's website.
    
    :param bookstore_url_from_tritonlink: UCSD Bookstore website URL for a course section
    :type bookstore_url_from_tritonlink: string
    :rtype: :class:`BookList`
    """
    url = bookstore_url_from_tritonlink.replace("https", "http", 1)
    tree, _url = make_tree4url()(url)
    booklist = BookList()
    for sextuple in grouper(6, _skipping_availability_side_headers(book_cells(tree))):
        if config.LACK_BOOK_LIST in sextuple[0].text:# No book list
            return BookList(unknown=True)
        _sections, _instructor, required, author, title_comma_isbn = (cell.text for cell in sextuple[:5])
        availability = sextuple[-1]
        required = required == config.REQUIRED_BOOK_CODE
        title, isbn = title_comma_isbn.rsplit(", ", 1) # Principles Of General Chemistry, 2 Edition, 9780077470500
        if config.NO_TEXTBOOK_REQUIRED in title:
            return BookList(required=[])
        if config.AS_SOFT_RESERVES in title:
            booklist.as_soft_reserves = True
            continue
        discounts = discounted_price(availability)
        if discounts:
            discount = discounts[0]
            if config.IN_STOCK not in availability.text:
                new = NaN
            else:
                # New Books, Not in Stock*, Retail Price: $65.70, Discounted Price: <FONT COLOR="#008000">$21.03</FONT>
                new = Decimal(discount.text[1:])#remove dollar sign
            used = discount.tail
        else:
            new, used = availability.text.split("\n")
            new = _availability2price(new)
        used = _availability2price(used)
        booklist.add_book(Book(isbn, new, used, title, author), required)
    return booklist
