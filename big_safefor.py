#!/usr/bin/python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
from pathlib import Path
import re

# Hacky parser for the big actor registry files.
# * browser/components/DesktopActorRegistry.sys.mjs
# * toolkit/modules/ActorManagerParent.sys.mjs
# * mobile/shared/components/geckoview/GeckoViewStartup.sys.mjs


actorDeclRe = re.compile("^  ([^:]+): {$")

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

def fixBigActorDecls(seenWeb, fileName):
    inActorDecls = False
    currActorDecl = None
    actorAlreadySafe = False

    outFileName = fileName + ".tmp"
    anyChanged = False

    with open(fileName, "r") as fi, open(outFileName, "w") as fo:
        for l in fi:
            if not inActorDecls:
                if l == "let JSPROCESSACTORS = {\n":
                    inActorDecls = True
                elif l == "let JSWINDOWACTORS = {\n":
                    inActorDecls = True
                fo.write(l)
                continue
            if not currActorDecl:
                m = actorDeclRe.match(l)
                if m:
                    currActorDecl = m.group(1)
                elif l == "};\n":
                    inActorDecls = False
                fo.write(l)
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
                    if not actorAlreadySafe:
                        fo.write("    safeForUntrustedWebProcess: true,\n")
                        anyChanged = True
                else:
                    assert not actorAlreadySafe
                currActorDecl = None
                actorAlreadySafe = False
            elif l == "    safeForUntrustedWebProcess: true,\n":
                actorAlreadySafe = True
            fo.write(l)

    if anyChanged:
        print(f"Made changes to {fileName}")
        Path(outFileName).rename(fileName)
    else:
        print(f"No changes to {fileName}")
        Path(outFileName).unlink()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fix large JS actor registrations.")
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

    bigActorDeclFiles = [
        "browser/components/DesktopActorRegistry.sys.mjs",
        "toolkit/modules/ActorManagerParent.sys.mjs",
    ]

    # TODO: Add mobile/shared/components/geckoview/GeckoViewStartup.sys.mjs
    # Need to do a logging run on Android first.

    for f in bigActorDeclFiles:
        fixBigActorDecls(seenWeb, firefoxDir + f)
