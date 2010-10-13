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

from triton_scraper.config import BUILDING_CODE_URL
from triton_scraper.util import *
from triton_scraper.fetchparse import make_tree4url

_TO_BE_ANNOUNCED = "TBA"

class Location(object):
    """A known campus location."""
    @classmethod
    def new(cls, bldg, room):
        if not bldg and not room:
            return cls.unknown
        elif _TO_BE_ANNOUNCED in (bldg, room):
            return LocationTBA()
        else:
            return cls(bldg, room)
    
    @property#FIXME: BROKEN
    @staticmethod
    def unknown():
        return UnknownLocation()
    
    def __init__(self, building_code, room):
        if not building_code or not room:
            raise ValueError, "Vague location"
        #: UCSD building code (e.g. "CENTER")
        #:
        #: :type: string
        self.building = Building.for_code(building_code)
        #: Room "number" (e.g. "001A")
        #:
        #: :type: string
        self.room_number = room

    def __repr__(self):
        return "%s %s" % (self.building.name, self.room_number)
    
    @property
    def __key(self):
        return (self.building_code, self.room_number)
    
    def __eq__(self, other):
        """Locations with the same building code and room number are equal to each other"""
        return isinstance(other, Location) and self.__key == other.__key
    
    def __ne__(self, other):
        return not self == other


class UnknownLocation(object):
    """An unknown campus location."""
    def __init__(self):
        pass
    
    def __repr__(self):
        return "(Unknown)"
    
    def __eq__(self, other):
        return isinstance(other, UnknownLocation)
    
    def __ne__(self, other):
        return not self == other


class LocationTBA(object):
    """A campus location which has yet To Be Announced."""
    def __init__(self):
        pass
    
    def __repr__(self):
        return "(TBA)"
    
    def __eq__(self, other):
        return isinstance(other, LocationTBA)
    
    def __ne__(self, other):
        return not self == other


building_info_table_texts = XPath(RELATIVE_PREFIX+"/tr[not(@bgColor)]/td/text()")
class Building(object):
    _CODE2OBJ = {}
    
    @classmethod
    def for_code(cls, building_code):
        """Gives the :class:`Building` object corresponding to the given UCSD building code.
        
        :param building_code: UCSD campus building code (e.g. CSB)
        :type building_code: string
        :rtype: :class:`Building`
        """
        try:
            return cls._CODE2OBJ[building_code]
        except KeyError:
            raise KeyError, "No such building known by code %s" % repr(building_code)
    
    def __init__(self, code, name, area):
        #: UCSD building code (e.g. "CSB")
        #: :type: string
        self.code = code
        #: Descriptive name of building
        #: :type: string
        self.name = name
        #: Area of UCSD campus that building is located in (e.g. "University Center")
        #: :type: string
        self.area = area
    
    __FORMAT = "{0.name} ({0.code}) in {0.area}"
    def __str__(self):
        return self.__FORMAT.format(self)

# Initialize Building._CODE2OBJ
tree = make_tree4url()(BUILDING_CODE_URL)[0]
for quadruple in grouper(4, building_info_table_texts(tree)):
    code, name, area, _map_num = (s.strip() for s in quadruple)
    Building._CODE2OBJ[code] = Building(code, name, area)
del quadruple, tree, code, name, area, _map_num

# Begin total HACKS
Building._CODE2OBJ["LEDDN"] = Building._CODE2OBJ["LEDDN AUD"] # Dammit TritonLink, "AUD" isn't a room!
Building._CODE2OBJ["CPMC"] = Building("CPMC", "Conrad Prebys Music Center", "Sixth") # TritonLink is outdated. Sixth is a guess.
Building._CODE2OBJ["OTRSN"] = Building("OTRSN", "Otterson Hall (i.e. Rady School)", "Roosevelt") # TritonLink is outdated
Building._CODE2OBJ["TM102"] = Building("TM102", "TM102", "TM102") # Mystery building not in building code index
Building._CODE2OBJ["MYR-A"] = Building("MYR-A", '"MYR-A"', "MYR-A") # Mystery building not in building code index
Building._CODE2OBJ["SPIES"] = Building("SPIES", "SPIES", "SIO") # Mystery building not in building code index. SIO is a guess.
#       Reflect situation on the ground :-)
cse = Building._CODE2OBJ["EBU3B"]
cse.code = "CSE (a.k.a. %s)" % cse.code
cse.name = "Computer Science & Engineering Building (a.k.a. %s)" % cse.name
Building._CODE2OBJ["CSE"] = cse
del cse
