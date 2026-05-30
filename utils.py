#!/usr/bin/python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

manual = {}
manualWeb = [
    "AISmartBar",
    "ExtFind",
    "LayoutDebug",
    "SpeechDispatcher",
    "SwitchDocumentDirection",
    # Only seen in parent during testing but maybe it is used in web?
    "LinkPreview",
    # I didn't run the right tests, but feels like it must be used in web.
    "DampLoad",
]
manualNonWeb = [
    "HPKEConfigManager",
    "MozCachedOHTTP",
    "MozNewTabRemoteRendererProtocol",
]
for a in manualWeb:
    manual[a] = True
for a in manualNonWeb:
    manual[a] = False

def loadRemoteTypesFile(fileName):
    seenWeb = {}
    with open(fileName, "r") as f:
        lines = 0
        for l in f:
            if lines == 0:
                # Actors that have been seen in web processes during testing.
                for a in l.split():
                    seenWeb[a] = True
            elif lines == 1:
                # Actors that haven't been seen in web processes during testing.
                for a in l.split():
                    seenWeb[a] = False
            lines += 1
    return seenWeb

def niceList(msg, actors):
    actors.sort()
    numActors = 0
    col = len(msg)
    print(msg, end="")

    for a in actors:
        numActors += 1
        if col + len(a) > 80:
            print()
            col = 0
        if col == 0:
            before = ""
        else:
            before = " "
        if numActors == len(actors):
            after = ""
        else:
            after = ","
        toPrint = before + a + after
        print(toPrint, end="")
        col += len(toPrint)

    print()
