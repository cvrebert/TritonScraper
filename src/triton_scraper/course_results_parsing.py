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

from time import strptime
from datetime import date, time

from triton_scraper import config
from triton_scraper.util import *
from triton_scraper.datatypes import *
from triton_scraper.meetings import *
from triton_scraper.locations import Location

HREF = 'href'
NBSP = u'\xa0'
ANCHOR = 'a'

TABLE_ROW = 'tr'
def rows_in_table(table):
    """Returns all table row elements in the given HTML table Element"""
    return table.findall(TABLE_ROW)

anchors_recursively = XPath(RELATIVE_PREFIX+"/a") # all anchor elements that are descendants of the given Element

class TransientError(RuntimeError):
    """An non-permanent error that should go away if you retry"""

### Just-below-top-level functions used by course_instances_from()
BOLD = 'b'
def extract_current_page_num(pagination_table):
    b = pagination_table.find(BOLD) 
    return int(b.text.split(' ')[1]) # "(Page 1 of 32):"
class CannotProcessRequestError(TransientError):
    """'TritonLink cannot process your request at this time'; the problem is on TritonLink's end"""
pagination_like_tables = XPath(RELATIVE_PREFIX+"/table[@width='100%']/"+RELATIVE_PREFIX+"/td[@align='RIGHT']")
RESULTS_PAGE_LINK_XPATH_TEMPLATE = "a[text()='%s']/@href"
def next_result_page_url(results_tree):
    try:
        pagination_table = pagination_like_tables(results_tree)[-1]
    except IndexError:
        #FIXME: LOOK FOR THIS SUBSTRING "We cannot process your request at this time."
        raise CannotProcessRequestError
    next_page_num = extract_current_page_num(pagination_table) + 1
    urls = pagination_table.xpath(RESULTS_PAGE_LINK_XPATH_TEMPLATE % next_page_num)
    return urls[0] if urls else None

has_boundary_cell = XPath("td[@valign='MIDDLE']")
def remove_field_header_rows_in(courses_table):
    for row in rows_in_table(courses_table):
        if has_boundary_cell(row):
            break
        else:
            courses_table.remove(row)

def rows_grouped_by_course_instances(courses_table):
    cur_group = None
    rows = rows_in_table(courses_table)
    for row in rows:
        if has_boundary_cell(row):
            if cur_group is not None:
                yield cur_group
            cur_group = []
        cur_group.append(row)

### Course header parsing
class ProblematicCourse(ValueError):
    """This type of course is problematic to parse"""

texts_of_divs = XPath("div/text()")
title_tds = XPath(RELATIVE_PREFIX+"/td[@class='TITLETXT']")
def parse_course_header(first_row, subject_code):
    restrict_codes, course_num, nested_table = first_row
    restrict_codes = texts_of_divs(restrict_codes)
    course_num = course_num.text.strip()
    
    td = title_tds(nested_table)[0]
    if td.text: # missing normal link to course catalog (cf. COGS 92)
        #FIXME: include course catalog link
        name_and_units = td.text
        border = name_and_units.rindex('(')
        name = name_and_units[:border].strip()
        units = extract_units(name_and_units)
        prereqs_anchor = anchors_recursively(nested_table)[0]
    else:
        name_and_units, prereqs_anchor = anchors_recursively(nested_table)[:2]
        name = name_and_units.text
        units = extract_units(name_and_units.tail)
    prereqs_link = extract_JavaScript_link(prereqs_anchor)
    course_inst = CourseInstance(subject_code=subject_code, course_number=course_num, restriction_codes=restrict_codes, name=name, units=units, prerequisites_url=prereqs_link)
    LOGGER.debug("Parsing instance of course %s", repr(course_inst.code))
    return course_inst

NaN = float('NaN')
def extract_units(name_andor_units):
    """Extracts the number of academic credit units the course is worth.
    Returns NaN if the number of units is variable."""
    start = name_andor_units.rindex('(') + 1
    end = name_andor_units.index(' ', start)
    units = name_andor_units[start:end]
    try:
        return float(units)
    except ValueError:
        if '/' in units or '-' in units:
            LOGGER.debug("Encountered variable units string %s; using NaN", repr(units))
            return NaN
        LOGGER.error("Encountered unparseable units string %s", repr(units))
        raise

def extract_JavaScript_link(anchor):
    """Extracts normal hyperlink from anchor with hyperlink embedded in JavaScript."""
    js_link = anchor.get(HREF)# JavaScript:openLinkInNewWindow('http://...', ...)
    start = js_link.find("'") + 1
    end = js_link.find("'", start)
    return js_link[start:end]

