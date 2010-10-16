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

from ConfigParser import RawConfigParser
from os.path import dirname, join as pathjoin

### Fetch configuration settings
_CONFIG_FILENAME = 'config.cfg'
#: Full path to configuration file
CONFIG_FILEPATH = pathjoin(dirname(__file__), _CONFIG_FILENAME)
cfg = RawConfigParser()
with open(CONFIG_FILEPATH, 'r') as config_file:
    cfg.readfp(config_file)

#: Name of main section in INI config file
_MAIN_SECT = 'main'
#: HTTP User-Agent to use
USER_AGENT = cfg.get(_MAIN_SECT, 'useragent')
LOGGER_NAME = cfg.get(_MAIN_SECT, 'loggername')
SCHEDULE_OF_CLASSES_LINK_TEXT = cfg.get(_MAIN_SECT, 'soclinktext')
EXCLUDE_FULL_SECTIONS_CHECKBOX_NAME = cfg.get(_MAIN_SECT, 'exclfullsectsname')
NAME_OF_SELECT_ELEMENT_FOR_TERMS = cfg.get(_MAIN_SECT, 'termselectname')
NAME_OF_SELECT_ELEMENT_FOR_SUBJECTS = cfg.get(_MAIN_SECT, 'subjselectname')
SUBJECTWISE_FORM_NAME = cfg.get(_MAIN_SECT, 'subjformname')
COURSENUM_CHECKBOXES_NAME_PART = cfg.get(_MAIN_SECT, 'coursenumcheckboxname')
DAYS_OF_WEEK_CHECKBOXES_NAME = cfg.get(_MAIN_SECT, 'doycheckboxname')
SUBJECT_SELECT_NAME = cfg.get(_MAIN_SECT, 'subjselectname')
UNLIMITED_AVAILABLE_SEATS = cfg.get(_MAIN_SECT, 'unlimitedavailability')
#: Subject codes to exclude
SUBJECT_CODE_BLACKLIST = cfg.get(_MAIN_SECT, 'subjectsblacklist')
DATA_UNAVAILABLE = cfg.get(_MAIN_SECT, 'dataunavailablemsg')

#: How many seconds to wait before retrying upon encountering a transient error.
RETRY_DELAY = float(cfg.get(_MAIN_SECT, 'waitbeforeretry'))
#: Socket timeout (in seconds) to set
SOCKET_TIMEOUT = float(cfg.get(_MAIN_SECT, 'socktimeout'))

BUILDING_CODE_URL = cfg.get(_MAIN_SECT, 'buildingcodeurl')
RESTRICTION_CODE_URL = cfg.get(_MAIN_SECT, 'restrictioncodeurl')

_BOOKSTORE_SECT = 'bookstore'
LACK_BOOK_LIST = cfg.get(_BOOKSTORE_SECT, 'nobooklistmsg')
REQUIRED_BOOK_CODE = cfg.get(_BOOKSTORE_SECT, 'requiredcode')
AS_SOFT_RESERVES = cfg.get(_BOOKSTORE_SECT, 'softreservestext')
NO_TEXTBOOK_REQUIRED = cfg.get(_BOOKSTORE_SECT, 'nonerequiredtext')
IN_STOCK = cfg.get(_BOOKSTORE_SECT, 'instocktext')

#Meeting type codes
_MTG_TYPE_CODES = "meetingtypecodes"
for option_name in cfg.options(_MTG_TYPE_CODES):
    globals()[option_name.upper()+"_CODE"] = cfg.get(_MTG_TYPE_CODES, option_name)

del cfg
