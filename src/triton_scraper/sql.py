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
This module dumps :class:`CourseAndProfessorEvaluation` data into `SQLite <http://www.sqlite.org/>`_ databases using :mod:`sqlite3`.

:copyright: (c) 2010 by Christopher Rebert.
:license: MIT, see :file:`LICENSE.txt` for more details.
"""
#FIXME: .sqlite will work for file extension
from sqlite3 import connect as _sqlite_connect
from contextlib import closing as _closing

import triton_scraper.cape as _cape

#: SQLite type name for integers
_INT = "INTEGER"
#: SQLite type for strings
_STR = "TEXT"
#: SQLite declaration part for a primary key
_PRIMARY_KEY = "PRIMARY KEY"
#: Name of Section ID columns in SQLite database tables
SECTION_ID_COL = "section_id"

def _create_statement_for(table_name, columns):
    """
    :param table_name: name of table to create; does not get escaped, so don't use untrusted user input
    :type table_name: string
    :param columns: (column name, SQLite type) pairs
    :type columns: list of 2-tuples of strings
    :rtype: string
    :returns: SQLite CREATE TABLE statement
    """
    columns_def = ", ".join("%s %s" % pair for pair in CAPE_TABLE_COLUMNS)
    return "CREATE TABLE %s(%s)" % (table_name, columns_def)

def foreign_key(col, datatype, foreign_table, foreign_column):
    return "%s %s REFERENCES %s(%s)" % (col, datatype, foreign_table, foreign_column)

#: Name of main CAPE SQLite table
CAPE_TABLE_NAME = "Cape"
#: List of (column name, SQLite type name) tuples for main CAPE SQLite table
CAPE_TABLE_COLUMNS = [
    (SECTION_ID_COL, _INT+" "+_PRIMARY_KEY),#FIXME: add this
    ("department_code", _STR),
    ("term_code", _STR),
    ("subject_code", _STR),#FIXME: split course_code
    ("course_number", _STR),
    ("instructor", _STR),
    ("enrollment", _INT),
    ("respondents", _INT)] + [
    (level_name, _INT) for level_name in _cape.ClassLevels._fields] + [
    (reason_name, _INT) for reason_name in _cape.ReasonsForTaking._fields] + [
    (grade, _INT) for grade in _cape.ExpectedGrades._fields] + [
    (hours, _INT) for hours in _cape.StudyHours._fields] + [
    (attendance_category, _INT) for attendance_category in _cape.Attendance._fields] + [
    ("%s_%s" % (recommendee, recommendation), _INT) for recommendation in ("no", "yes") for recommendee in ("course", "instructor")]

#: SQLite CREATE TABLE statement for main CAPE SQLite table
CREATE_CAPE_TABLE_STMT = _create_statement_for(CAPE_TABLE_NAME, CAPE_TABLE_COLUMNS)

#: Name of subsidiary level-of-agreement question answers SQLite table
AGREEMENT_TABLE_NAME = "Agreement"
#: List of (column name, SQLite type name) tuples for the level-of-agreement question answers SQLite table
AGREEMENT_TABLE_COLUMNS = [foreign_key(SECTION_ID_COL, _INT, CAPE_TABLE_NAME, SECTION_ID_COL), ("question", _STR)] + [(level_name, _INT) for level_name in _cape.AgreementLevels._fields]
#: SQLite CREATE TABLE statement for level-of-agreement question answers SQLite table
CREATE_AGREEMENT_TABLE_STMT = _create_statement_for(AGREEMENT_TABLE_NAME, AGREEMENT_TABLE_COLUMNS)

def create_cape_tables(sqlite_conn):
    """Create SQL tables in the *sqlite_conn* database to store CAPE data. The tables will be named :const:`AGREEMENT_TABLE_NAME` and :const:`CAPE_TABLE_NAME`.
    
    :param sqlite_conn: database to create tables in
    :type sqlite_conn: :class:`sqlite3.Connection` or :class:`sqlite3.Cursor`
    """
    sqlite_conn.execute(CREATE_CAPE_TABLE_STMT)
    sqlite_conn.execute(CREATE_AGREEMENT_TABLE_STMT)

def _positional_insert(sqlite_conn, table_name, values):
    """Insert *values* into the table *table_name* of the database *sqlite_conn*.
    
    :param sqlite_conn: database whose table is to be written to
    :type sqlite_conn: :class:`sqlite3.Connection` or :class:`sqlite3.Cursor`
    :param table_name: name of the table to insert values into; does not get escaped, so don't use untrusted user input
    :type table_name: string
    :param values: row of values to insert into the given table
    :type values: sequence
    """
    insert_stmt = "INSERT INTO %s VALUES (%s)" % (table_name, ",".join("?" for i in range(len(values))))
    sqlite_conn.execute(insert_stmt, values)

def _dump_just_cape_itself(cape, sqlite_conn):
    """Inserts the data from the *cape* into database *sqlite_conn*.
    Does not add the data from :attr:`CourseAndProfessorEvaluation.agreement_questions`.
    
    :param cape: the CAPE whose data is to be inserted
    :type cape: :class:`CourseAndProfessorEvaluation`
    :param sqlite_conn: the database to write to
    :type sqlite_conn: :class:`sqlite3.Connection` or :class:`sqlite3.Cursor`
    """
    plain = cape[:8]
    flattened = sum([], cape[8:-1])
    cape_values = plain + flattened
    _positional_insert(sqlite_conn, CAPE_TABLE_NAME, cape_values)

def _dump_agreement_levels(section_id, question, agreement_levels, sqlite_conn):
    """Inserts agreement level response data *agreement_levels* for the question *question* regarding the Course Instance with Section ID *section_id* into the database *sqlite_conn*.
    
    :param section_id: Section ID of the Course Instance 
    :type section_id: int
    :param question: CAPE level-of-agreement survey question that the response data *agreement_levels* is for
    :type question: string
    :param agreement_levels: agreement level response data to insert
    :type agreement_levels: :class:`AgreementLevels`
    :param sqlite_conn: the database to write to
    :type sqlite_conn: :class:`sqlite3.Connection` or :class:`sqlite3.Cursor`
    """
    _positional_insert(sqlite_conn, AGREEMENT_TABLE_NAME, [section_id, question] + agreement_levels)

def dump_into_db(cape, sqlite_conn):
    """Write the data in *cape* to the database *sqlite_conn*.
    
    :param cape: the CAPE whose data is to be written
    :type cape: :class:`CourseAndProfessorEvaluation`
    :param sqlite_conn: the database to write to
    :type sqlite_conn: :class:`sqlite3.Connection` or :class:`sqlite3.Cursor`
    """
    with sqlite_conn:
        _dump_just_cape_itself(cape, sqlite_conn)
        for question, agree_levels in cape.agreement_questions:
            _dump_agreement_levels(cape.section_id, question, agree_levels, sqlite_conn)

def dump_into_file(capes, filepath):
    """Serialize *capes* into the file *filepath* as an `SQLite <http://www.sqlite.org/>`_ database (see :mod:`sqlite3`).
    
    :param capes: the CAPE to serialize
    :type capes: list of :class:`CourseAndProfessorEvaluation`
    :param filepath: path to file to write SQLite data to
    :type filepath: string
    """
    with _closing(_sqlite_connect(filepath)) as conn:
        create_cape_tables(conn)
        for cape in capes:
            dump_into_db(cape, conn)
