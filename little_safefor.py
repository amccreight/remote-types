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


registerRe = re.compile("^(\\s*)ChromeUtils.register([a-zA-Z]+)Actor\\(\"([^\"]+)\", {$")

# XXX Need to make this echo the modified file to a tmp file, move it over.

# XXX Print out a list of actors we modified, saw but didn't modify etc.

def fixLittleActorDecls(seenWeb, fileName):
    foundAny = False

    currActor = None
    safeFor = None
    endCurrActor = None
    actorAlreadySafe = False

    with open(fileName, "r") as fi:
        for l in fi:
            m = registerRe.match(l)
            if m:
                foundAny = True
                assert currActor is None
                assert safeFor is None
                assert endCurrActor is None
                actorAlreadySafe = False

                indentWith = m.group(1)
                safeFor = indentWith + "safeForUntrustedWebProcess: true,\n"
                endCurrActor = indentWith + "});\n"
                kind = m.group(2)
                assert kind == "Window" or kind == "Process"
                currActor = m.group(3)
                print("MATCHED: " + currActor)
                continue
            if currActor:
                if l == safeFor:
                    actorAlreadySafe = True
                elif l == endCurrActor:
                    okayForWeb = False
                    if currActor in seenWeb:
                        if seenWeb[currActor]:
                            okayForWeb = True
                    else:
                        print(f"Unknown actor: {currActor}")
                        assert False
                    if okayForWeb:
                        if not actorAlreadySafe:
                            print("==>" + safeFor[:-1])
                    else:
                        assert not actorAlreadySafe
                    currActor = None
                    safeFor = None
                    endCurrActor = None

    if not foundAny:
        print("!!! did not find any in " + fileName)


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

