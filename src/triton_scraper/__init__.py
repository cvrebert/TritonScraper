# minimal logging setup
import logging
logger = logging.getLogger("triton_scraper")
logger.setLevel(logging.DEBUG)
class NullHandler(logging.Handler):
    def emit(self, record):
        pass
logger.addHandler(NullHandler())
del logging, logger, NullHandler

from triton_scraper.datatypes import *
from triton_scraper.browser import TritonBrowser
# names = globals().keys()
# import triton_scraper
# for name in names:
#     try:
#         globals()[name].__module__
#     except AttributeError:
#         continue
#     else:
#         globals()[name].__module__ = triton_scraper
# del name, names, triton_scraper
