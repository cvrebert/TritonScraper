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
This module prepares TritonLink Schedule of Classes search queries.

:copyright: (c) 2010 by Christopher Rebert.
:license: MIT, see :file:`LICENSE.txt` for more details.
"""

from urlparse import urljoin

from triton_scraper import config
from triton_scraper.util import *

# HTML attributes
NAME = 'name'
VALUE = 'value'

### Generation of query
hidden_inputs = XPath(RELATIVE_PREFIX+"/input[@type='hidden']")
def _extract_hidden_inputs_of(form):
    """Extracts all hidden inputs in the given form so that they may be passed along in the query"""
    form_vars = dict( (input_tag.get(NAME), input_tag.get(VALUE)) for input_tag in hidden_inputs(form) )
    return form_vars

HTML_TRUE = 'on'
coursenum_checkboxes = XPath(RELATIVE_PREFIX+"/input[contains(@name, '%s')]" % config.COURSENUM_CHECKBOXES_NAME_PART)
def _check_all_coursenum_boxes_of(form):
    """Checks all course number range checkboxes so as to not exclude any courses based on their course number"""
    return dict( (input_tag.get(NAME), HTML_TRUE) for input_tag in coursenum_checkboxes(form))

days_checkboxes = XPath(RELATIVE_PREFIX+"/input[@name='%s']" % config.DAYS_OF_WEEK_CHECKBOXES_NAME)
def _check_all_day_checkboxes_of(form):
    """Checks all the day of the week checkboxes so as to now exclude any courses based on what days of the week they take place"""
    values = [input_tag.get(VALUE) for input_tag in days_checkboxes(form)]
    return {config.DAYS_OF_WEEK_CHECKBOXES_NAME : values}

OPTION_TAG = 'option'
time_selects = XPath(RELATIVE_PREFIX+"/select[contains(@name, 'start') or contains(@name, 'end')]")
def _choose_default_times(form):
    """Selects the default time of day options so as to not exclude any courses based on their time of day"""
    return dict( (select.get(NAME), select.find(OPTION_TAG).get(VALUE)) for select in time_selects(form))

#Just-below-top-level functions used by prepare_class_search_query
HTML_FALSE = 'false'
BROAD_CLASS_SEARCH_FORM_VAR_FETCHERS = (_extract_hidden_inputs_of, _check_all_coursenum_boxes_of, _check_all_day_checkboxes_of, _choose_default_times)
def _broad_class_search_form_query(form, term_code, subject_code):
    """Prepares the broadest possible course search query for the given term and subject"""
    query = {}
    for form_var_fetcher in BROAD_CLASS_SEARCH_FORM_VAR_FETCHERS:
        query.update(form_var_fetcher(form))
    query[config.EXCLUDE_FULL_SECTIONS_CHECKBOX_NAME] = HTML_FALSE
    query[config.SUBJECT_SELECT_NAME] = subject_code
    query[config.NAME_OF_SELECT_ELEMENT_FOR_TERMS] = term_code
    return query

HTTP_METHOD = 'method'
POST = 'post'
ACTION = 'action'
def _class_search_post_url_from(absolute_url, form):
    """Determines absolute URL to submit HTTP POST query request to"""
    method = form.get(HTTP_METHOD)
    if method != POST:
        raise ValueError("Expected POST form submission method; Got "+repr(method))
    action = form.get(ACTION)
    dest_url = urljoin(absolute_url, action)
    return dest_url

### The One Externally-relevant Function
subject_forms = XPath("//form[@name='%s']" % config.SUBJECTWISE_FORM_NAME)
def prepare_class_search_query(term_code, subject_code, sched_tree, sched_url):
    """
    :param term_code: code of the UCSD academic term to restrict the search to
    :type term_code: string
    :param subject_code: code of the academic subject to restrict the search to
    :type subject_code: string
    :param sched_tree: HTML element tree of the UCSD Schedule of Classes search webpage
    :type sched_tree: :class:`lxml.etree.ElementTree`
    :param sched_url: URL of the UCSD Schedule of Classes search webpage
    :type sched_url: string
    :returns: HTTP POST destination URL and form query data for running a search for all courses in the given subject during the given term
    :rtype: tuple of a string and a dict of strings to (possibly lists of) strings
    """
    form = subject_forms(sched_tree)[0]
    query = _broad_class_search_form_query(form, term_code, subject_code)
    form_post_url = _class_search_post_url_from(sched_url, form)        
    return form_post_url, query
