.. TritonScraper documentation master file, created by
   sphinx-quickstart on Fri Oct  1 22:18:55 2010.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to TritonScraper's documentation!
=========================================

Contents:

..  toctree::
    :maxdepth: 3
    
    intro
    tutorial
    datamodel
    config

Introduction
------------
TritonScraper is a `web scraper <http://en.wikipedia.org/wiki/Web_scraping>`_ for the `University of California, San Diego (UCSD) <http://ucsd.edu>`_'s `Schedule of Classes <https://www-act.ucsd.edu/cgi-bin/tritonlink.pl/2/students/academic/classes/schedule_of_classes.pl>`_ on `TritonLink`_, written in `Python <http://python.org>`_. That is, it is a library for programmatically extracting scheduling and enrollment information on UCSD classes.

Terminology
-----------
In order to avoid confusion, TritonScraper uses the same nomenclature as `TritonLink`_ whenever possible:

Course
    A course of academic study on a particular topic within a Subject.
    Each Course has a unique identifying Course Code.

Course Code
    A Subject Code and Course Number; e.g. CSE 15L.

Subject
    The academic subject of a Course; e.g. Computer Science & Engineering.

Subject Code
    The unique, short, all-uppercase abbreviation for a Subject; e.g. CSE.

Course Number
    The unique identifying number for a Course within a Subject.
    It can include an alphabetical suffix, so it's not strictly speaking a number. Examples: 15L, 110A.

Term
    An academic Quarter or Session; e.g. Fall Quarter 2010.

Term Code
    The short abbreviation used for a Term; e.g. FA10.

Instructor
    The person teaching a Course Instance. May or may not technically be a professor.

Course Instance
    A particular teaching of a Course with a particular Instructor during a particular Term, comprising a particular combination of scheduled events. TritonLink has no term for this; a better one should be thought up.

Seating/Seatedness
    Seated events have limited Seating; there is a limit on the number of students who can sign up for a Seated event.

Section ID
    The unique identifying number for a Course Instance seated event across all UCSD classes; e.g. 698362.

Section Number
    The identifying number for a Course Instance event. Only unique within that Course; e.g. B02.

..  automodule:: triton_scraper
    :members:

..  automodule:: __init__
    :members:


Querying interface
------------------
..  automodule:: triton_scraper.browser
    :members:

Other
-----
..  automodule:: triton_scraper.fetchparse
    :members:   

..  automodule:: triton_scraper.search_querier
    :members:   

..  automodule:: triton_scraper.course_results_parsing
    :members:   


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _TritonLink: http://tritonlink.ucsd.edu