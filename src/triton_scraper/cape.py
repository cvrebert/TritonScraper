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
This module browses, scrapes, and parses `CAPE's website <http://www.cape.ucsd.edu>`_ into useful objects.

:copyright: (c) 2010 by Christopher Rebert.
:license: MIT, see :file:`LICENSE.txt` for more details.
"""

from contextlib import closing as _closing
from time import sleep as _sleep
from decimal import Decimal
from collections import namedtuple as _namedtuple#, OrderedDict
from urlparse import urljoin as _urljoin
from urllib import urlencode as _urlencode

import triton_scraper.config
from triton_scraper.util import RELATIVE_PREFIX, XPath
from triton_scraper.fetchparse import make_tree4url
from lxml import etree

CAPE_SEARCH_URL = "http://www.cape.ucsd.edu/stats.html"

_tree4url = make_tree4url()
def url2tree(url):
    tree, _url = _tree4url(url)
    return tree

#FIXME: enable
# self_cape = XPath(RELATIVE_PREFIX+"/div[@align='right' and text() = 'SelfCAPE']")

search_forms = XPath(RELATIVE_PREFIX+"/form[@name='searchQuery']")
select_elements = XPath(RELATIVE_PREFIX+"/select")
def _search_form_and_select_tag():
    tree = url2tree(CAPE_SEARCH_URL)
    form = search_forms(tree)[0]
    select = select_elements(form)[0]
    return form, select

VALUE = 'value'
option_elements = XPath(RELATIVE_PREFIX+"/option")
Department = _namedtuple('Department', "code name form_value")    
def list_departments():
    form, select = _search_form_and_select_tag()
    for opt in option_elements(select):
        val = opt.get(VALUE)
        if not val: continue
        code, name = opt.text.split(" - ")
        yield Department(code.strip(), name.strip(), val)

# HTTP_METHOD = 'method'
# HTTP_GET = 'get'
NAME = 'name'
ACTION = 'action'
section_links = XPath(RELATIVE_PREFIX+"/a[@target='_new']/@href")
def capes_for(department_form_val):
    form, select = _search_form_and_select_tag()
    field_name = select.get(NAME)
    # method = form.get(HTTP_METHOD)
    # if method != HTTP_GET:
        # raise ValueError("Expected GET form submission method; Got "+repr(method))
    action = form.get(ACTION)
    dest_url = _urljoin(CAPE_SEARCH_URL, action)
    dept_url = "%s?%s" % (dest_url, _urlencode({field_name:department_form_val}))
    tree = url2tree(dept_url)
    for link in section_links(tree):
        cape = parse_detailed_page(link)
        if cape is not None:
            yield cape

page_is_dud = XPath("/html/body[contains(text(), 'No statistics found')]")
departments = XPath(RELATIVE_PREFIX+"/td[@width='110']/text()")
enrollments = XPath(RELATIVE_PREFIX+"/td[@width='155']/text()")
questionaires_returneds = XPath(RELATIVE_PREFIX+"/td[@width='180']/text()")
term_codes = XPath(RELATIVE_PREFIX+"/td[@width='109']/div/text()")
course_codes = XPath(RELATIVE_PREFIX+"/td[@width='56']/text()")
instructor_names = XPath(RELATIVE_PREFIX+"/td[@colspan='2' and @height='15']/text()")
team_taught = XPath(RELATIVE_PREFIX+"/td[@colspan='9' and text()='Team Taught']")
def parse_detailed_page(url):
    tree = url2tree(url)
    if page_is_dud(tree):
        return None
    department_code = departments(tree)[0]
    
    enrollment = int(enrollments(tree)[0].split(": ")[1])
    respondents = int(questionaires_returneds(tree)[0].split(": ")[1])
    term_code = term_codes(tree)[0]
    course_code = course_codes(tree)[0]
    instructor = instructor_names(tree)
    if instructor:
        instructor = instructor[0].strip() #FIXME: parse into Instructor. multi-instructor courses have semicolons btw names. last, first
    else:
        instructor = None # Some courses have no listed instructor
    
    nums = [string2num(s) for s in (u.strip() for u in numbers(tree)) if s]

    class_levels = parse_class_levels(nums)
    reasons_for_taking = parse_reasons_for_taking(nums)
    expected_grades = parse_expected_grades(nums)
    # _expected_gpa = Decimal(expected_gpas(tree)[0].strip())
    agree_disagree_qs = questions_negative_4_thru_16E(tree)[NUM_PRE_AGREEMENT_QUESTIONS-1:-NUM_INSTRUCTOR_QUESTIONS] # skip class level, reason, expected grade, and Instructor Questions
    taught_by_team = team_taught(tree)
    num_agreement_qs = 6 if taught_by_team else NUM_AGREEMENT_QUESTIONS
    sixteen_agree_disagrees = [parse_agree_disagree_row(nums) for i in range(num_agreement_qs)]
    question2agreement = zip(agree_disagree_qs[-num_agreement_qs:], sixteen_agree_disagrees)#OrderedDict()
    skip_instructor_questions(nums)
    hours_studying_per_week = parse_study_hours(nums)
    attendance = parse_attendance(nums)
    recommend_course = parse_recommendations(nums)
    if not taught_by_team:
        recommend_prof = parse_recommendations(nums)
    else:
        recommend_prof = RecommendLevel(0, 0)
    cape = CourseAndProfessorEvaluation(department_code=department_code, term_code=term_code, course_code=course_code, instructor_name=instructor, enrollment=enrollment, respondents=respondents, class_levels=class_levels, reasons_for_taking=reasons_for_taking, expected_grades=expected_grades, agreement_questions=question2agreement, hours_studying_per_week=hours_studying_per_week, attendance=attendance, recommend_course=recommend_course, recommend_instructor=recommend_prof)
    if nums:
        print cape
        print nums
        raise ValueError, "Problem when trying to parse %s %s %s (%s)" % (term_code, course_code, instructor, url)
    return cape

AgreementLevels = _namedtuple('AgreementLevels', "na strong_disagree disagree neutral agree strong_agree")
# FIXME: account for #responses != total #students
#(None,) + range(-2,3)
NUM_AGREEMENT_LEVELS = len(AgreementLevels._fields)
def parse_agree_disagree_row(l):
    responses = slice_off(l, NUM_AGREEMENT_LEVELS)
    _num_resp = slice_off(l, 1)
    if _num_resp:# CAPE pages don't include stats if no non-N/A responses
        _mean, _std_dev = slice_off(l, 2)
        _percents = slice_off(l, NUM_AGREEMENT_LEVELS-1) # no percentage for N/A
    return AgreementLevels(*responses)

StudyHours = _namedtuple('StudyHours', "zero_one two_three four_five six_seven eight_nine ten_eleven twelve_thirteen fourteen_fifteen sixteen_seventeen eighteen_nineteen twenty_plus")
# setup StudyHours.VALUES
# _values = []
# _n = Decimal('0.5')
# TWO = Decimal('2')
# for _i in range(11):
#     _values.append(_n)
#     _n += TWO
# StudyHours.VALUES = tuple(_values)
# del _values, _n, _i
NUM_STUDY_HOURS_INTERVALS = 11
def parse_study_hours(l):
    hours = StudyHours(*slice_off(l, NUM_STUDY_HOURS_INTERVALS))
    _num_resp = slice_off(l, 1)
    if _num_resp:# CAPE pages don't include stats if no responses given
        _avg_hours = slice_off(l, 1)
        _percents = slice_off(l, NUM_STUDY_HOURS_INTERVALS)
    return hours

Attendance = _namedtuple('Attendance', "rarely some most")
# 0, 0.5, 1
NUM_ATTENDANCE_TYPES = len(Attendance._fields)
def parse_attendance(l):
    attendance = Attendance(*slice_off(l, NUM_ATTENDANCE_TYPES))
    _num_resp = slice_off(l, 1)
    if _num_resp:
        _percents = slice_off(l, NUM_ATTENDANCE_TYPES)
    return attendance

RecommendLevel = _namedtuple('RecommendLevel', "no yes")
#False, True
def parse_recommendations(l):
    rec_level = RecommendLevel(*slice_off(l, 2))
    _num_resp = slice_off(l, 1)
    _percents = slice_off(l, 2)
    return rec_level


numbers = XPath(RELATIVE_PREFIX+"/td[@class='style3']/div[@align='center']/text()")
def string2num(string):
    if string.endswith('%'):
        return int(string[:-1])/Decimal(100)
    elif '.' in string:
        return Decimal(string)
    else:
        return int(string)
def slice_off(l, n):
    if n == 1:
        return l.pop(0)
    sliced = l[:n]
    del l[:n]
    return sliced
NUM_AGREEMENT_QUESTIONS = 16
NUM_INSTRUCTOR_QUESTIONS = 5
NUM_PRE_AGREEMENT_QUESTIONS = 4
questions_negative_4_thru_16E = XPath(RELATIVE_PREFIX+"/td[@colspan='2' and @class='style3']/text()")

NUM_INSTRUCTOR_QUESTIONS = 5
NUM_FIELDS_PER_FULL_INSTRUCTOR_QUESTION = 15
NUM_FIELDS_PER_BLANK_INSTRUCTOR_QUESTION = 7
INDEX_OF_FIRST_PERCENTAGE_IN_FULL_INSTRUCTOR_QUESTION = 9
def has_full_instructor_questions(l):
    return isinstance(l[INDEX_OF_FIRST_PERCENTAGE_IN_FULL_INSTRUCTOR_QUESTION], Decimal)
def skip_instructor_questions(l):
    for i in range(NUM_INSTRUCTOR_QUESTIONS):
        fields_per_question = NUM_FIELDS_PER_FULL_INSTRUCTOR_QUESTION if has_full_instructor_questions(l) else NUM_FIELDS_PER_BLANK_INSTRUCTOR_QUESTION
        slice_off(l, fields_per_question)

ClassLevels = _namedtuple('ClassLevels', "freshman sophomore junior senior graduate extension")
#range(1,6) + (None,)
NUM_CLASS_LEVELS = len(ClassLevels._fields)
def parse_class_levels(l):
    class_levels = ClassLevels(*slice_off(l, NUM_CLASS_LEVELS))
    _num_class_level_resps = slice_off(l, 1)
    if _num_class_level_resps:
        _class_level_percents = slice_off(l, NUM_CLASS_LEVELS)
    return class_levels

ReasonsForTaking = _namedtuple('ReasonsForTaking', "major minor ge elective interest")
NUM_REASONS_FOR_TAKING = len(ReasonsForTaking._fields)
def parse_reasons_for_taking(l):
    reasons = ReasonsForTaking(*slice_off(l, NUM_REASONS_FOR_TAKING))
    _reason_resps = slice_off(l, 1)
    if _reason_resps:
        _reason_percents = slice_off(l, NUM_REASONS_FOR_TAKING)
    return reasons

ExpectedGrades = _namedtuple('ExpectedGrades', "A B C D F P NP")
#range(4,-1,-1) + (True, False)
NUM_POSSIBLE_GRADES = len(ExpectedGrades._fields)
def parse_expected_grades(l):
    expected_grades = ExpectedGrades(*slice_off(l, NUM_POSSIBLE_GRADES))
    _num_grade_resps = slice_off(l, 1)
    if _num_grade_resps:
        _expects_grade_percents = slice_off(l, NUM_POSSIBLE_GRADES)
    return expected_grades

#FIXME: remember section ID#
_CourseAndProfessorEvaluation = _namedtuple('_CourseAndProfessorEvaluation', "section_id department_code term_code subject_code course_number instructor enrollment respondents class_levels reasons_for_taking expected_grades hours_studying_per_week attendance recommend_course recommend_instructor agreement_questions")
class CourseAndProfessorEvaluation(_CourseAndProfessorEvaluation):
    FORMAT = "{0.term_code}: {0.course_code} with {0.instructor_name}; ({0.respondents} responses/{0.enrollment} enrolled)"
    def __repr__(self):
        parts = [self.FORMAT.format(self), self.class_levels, self.reasons_for_taking, self.expected_grades]
        parts = [str(part) for part in parts]
        parts.extend("%s\n\t\t%s" % (q, a) for q, a in self.agreement_questions)
        parts.extend(str(part) for part in (self.hours_studying_per_week, self.attendance, self.recommend_course, self.recommend_instructor))
        return "\n\t".join(parts)
