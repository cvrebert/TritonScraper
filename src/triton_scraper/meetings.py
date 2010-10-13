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

from triton_scraper.util import INFINITY as _INFINITY
from triton_scraper.bookstore import books_on as _books_on

class Meeting(object):
    """A meeting with known start and end times."""
    def __init__(self, start_time, end_time, location=None, section_number=None):
        #: Time of day when the event starts.
        #:
        #: :type: :class:`datetime.time`
        self.start_time = start_time
        #: Time of day when the event ends.
        #:
        #: :type: :class:`datetime.time`
        self.end_time = end_time
        #: Location of the event.
        #:
        #: :type: :class:`Location` or :class:`LocationTBA` or :class:`UnknownLocation`
        self.location = location if location is not None else _UnknownLocation()
        #: The locally-unique identifying "number" for this meeting within the course; e.g. "B02".
        #:
        #: :type: string or None
        self.section_number = section_number
    
    @property
    def duration(self):
        """How long the event is in duration.

        :type: :class:`datetime.timedelta`
        """
        return self.end_time - self.start_time
    
    @property
    def _sect_num(self):
        return ("[%s] " % self.section_number) if self.section_number is not None else ""
    
    __FORMAT = "{0.start_time}-{0.end_time} in {0.location}"
    @property
    def _times_in_loc(self):
        return self.__FORMAT.format(self)

    def __repr__(self):
        """[SectionNumber] Start-End in Location"""
        return self._sect_num + self._times_in_loc

class OneShotMeeting(Meeting):
    """An meeting which is not recurring (i.e. happens only once)."""
    def __init__(self, date, start_time, end_time, location=None):
        Meeting.__init__(self, start_time=start_time, end_time=end_time, location=location, section_number=None)
        #: The date when the event takes place.
        #:
        #: :type: :class:`datetime.date`
        self.date = date
    
    __FORMAT = "{0._sect_num} {0.date} {0._times_in_loc}"
    def __repr__(self):
        return self.__FORMAT.format(self)
    
    @property
    def __key(self):
        return (self.date, self.start_time, self.end_time, self.location, self.section_number)
    
    def __eq__(self, other):
        return self.__key == other.__key
    
    def __ne__(self, other):
        return not self == other

class RecurringMeeting(Meeting):
    """A recurring meeting."""
    def __init__(self, section_number, instructor, start_time, end_time, days, location=None):
        Meeting.__init__(self, start_time=start_time, end_time=end_time, section_number=section_number, location=location)
        #: Days of the week which the event is held on.
        #:
        #: :type: :class:`DaysOfWeekSet`
        self.days = days
        #: The meeting's instructor.
        #:
        #: :type: :class:`Instructor` or None
        self.instructor = instructor
    
    __FORMAT = "{0._sect_num} {0.days}{1} {0._times_in_loc}"
    @property
    def _num_days_times_loc(self):
        return self.__FORMAT.format(self, (" with "+str(self.instructor)) if self.instructor is not None else "")
    
    def __repr__(self):
        return self._num_days_times_loc

class SeatedMeeting(object): #TBA
    """A meeting with limited seating."""
    def __init__(self, section_id, section_number, instructor, available_seats, total_seats, bookstore_url):
        #: The globally-unique identifying number for this meeting; e.g. 698362
        #:
        #: :type: int
        self.section_id = section_id
        #: The locally-unique identifying "number" for this meeting within the course; e.g. "B02".
        #:
        #: :type: string or None
        self.section_number = section_number
        #: The meeting's instructor.
        #:
        #: :type: :class:`Instructor` or None
        self.instructor = instructor
        #: The number of currently remaining available seats.
        #: A negative number means there are the absolute value of that number of people on the waitlist.
        #:
        #: :type: int or float('infinity')
        self.available_seats = available_seats
        #: The total number of seats for the event.
        #:
        #: :type: int or float('infinity')
        self.total_seats = total_seats
        #: URL of UCSD Bookstore webpage listing course textbooks.
        #:
        #: :type: string
        self._bookstore_url = bookstore_url
    
    __FORMAT = "{0.section_id} {0.section_number}{1} {0._seats_str}"
    def __repr__(self):
        return self.__FORMAT.format(self, (" with "+str(self.instructor)) if self.instructor is not None else "")
    
    @property
    def full(self):
        """Is the event full?

        :type: bool
        """
        return self.available_seats <= 0
    
    @property
    def unlimited_seating(self):
        """Does the event have unrestricted seating?

        :type: bool
        """
        return self.available_seats == _INFINITY
    
    @property
    def how_full(self):
        """How full the event is.
        If seating is unlimited, then it's considered 0% full.
        A waitlisted event is over 100% full.

        :type: float
        """
        if self.unlimited_seating:
            return 0
        elif self.available_seats < 0:
            return (abs(self.available_seats) + self.total_seats) / self.total_seats
        else:
            return self.available_seats / self.total_seats
    
    @property
    def _seats_str(self):
        if self.unlimited_seating:
            return "(no seating limit)"
        else:
            return "%s open/%s total" % (self.available_seats, self.total_seats)
    
    @property
    def booklist(self):
        """Textbooks for the meeting. None if the UCSD Bookstore hasn't received a booklist for the course.

        :type: :class:`BookList`
        """
        return _books_on(self._bookstore_url)

class RecurringSeatedMeeting(RecurringMeeting, SeatedMeeting):
    """A recurring meeting with limited seating."""
    def __init__(self, section_id, section_number, instructor, start_time, end_time, days, available_seats, total_seats, bookstore_url, location=None):
        RecurringMeeting.__init__(self, section_number=section_number, start_time=start_time, end_time=end_time, days=days, location=location)
        SeatedMeeting.__init__(self, section_id=section_id, section_number=section_number, instructor=instructor, available_seats=available_seats, total_seats=total_seats, bookstore_url=bookstore_url)
    
    __FORMAT = "{0.section_id} {0._num_days_times_loc} {0._seats_str}"
    def __repr__(self):
        return self.__FORMAT.format(self)