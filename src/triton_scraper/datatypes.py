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

from __future__ import division
from warnings import simplefilter as _simplefilter, catch_warnings as _catch_warnings

from triton_scraper import config as _config
from triton_scraper.locations import UnknownLocation as _UnknownLocation
from triton_scraper.restriction_codes import restriction_code2description

class DaysOfWeekSet(frozenset):
    """A :class:`set` of days of the week.

    Each individual day is represented using its corresponding entry in :attr:`DAYS_IN_ORDER`.

    Iterating over the set yields the days in their conventional ordering; Sunday is considered the first day of the week."""
    
    #: Normalized day of the week abbrevations used by :class:`DaysOfWeekSet`, in order, starting with Sunday. A tuple of strings.
    DAYS_IN_ORDER = tuple('Sun Mon Tue Wed Thu Fri Sat'.split())
    _DAYS_OF_WEEK_SET = set(DAYS_IN_ORDER)
    #: Day of the week abbreviations used by TritonLink, in order, starting with Sunday. A tuple of strings.
    UCSD_DAY_ABBEVIATIONS = tuple('Sun M Tu W Th F S'.split())
    
    @classmethod
    def from_ucsd_abbrevs(cls, ucsd_abbreviated):
        """Additional constructor.
        
        :param ucsd_abbreviated: string representing a group of days of the week using TritonLink's day of the week abbreviations (see :attr:`UCSD_DAY_ABBEVIATIONS`; e.g. "TuTh")
        """
        norm_days = set()
        for index, name in enumerate(cls.UCSD_DAY_ABBEVIATIONS):
            if ucsd_abbreviated.startswith(name):
                ucsd_abbreviated = ucsd_abbreviated[len(name):]
                norm_days.add(cls.DAYS_IN_ORDER[index])
        if ucsd_abbreviated:
            raise ValueError, "Unrecognized day name abbreviations: "+repr(ucsd_abbreviated)
        return cls(norm_days)
    
    def __init__(self, iterable):
        """Creates a new DaysOfWeekSet from an iterable containing strings from :attr:`DAYS_IN_ORDER`.
        The ordering of the strings doesn't matter."""
        with _catch_warnings(): # Suppress irrelevant DeprecationWarning
            _simplefilter("ignore")
            frozenset.__init__(self, iterable)
        if self - self._DAYS_OF_WEEK_SET:
            raise ValueError, "Non-day-names present"
    
    def __iter__(self):
        """Yields day names in conventional order. A week is considered to start on Sunday."""
        for day in self.DAYS_IN_ORDER:
            if day in self:
                yield day
    
    def __repr__(self):
        return "{%s}" % (", ".join(self))
    
_NORMAL_EVENT_TYPES = "lecture discussion lab tutorial seminar studio midterm problem_session review_session make_up_session film".split()
def _event_type_name2code(type_name):
    return getattr(_config, type_name.upper()+"_CODE")
def add_event_list_properties(klass):
    for type_name in _NORMAL_EVENT_TYPES:
        property_name = type_name+"s"
        extractor = lambda self, type_code=_event_type_name2code(type_name): self._code2event_list[type_code]
        setattr(klass, property_name, property(extractor))
    return klass
