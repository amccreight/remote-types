#!/usr/bin/python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This script is about adding annotations specifically to the file
# mobile/shared/chrome/geckoview/geckoview.js

# I wasn't able to get logging working on Android, but none of these actors use
# remoteTypes and they look like they are probably dealing with web content, so
# add annotations for all of them.

import argparse
from pathlib import Path
import re
from utils import niceList

actorsStartRe = re.compile("^(\\s*)actors: {")

def fixGeckoViewActorDecls(baseFile, fileName, results):
    changedAny = False

    foundActors = False

    currActor = None
    safeFor = None
    actorAlreadySafe = False

    actualFileName = baseFile + fileName
    outFileName = actualFileName + ".tmp"

    with open(actualFileName, "r") as fi, open(outFileName, "w") as fo:
        for l in fi:
            if not foundActors:
                m = actorsStartRe.match(l)
                if m:
                    foundActors = True
                    indentWith = m.group(1)
                    actorsEnd = indentWith + "},\n"
                    actorStartRe = re.compile(indentWith + "  ([^:]*): {")
                    actorEnd = indentWith + "  },\n"
                    safeFor = indentWith + "    safeForUntrustedWebProcess: true,\n"
            elif currActor == None:
                if l == actorsEnd:
                    foundActors = False
                    actorsEnd = None
                else:
                    m = actorStartRe.match(l)
                    if m:
                        currActor = m.group(1)
                        actorStartRe = None
                        actorAlreadySafe = False
            else:
                if l == actorEnd:
                    if actorAlreadySafe:
                        results["already"].append(currActor)
                    else:
                        results["fixed"].append(currActor)
                        changedAny = True
                        fo.write(safeFor)
                    currActor = None
                    actorEnd = None
                    safeFor = None
                elif l == safeFor:
                    actorAlreadySafe = True
            fo.write(l)

    # We should have found the end of an actor by the end of the file.
    assert currActor == None

    if changedAny:
        Path(outFileName).rename(actualFileName)
        return
    Path(outFileName).unlink()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fix JS actor registrations in geckoview.js.")
    parser.add_argument("firefox_dir",
                        help="Root of Firefox source code directory.")
    args = parser.parse_args()

    firefoxDir = args.firefox_dir
    if not firefoxDir.endswith("/"):
        firefoxDir += "/"

    results = {"already": [], "fixed": [], "notWeb": []}

    file = "mobile/shared/chrome/geckoview/geckoview.js"
    fixGeckoViewActorDecls(firefoxDir, file, results)

    niceList("* Actors that had the annotation added:", results["fixed"])
    niceList("* Actors that already had the annotation:", results["already"])
    niceList("* Actors that were seen that shouldn't have the annotation:", results["notWeb"])
