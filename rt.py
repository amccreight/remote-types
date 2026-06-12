#!/usr/bin/python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sys
import re

# Analyze the condensed remote type logs and summarize the output in various
# formats, including CSV.

initRe = re.compile("^init (.+); ((?:no )?remoteTypes)$")
matchRe = re.compile("^match ([^ ]+) (.+)$")

actors = {}
remoteTypes = {}

for l in sys.stdin:
    m = initRe.match(l)
    if m:
        actor = m.group(1)
        hasRemoteTypes = (m.group(2) == "remoteTypes")
        actors[actor] = hasRemoteTypes
        continue
    m = matchRe.match(l)
    assert m
    actor = m.group(1)
    remoteType = m.group(2)
    remoteTypes.setdefault(actor, set([])).add(remoteType)


neverMatchedRT = set([])
neverMatchedNoRT = set([])

for a, hasRemoteTypes in actors.items():
    if a in remoteTypes:
        continue
    if hasRemoteTypes:
        neverMatchedRT.add(a)
    else:
        neverMatchedNoRT.add(a)

webIso = set([])
web = set([])
otherRT = set([])
otherNoRT = set([])

for a, rts in remoteTypes.items():
    if "webIsolated" in rts:
        webIso.add(a)
        assert not actors[a] or a == "TestWindow"
        continue
    if "web" in rts:
        web.add(a)
        assert not actors[a] or a == "TestProcessActor"
        continue
    assert a in actors
    if actors[a]:
        otherRT.add(a)
    else:
        otherNoRT.add(a)

def csvRemoteTypes(rtOrder, a):
    rts = set(["web" if rt.startswith("web") else rt for rt in remoteTypes[a]])
    return ", ".join(["Y" if rt in rts else "" for rt in rtOrder])

def fullCSV():
    allRemoteTypes = set([])
    rtCounts = {}
    for a, rts in remoteTypes.items():
        allRemoteTypes = allRemoteTypes.union(rts)

        haveWeb = False
        for rt in rts:
            if rt.startswith("web"):
                if haveWeb:
                    continue
                haveWeb = True
                rt = "web"
            rtCounts[rt] = rtCounts.setdefault(rt, 0) + 1

    rtCountsList = sorted([(c, rt) for rt, c in rtCounts.items()])
    rtCountsList.reverse()
    rtOrder = [rt for (_, rt) in rtCountsList]

    # Header.
    print(f"Actor, remoteTypes?, {", ".join(rtOrder)}")

    # Never matched actors.
    print("Never matched (no remoteTypes)")
    for a in sorted(list(neverMatchedNoRT)):
        print(a)
    print("Never matched (remoteTypes)")
    for a in sorted(list(neverMatchedRT)):
        print(f"{a}, Y")

    # Never web actors.
    print("Never web (no remoteTypes)")
    for a in sorted(list(otherNoRT)):
        print(f"{a}, , {csvRemoteTypes(rtOrder, a)}")

    print("Never web (remoteTypes)")
    for a in sorted(list(otherRT)):
        print(f"{a}, Y, {csvRemoteTypes(rtOrder, a)}")

    print("Sometimes web")
    for a in sorted(list(web.union(webIso))):
        print(f"{a}, {"Y" if actors[a] else ""}, {csvRemoteTypes(rtOrder, a)}")


# This prints out the actors seen with web content remote types on the first line,
# and with non web content remote types on the second line. This is intended to be
# used as input to the safefor.py script.
def seenInWeb():
    seenInWeb = set([])
    notSeenInWeb = set([])

    for a, rts in remoteTypes.items():
        seen = False

        for rt in rts:
            if rt.startswith("web") or rt.startswith("file"):
                seenInWeb.add(a)
                seen = True
                break
 
        if not seen:
            notSeenInWeb.add(a)

    print(" ".join(sorted(list(seenInWeb))))
    print(" ".join(sorted(list(notSeenInWeb))))

seenInWeb()


def actorsRemoteTypesString(actors):
    return ", ".join([f"{a} ({", ".join(sorted(list(remoteTypes[a])))})" for a in actors])

def actorSummary():
    print("Never matched actors:")
    print(f"  With remoteTypes: {", ".join(sorted(list(neverMatchedRT)))}")
    print(f"  Without remoteTypes: {", ".join(sorted(list(neverMatchedNoRT)))}")
    print()

    print("Actors never matched against webIsolated or web remoteTypes:")
    print(f"With remoteTypes: {actorsRemoteTypesString(otherRT)}")
    print()
    print(f"Without remoteTypes: {actorsRemoteTypesString(otherNoRT)}")
    print()

    print(f"Number of actors loaded into webIsolated processes: {len(webIso)}")
    print()
    print(f"Actors loaded into web processes but not webIsolated: {", ".join(sorted(list(web)))}")

    #print()
    #for a in webIso:
    #    print(f"WWW {", ".join(sorted(list(remoteTypes[a])))}\t{a}")