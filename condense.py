#!/usr/bin/python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sys
import re

# This takes in the raw logs when MOZ_LOG for JSActorService is enabled and
# eliminates all of the redundancy without fundamentally changing the output
# format. Basically, this strips out all of the logging goo before "I/JSActorService"
# and then eliminates duplicate lines once that is done.

# You can run this script with something like:
# cat *.log | rg "I/JSActorService" | python3 condense.py | sort > condense.txt

logRe = re.compile("I/JSActorService.*$")

seen = set([])

for l in sys.stdin:
    m = logRe.search(l)
    if not m:
        continue
    line = m.group(0)
    if line in seen:
        continue
    seen.add(line)
    print(line)