@add_event_list_properties
class CourseInstance(object):
    """An instance of a course. Two instances of the same course typically have different instructors and/or lecture times."""
    
    _FORMAT = '{0.code} "{0.name}" ({0.units} units) with {0.instructor}\n\tPrerequisites: {0.prerequisites_url}'
    def __init__(self, subject_code, course_number, name, units, restriction_codes=None, prerequisites_url=None):
        #: Code for course's subject; e.g. "CSE"
        #:
        #: :type: string
        self.subject_code = subject_code
        #: Course "number"; e.g. "15L"
        #:
        #: :type: string
        self.course_number = course_number
        #: Descriptive name of course.
        #:
        #: :type: string
        self.name = name
        if restriction_codes is None:
            restriction_codes = []
        #: Human-readable descriptions of registration restrictions applicable to course.
        #:
        #: :type: list of strings
        self.restrictions = set(restriction_code2description(restrict_code) for restrict_code in restriction_codes)
        #: Number of credit units; NaN if variable.
        #:
        #: :type: float
        self.units = units
        #: URL of page listing prerequisites for course.
        #:
        #: :type: string or None
        self.prerequisites_url = prerequisites_url
        self._code2event_list = dict( (_event_type_name2code(type_name), []) for type_name in _NORMAL_EVENT_TYPES)
        #: Final exam
        #:
        #: :type: :class:`OneShotEvent`
        self.final = None
        
        self.instructor = None
    
    # @property
    # def instructor(self):
    #     """Course's instructor.
    #     
    #     :type: :class:`Instructor` or :class:`InstructorTBA`"""
    #     # if not self._instructor:
    #         # raise ValueError, self.code+" has no instructor!"
    #     return self._instructor or InstructorTBA()
    
    # @instructor.setter
    # def instructor(self, value):
    #     if not value:
    #         raise ValueError, "Attempted to set invalid instructor value: "+repr(value)
    #     
    #     if not self._instructor:
    #         self._instructor = value
                
    @property
    def code(self):
        """Full course code; e.g. "CSE 15L".
        
        :type: string
        """
        return "%s %s" % (self.subject_code, self.course_number)
    
    def __repr__(self):
        parts = [self._FORMAT.format(self)]
        if not self.restrictions:    
            parts.append("\tUnrestricted")
        else:
            parts.append("\tRestrictions: " + ", ".join(self.restrictions))
        event_types = [("Seminars", self.seminars), ("Studios", self.studios), ("Lectures", self.lectures), ("Discussions", self.discussions), ("Labs", self.labs), ("Tutorials", self.tutorials), ("Films", self.films), ("Problem Sessions", self.problem_sessions), ("Review Sessions", self.review_sessions), ("Make-up Sessions", self.make_up_sessions), ("Midterms", self.midterms)]
        for name, events in event_types:
            if events:
                part = "\t%s:\n\t\t%s" % (name, "\n\t\t".join(str(event) for event in events))
                parts.append(part)
        parts.append("\tFinal: "+str(self.final))
        return "\n".join(parts)
    
    def add_event(self, meeting_type_code, event):
        try:
            self._code2event_list[meeting_type_code].append(event)
        except KeyError:
            raise ValueError, "Unrecognized meeting type code: %s" % repr(mtg_type)
        else:
            if self.instructor is None and hasattr(event, 'instructor') and event.instructor is not None and not isinstance(event.instructor, InstructorTBA):
                self.instructor = event.instructor
    
    def __bool__(self):
        return any(event_list for event_list in self._code2event_list.values())
del add_event_list_properties


_STAFF = "Staff"
class Instructor(object):
    """A known course instructor."""
    __FORMAT = "{0.first_name} {0.last_name} <{0.email}>"

    @classmethod
    def from_full_name(cls, full_name, email=None):
        """Alternate constructor. Parses out the instructor's first and last names from their full name.
        May return an :class:`InstructorTBA` if they are TBA.
        
        :param full_name: the instructor's full name (e.g. "Doe, John")
        :type full_name: string
        :param email: the instructor's email address
        :type email: string or None
        """
        if full_name.strip() == _STAFF:
            return InstructorTBA()
        while full_name.count(",") > 1:
            index = full_name.rindex(",")
            full_name = full_name[:index]+full_name[index+1:]
        last, first = full_name.split(", ")
        return cls(last, first, email)

    def __init__(self, last, first, email=None):
        #: Instructor's given name
        #:
        #: :type: string
        self.first_name = first
        #: Instructor's surname
        #:
        #: :type: string
        self.last_name = last
        #: Instructor's email address, if they have one.
        #:
        #: :type: string or None
        self.email = email

    def __repr__(self):
        "FirstName LastName <EmailAddress>"
        return self.__FORMAT.format(self)
    
    @property
    def __key(self):
        return (self.first_name, self.last_name)
    
    def __eq__(self, other):
        """Instructors with the same first and last name are equal to each other"""
        return not isinstance(other, InstructorTBA) and self.__key == other.__key
    
    def __ne__(self, other):
        return not self == other


class InstructorTBA(object):
    """An as-yet-unknown instructor."""
    def __init__(self):
        pass
    
    def __repr__(self):
        return "(TBA)"
    
    def __eq__(self, other):
        """Unknown instructors are equal to each other"""
        return isinstance(other, self.__class__)
    
    def __ne__(self, other):
        return not self == other
