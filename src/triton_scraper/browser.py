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

from time import sleep as _sleep
from collections import namedtuple

from triton_scraper import config
from triton_scraper.util import *
from triton_scraper.fetchparse import make_tree4url
from triton_scraper.search_querier import prepare_class_search_query
from triton_scraper.course_results_parsing import course_instances_from, TransientError

TRITONLINK_HOME_URL = "http://tritonlink.ucsd.edu/" # if this changes, they've probably changed stuff enough to break this module

VALUE = 'value'

#: A :class:`collections.namedtuple` of a subject's name and code.
Subject = namedtuple('Subject', 'name code')
#: A :class:`collections.namedtuple` of a term's name, code, and default status.
Term = namedtuple('Term', 'name code is_default')

# Slower but more robust:
# TERM_FORM_TITLE = "Select search term:"
# term_selector_title_spans = etree.XPath("//span[contains(text(), '%s')]" % TERM_FORM_TITLE)
SELECTED = 'selected'
term_options = XPath("//select[@name='%s']/option" % config.NAME_OF_SELECT_ELEMENT_FOR_TERMS)
def options2Terms(option_elems):
    return [Term(option_elem.text.strip().decode('utf8'), option_elem.get(VALUE), SELECTED in option_elem.attrib) for option_elem in option_elems]

schedule_of_classes_hrefs = XPath("//a[.='%s']/@href" % config.SCHEDULE_OF_CLASSES_LINK_TEXT)
subject_options = XPath("//select[@name='%s']/option" % config.NAME_OF_SELECT_ELEMENT_FOR_SUBJECTS)
### Where it all comes together
class TritonBrowser(object):
    """Used to programmatically browse TritonLink's Schedule of Classes."""
    def __init__(self):
        """Takes no arguments."""
        self._tree4url = make_tree4url()
    
    @property
    def _url_of_schedule(self):
        """A string which is a URL for the "Schedule of Classes" main search page."""
        tree, _url = self._tree4url(TRITONLINK_HOME_URL)
        return schedule_of_classes_hrefs(tree)[0]

    @property
    def terms(self):
        """Recent, current, and upcoming UCSD academic terms.
        
        :returns: Term name, term code, is-default triples; e.g. ("Fall Quarter 2010", "FA10", True)
        :type: List of :class:`Term`-s.
        """
        tree, _url = self._tree4url(self._url_of_schedule)
        return options2Terms(term_options(tree))
    
    # @property
    # def departments(self):
    #     tree = self._tree4url(self._url_of_schedule)
    #     return [(option.text.strip(), option.attrib[VALUE]) for option in dept_options(tree)]
    
    @property
    def subjects(self):
        """UCSD's academic subjects. Not to be confused with "departments", which are somehow different.
        
        :returns: Subject name, subject code pairs; e.g. ("Computer Science & Engineering", "CSE")
        :type: Generator of :class:`Subject`-s."""
        tree, _url = self._tree4url(self._url_of_schedule)
        for option in subject_options(tree):
            name = option.text.split("-")[1].strip()
            code = option.get(VALUE).decode('utf8')
            if code not in config.SUBJECT_CODE_BLACKLIST:
                yield Subject(name, code)
    
    def _run_class_search(self, term_code, subject_code):
        """Runs a search for all courses in the given subject during the given term.
        Returns resulting HTML ElementTree of first results page."""
        sched_tree, sched_url = self._tree4url(self._url_of_schedule)
        url, query = prepare_class_search_query(term_code, subject_code, sched_tree, sched_url)
        result_tree, _url = self._tree4url(url, query, hack_around_broken_html=True)
        return result_tree
    
    def classes_for(self, term_code, subject_code):
        """
        :param term_code: Academic term code (e.g. "FA10")
        :type term_code: string
        :param subject_code: Course subject code (e.g. "CSE")
        :type subject_code: string
        :returns: Courses in the given subject during the given term.
        :rtype: Generator of :class:`CourseInstance`-s
        """
        LOGGER.info("Getting courses in subject %s for term %s", repr(subject_code), repr(term_code))
        results_tree = self._run_class_search(term_code, subject_code)
        while True:
            try:
                course_instances, url = course_instances_from(results_tree, subject_code)
            except TransientError:
                LOGGER.info("Waiting before retrying after transient error")
                # wait and retry
                _sleep(config.RETRY_DELAY)
                continue
            for course_instance in course_instances:
                yield course_instance
            if url is None:
                break
            results_tree, _url = self._tree4url(url, hack_around_broken_html=True)
    
    def all_classes_during(self, term_code):
        """
        :param term_code: Academic term code (e.g. "FA10")
        :type term_code: string
        :returns: All courses taking place during the given term.
        :rtype: Generator of :class:`CourseInstance`-s
        """
        for subject in self.subjects:
            for course_inst in self.classes_for(term_code, subject.code):
                yield course_inst

# The arbitrary .decode('utf8')s are needed due to inscrutable machinations of lxml.
# Whether UTF-8 is the right choice is unknown.