### Time parsing
TIMES_SEPARATOR = " - "
def parse_start_end_times(start_end_times):
    """Parses the starting and ending times of a course event into a (start, end) tuple of :class:`datetime.time`-s."""
    return tuple(parse_ucsd_time(ucsd_time) for ucsd_time in start_end_times.text.split(TIMES_SEPARATOR))

UCSD_TIME_FORMAT = "%I:%M%p"
def parse_ucsd_time(ucsd_time):
    """Parses a time in TritonLink's format into a :class:`datetime.time`"""
    ucsd_time += 'm' # a/p -> am/pm
    struct_time = strptime(ucsd_time, UCSD_TIME_FORMAT)
    return time(struct_time.tm_hour, struct_time.tm_min)

### Lecture parsing
def parse_unseated_event(row, course_inst):
    lectures = course_inst.lectures
    _sect_id, mtg_type, sect_num, mtg_days_of_wk, start_end_times, bldg, room, instructor = row
    if _sect_id.text.strip():# req'd, but time+location TBA
        return parse_TBA_seminar_or_sect(row, course_inst)
    mtg_type = mtg_type.text
    sect_num = sect_num.text
    mtg_days_of_wk = mtg_days_of_wk.text
    days = DaysOfWeekSet.from_ucsd_abbrevs(mtg_days_of_wk)
    start, end = parse_start_end_times(start_end_times)
    location = Location.new(bldg.text.strip(), room.text.strip())
    instructor = parse_instructor(instructor) if instructor.text != NBSP else None
    meeting = RecurringMeeting(sect_num, instructor, start, end, days, location)
    course_inst.add_event(mtg_type, meeting)

def parse_instructor(instructor):
    """Parses out an instructor cell into a triton_scraper.datatypes.Instructor"""
    mailtos = anchors_recursively(instructor)
    if mailtos:
        anchor = mailtos[0]
        email = anchor.get(HREF).split(':')[1] #remove mailto:
        full_name = anchor.text
    else:
        full_name = instructor.text
        email = None
    return Instructor.from_full_name(full_name, email)

PROBLEMATIC_MEETING_TYPES = (config.RESEARCH_CONFERENCE_CODE, config.INDEPENDENT_STUDY_CODE, config.PRACTICUM_CODE)
### Section parsing
def parse_seated_event(row, course_inst):
    sect_id, mtg_type, sect_num, mtg_days_of_wk, start_end_times, bldg, room, instructor, avail, limit, books = row
    mtg_type = mtg_type.text
    #FIXME: PRACTICUM_CODE not strictly problematic
    if mtg_type in PROBLEMATIC_MEETING_TYPES:
        msg = "Instance of course %s deemed problematic due to including meeting of type code %s" % (repr(course_inst.code), repr(mtg_type))
        LOGGER.info(msg)
        raise ProblematicCourse, msg
    sect_id = int(sect_id.text)
    sect_num = sect_num.text
    days = DaysOfWeekSet.from_ucsd_abbrevs(mtg_days_of_wk.text)
    start, end = parse_start_end_times(start_end_times)
    bldg = bldg.text.strip()
    room = room.text.strip()
    location = Location.new(bldg, room)
    available_seats, total_seats = parse_seating(avail, limit)
    books_link = extract_JavaScript_link(books.find(ANCHOR))
    instructor = parse_instructor(instructor) if instructor.text != NBSP else None
    meeting = RecurringSeatedMeeting(sect_id, sect_num, instructor, start, end, days, available_seats, total_seats, books_link, location)
    course_inst.add_event(mtg_type, meeting)

class SeatingDataUnavailableError(TransientError):
    "Seating data temporarily unavailable from TritonLink"

INFINITY = float('infinity')
def parse_seating(available_cell, total_cell):
    """Parses seating information into a triton_scraper.datatypes.Seatedness"""
    # print etree.tostring(available_cell)
    avail = available_cell.text
    total = total_cell.text
    if avail: # still seats available
        return int(avail.strip()), int(total)
    else: # waitlist
        avail = available_cell.find("span").text.strip() # "Full waitlist(17)"
        if avail == config.UNLIMITED_AVAILABLE_SEATS:
            return INFINITY, INFINITY
        elif avail == config.DATA_UNAVAILABLE:
            LOGGER.error("Encountered unavailablity of seating data")
            raise SeatingDataUnavailableError
        start = avail.index('(') + 1
        end = avail.index(')', start)
        avail = avail[start:end]
        return -int(avail), int(total) # negative indicates waitlist    

def parse_TBA_seminar_or_sect(row, course_inst):
    sect_id, mtg_type, sect_num, _where_when_TBA, instructor, avail, total, books = row
    mtg_type = mtg_type.text
    sect_id = row[0].text
    if sect_id == NBSP:# additional seminar time
        return parse_unseated_event(row, course_inst)
    sect_id = int(sect_id)
    sect_num = sect_num.text
    available_seats, total_seats = parse_seating(avail, total)
    books_link = extract_JavaScript_link(books.find(ANCHOR))
    instructor = parse_instructor(instructor) if instructor.text != NBSP else None
    meeting = SeatedMeeting(sect_id, sect_num, instructor, available_seats, total_seats, books_link)
    course_inst.add_event(mtg_type, meeting)
    
