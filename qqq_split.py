#!/usr/bin/python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Extract every line that contains a QQQ and echo out only the code afterwards.
# This was needed for the old-style printf JS actor logging and is obsolete now.

import sys

for l in sys.stdin:
    s = l.split("QQQ")
    if len(s) == 1:
        continue
    if len(s) != 2:
        assert len(l) > 100
        continue
    print(s[1].strip())
