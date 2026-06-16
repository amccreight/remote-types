#!/usr/bin/python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import re

# Analyze the condensed remote type logs and summarize the output in various
# formats, including CSV.

registeredRe = re.compile("^I/JSActorService registered [^ ]+ '([^']+)': {((?: parent,)?)((?: child,)?)((?: remoteTypes,)?) }")
matchRe = re.compile("^I/JSActorService JSActor '([^']+)' matched remoteType '([^']+)'$")

def parseFile(fileName):
    actors = {}
    actorRemoteTypes = {}

    with open(fileName, "r") as fi:
        for l in fi:
            m = registeredRe.match(l)
            if m:
                actor = m.group(1)
                hasParent = len(m.group(2)) > 0
                hasChild = len(m.group(3)) > 0
                hasRemoteTypes = len(m.group(4)) > 0
                actors[actor] = (hasParent, hasChild, hasRemoteTypes)
                continue
            m = matchRe.match(l)
            assert m
            actor = m.group(1)
            remoteType = m.group(2)
            actorRemoteTypes.setdefault(actor, set([])).add(remoteType)

    return [actors, actorRemoteTypes]

# Helpers for actor registration data.
def hasParent(a):
    return a[0]

def hasChild(a):
    return a[1]

def hasRemoteType(a):
    return a[2]


def analyzeNeverMatched(actors, actorRemoteTypes):
    neverMatched = {
        True: set([]),
        False: set([]),
    }
    for a in actors.keys():
        if a in actorRemoteTypes:
            continue
        if hasRemoteType(actors[a]):
            neverMatched[True].add(a)
        else:
            neverMatched[False].add(a)

    return neverMatched


# actorRemoteTypes maps actor names to the remote types they were seen with.
# This function splits actors into one of four buckets, with decreasing order
# of precedence.
def analyzeRemoteTypes(actors, actorRemoteTypes):
    remoteTypeBuckets = {
        "webIsolated": set([]),
        "web": set([]),
        "otherRT": set([]),
        "otherNoRT": set([]),
    }
    for a, rts in actorRemoteTypes.items():
        if "webIsolated" in rts:
            remoteTypeBuckets["webIsolated"].add(a)
            assert not hasRemoteType(actors[a]) or a == "TestWindow" or a == "TestProcessActor"
            continue
        if "web" in rts:
            remoteTypeBuckets["web"].add(a)
            assert not hasRemoteType(actors[a]) or a == "TestProcessActor"
            continue
        assert a in actors
        if hasRemoteType(actors[a]):
            remoteTypeBuckets["otherRT"].add(a)
        else:
            remoteTypeBuckets["otherNoRT"].add(a)

    return remoteTypeBuckets


def csvRemoteTypes(actorRemoteTypes, rtOrder, a):
    rts = set(["web" if rt.startswith("web") else rt for rt in actorRemoteTypes[a]])
    return ", ".join(["Y" if rt in rts else "" for rt in rtOrder])

def fullCSV(actorRemoteTypes, neverMatched, remoteTypeBuckets):
    allRemoteTypes = set([])
    rtCounts = {}
    for a, rts in actorRemoteTypes.items():
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
    for a in sorted(list(neverMatched[False])):
        print(a)
    print("Never matched (remoteTypes)")
    for a in sorted(list(neverMatched[True])):
        print(f"{a}, Y")

    # Never web actors.
    print("Never web (no remoteTypes)")
    for a in sorted(list(remoteTypeBuckets["otherNoRT"])):
        print(f"{a}, , {csvRemoteTypes(actorRemoteTypes, rtOrder, a)}")

    print("Never web (remoteTypes)")
    for a in sorted(list(remoteTypeBuckets["otherRT"])):
        print(f"{a}, Y, {csvRemoteTypes(actorRemoteTypes, rtOrder, a)}")

    print("Sometimes web")
    for a in sorted(list(remoteTypeBuckets["web"].union(remoteTypeBuckets["webIsolated"]))):
        print(f"{a}, {"Y" if hasRemoteType(actors[a]) else ""}, {csvRemoteTypes(actorRemoteTypes, rtOrder, a)}")


# This prints out the actors seen with web content remote types on the first line,
# and with non web content remote types on the second line. This is intended to be
# used as input to *_safefor.py scripts.
def seenInWeb(actorRemoteTypes):
    seenInWeb = set([])
    notSeenInWeb = set([])

    for a, rts in actorRemoteTypes.items():
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


def actorsRemoteTypesString(actorRemoteTypes, actors):
    return ", ".join([f"{a} ({", ".join(sorted(list(actorRemoteTypes[a])))})" for a in actors])

def actorSummary(actorRemoteTypes, neverMatched, remoteTypeBuckets):
    print("Never matched actors:")
    print(f"  With remoteTypes: {", ".join(sorted(list(neverMatched[True])))}")
    print(f"  Without remoteTypes: {", ".join(sorted(list(neverMatched[False])))}")
    print()

    print("Actors never matched against webIsolated or web remoteTypes:")
    print(f"With remoteTypes: {actorsRemoteTypesString(actorRemoteTypes, remoteTypeBuckets["otherRT"])}")
    print()
    print(f"Without remoteTypes: {actorsRemoteTypesString(actorRemoteTypes, remoteTypeBuckets["otherNoRT"])}")
    print()

    print(f"Number of actors loaded into webIsolated processes: {len(remoteTypeBuckets["webIsolated"])}")
    print()
    print(f"Actors loaded into web processes but not webIsolated: {", ".join(sorted(list(remoteTypeBuckets["web"])))}")

    #print()
    #for a in webIso:
    #    print(f"WWW {", ".join(sorted(list(remoteTypes[a])))}\t{a}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Summarize JS actor remote type information.")
    parser.add_argument("file_name",
                        help="Condensed logging filed.")
    parser.add_argument("--csv", action="store_true",
                        help="Write output in CSV format.")
    parser.add_argument("--seen-in-web", action="store_true",
                        help="Output actors that were and were not seen in web processes; for the safefor scripts.")
    args = parser.parse_args()

    # Load the file and do some analysis.
    [actors, actorRemoteTypes] = parseFile(args.file_name)
    neverMatched = analyzeNeverMatched(actors, actorRemoteTypes)
    remoteTypeBuckets = analyzeRemoteTypes(actors, actorRemoteTypes)

    if args.csv:
        fullCSV(actorRemoteTypes, neverMatched, remoteTypeBuckets)
    elif args.seen_in_web:
        seenInWeb(actorRemoteTypes)
    else:
        actorSummary(actorRemoteTypes, neverMatched, remoteTypeBuckets)
