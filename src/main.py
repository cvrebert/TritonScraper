#!/usr/bin/env python
from sys import stdout
from os.path import expanduser

from triton_scraper.browser import TritonBrowser

from logging import FileHandler, Formatter, getLogger
LOGGER = getLogger("triton_scraper")

handler = FileHandler(expanduser("~/Desktop/triton.log"))
formatter = Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
LOGGER.addHandler(handler)

browser = TritonBrowser()
reached = False
for sub in browser.subjects:
    sub = sub[1]
    # if not reached:
        # FIXME: prob w/ BIMM
        # if sub == 'BGGN':
            # reached = True
        # else: continue
    print (sub+' ')*25
    for klass in browser.classes_for("FA10", sub):
        # print klass
        stdout.flush()
# print
