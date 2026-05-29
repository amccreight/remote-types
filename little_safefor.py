#!/usr/bin/python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# First, create a list of all of the files that call the register actor
# methods.
# From the Firefox source directory:
#   rg -l "ChromeUtils.registerProcessActor" > /tmp/file1.txt
#   rg -l "ChromeUtils.registerWindowActor" > /tmp/file2.txt
# cat /tmp/file1.txt /tmp/file2.txt | sort | uniq > reg_files.txt

import argparse
import re
from utils import loadRemoteTypesFile


registerRe = re.compile("^\\s*ChromeUtils.register([a-zA-Z]+)Actor\\(\"([^\"]+)\", {$")


def fixLittleActorDecls(seenWeb, fileName):
    with open(fileName, "r") as fi:
        for l in fi:
            m = registerRe.match(l)
            if not m:
                if "ChromeUtils.register" in l:
                    print("OOPS: " + l[:-1])
                continue
            kind = m.group(1)
            assert kind == "Window" or kind == "Process"
            actor = m.group(2)
            print("MATCHED: " + actor)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fix individual JS actor registrations.")
    parser.add_argument("file_name",
                        help="File where first line is actors that have been "
                            "seen in web process during testing, and second "
                            "line is those that haven't")
    parser.add_argument("firefox_dir",
                        help="Root of Firefox source code directory.")
    args = parser.parse_args()

    firefoxDir = args.firefox_dir
    if not firefoxDir.endswith("/"):
        firefoxDir += "/"

    seenWeb = loadRemoteTypesFile(args.file_name)

    f = firefoxDir + "remote/shared/js-process-actors/WebDriverDocumentInsertedActor.sys.mjs"
    fixLittleActorDecls(seenWeb, f)

