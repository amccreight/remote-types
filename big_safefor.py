#!/usr/bin/python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sys
import re

# Very hacky parser for the big actor registry files.
# * browser/components/DesktopActorRegistry.sys.mjs
# * toolkit/modules/ActorManagerParent.sys.mjs
# * mobile/shared/components/geckoview/GeckoViewStartup.sys.mjs

# cat seenweb.txt ~/firefox/browser/components/DesktopActorRegistry.sys.mjs | python3 big_safefor.py
#   where seenweb.txt is the seenInWeb() output of rt.py.


actorDeclRe = re.compile("^  ([^:]+): {$")

# XXX Need to echo the unchanged lines.

# To import extra data in the hackiest way possible, the first two lines of
# input are cat'd onto the file we're transforming
seenFirst = False
seenSecond = False
seenWeb = {}

manual = {}
manualWeb = [
    "AISmartBar",
    "ExtFind",
    "LayoutDebug",
    "SpeechDispatcher",
    "SwitchDocumentDirection",
    "LinkPreview", # Only seen in parent during testing but surely it is used in web?
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


inActorDecls = False
currActorDecl = None

for l in sys.stdin:
    if not seenFirst:
        # This is our set of remote types that have been seen in web processes during testing.
        for a in l.split():
            seenWeb[a] = True
        seenFirst = True
        # Don't echo this line.
        continue
    if not seenSecond:
        # This is our set of remote types that haven't been seen in web processes during testing.
        for a in l.split():
            seenWeb[a] = False
        seenSecond = True
        # Don't echo this line.
        continue
    if not inActorDecls:
        if l == "let JSPROCESSACTORS = {\n":
            inActorDecls = True
        elif l == "let JSWINDOWACTORS = {\n":
            inActorDecls = True
        print(l[:-1])
        continue
    if not currActorDecl:
        m = actorDeclRe.match(l)
        if m:
            currActorDecl = m.group(1)
        elif l == "};\n":
            inActorDecls = False
        print(l[:-1])
        continue
    if l == "  },\n":
        assert currActorDecl is not None
        okayForWeb = False
        if currActorDecl in manual:
            if manual[currActorDecl]:
                okayForWeb = True
        elif currActorDecl in seenWeb:
            if seenWeb[currActorDecl]:
                okayForWeb = True
        else:
            print(f"Unknown actor: {currActorDecl}")
            assert False
        if okayForWeb:
            print(f"    safeForUntrustedWebProcess: true,")
        currActorDecl = None
    print(l[:-1])