### Final & Midterm parsing
def parse_one_shot(row, course_inst):
    """Parses a table row for a one-time event and adds it to the course instance"""
    _sect_id, mtg_type, date, _mtg_doy, start_end_times, bldg, room, _ = row
    mtg_type = mtg_type.text
    date = parse_ucsd_date(date.text)
    start, end = parse_start_end_times(start_end_times)
    location = Location.new(bldg.text.strip(), room.text.strip())
    one_shot = OneShotMeeting(date, start, end, location)
    if mtg_type == config.FINAL_CODE:
        if course_inst.final is not None and course_inst.final != one_shot:
            raise ValueError, "Multiple final exams\n(Old: %s\n New: %s)" % (course_inst.final, one_shot)
        course_inst.final = one_shot
    else:
        course_inst.add_event(mtg_type, one_shot)

UCSD_DATE_FORMAT = "%m/%d/%Y"
def parse_ucsd_date(ucsd_date):
    """Parses a date in UCSD format into a :class:`datetime.date`"""
    struct_time = strptime(ucsd_date, UCSD_DATE_FORMAT)
    return date(struct_time.tm_year, struct_time.tm_mon, struct_time.tm_mday)

was_cancelled = XPath(RELATIVE_PREFIX+"/span[@class='redtxt' and text()='Cancelled']")
### The One Externally-relevant Function
courses_like_tables = XPath(RELATIVE_PREFIX+"/table[@border='0' and @width='100%' and @cellspacing='2' and @cellpadding='3']")
def course_instances_from(results_page_tree, subject_code):
    """Takes the ElementTree of a course search results HTML page and the subject code searched for.
    Returns a list of course instances on the page and the URL of the next search results page (or None if this was the last page)"""
    next_page_url = next_result_page_url(results_page_tree)
    LOGGER.debug("Next result page URL: %s", next_page_url)
    courses_table = courses_like_tables(results_page_tree)[0]
    remove_field_header_rows_in(courses_table)        
    row_groups = rows_grouped_by_course_instances(courses_table)
    
    course_instances = []
    for rows in row_groups:
        try:
            course_inst = parse_course_header(rows.pop(0), subject_code)
            for row in rows:
                row = row[3:] # remove empties
                # print [c.text for c in row]
                # print etree.tostring(row)
                if len(row) == 8:
                    mtg_type = row[1].text
                    if mtg_type in (config.INDEPENDENT_STUDY_CODE, config.PRACTICUM_CODE, config.CONFERENCE_CODE, config.CLINICAL_CLERKSHIP_CODE, config.FIELDWORK_CODE):
                        raise ProblematicCourse
                    elif mtg_type in (config.FINAL_CODE, config.MIDTERM_CODE, config.PROBLEM_SESSION_CODE, config.REVIEW_SESSION_CODE, config.MAKE_UP_SESSION_CODE):
                        parse_one_shot(row, course_inst)
                    elif mtg_type in (config.LECTURE_CODE, config.DISCUSSION_CODE, config.LAB_CODE, config.TUTORIAL_CODE, config.FILM_CODE, config.STUDIO_CODE):
                        parse_unseated_event(row, course_inst)
                    elif mtg_type == config.SEMINAR_CODE:
                        parse_TBA_seminar_or_sect(row, course_inst)
                    else:
                        raise ValueError, "Unrecognized meeting type: "+repr(mtg_type)
                elif len(row) == 11:#Discussion/Lab/Tutorial
                    parse_seated_event(row, course_inst)
                else:# Free-form; ignore
                    if row and was_cancelled(row[-1]):
                        LOGGER.info("A meeting of %s was cancelled", repr(course_inst.code))
                    else:
                        LOGGER.info("Free-form row for %s ignored", repr(course_inst.code))
                    continue
                #FIXME: see if should ignore Final-less courses
                #FIXME: Parse CAPE
                #FIXME: See if should drop courseinstances w/ only TBA Tutorials
        except ProblematicCourse:
            # print 'SKIPPED PROBLEMATIC COURSE'
            continue # Skip problematic courses
        else:
            if not course_inst:
                # Entire course instance cancelled
                LOGGER.info("An entire instance of %s was cancelled" % repr(course_inst.code))
                continue
            course_instances.append(course_inst)
            print course_inst.code,
            # for lst in course_inst._code2event_list.values():
                # for m in lst:
                    # if isinstance(m, SeatedMeeting):
                        # print m.booklist
    return course_instances, next_page_url
