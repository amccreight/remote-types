#!/usr/bin/python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This script is about fixing up direct calls to ChromeUtils.registerWindowActor
# and ChromeUtils.registerProcessActor.

# First, create a list of all of the files that call the register actor
# methods.
# From the Firefox source directory:
#   rg -l "ChromeUtils.registerProcessActor" > /tmp/file1.txt
#   rg -l "ChromeUtils.registerWindowActor" > /tmp/file2.txt
# cat /tmp/file1.txt /tmp/file2.txt | sort | uniq > reg_files.txt

import argparse
import re
from utils import loadRemoteTypesFile, manual


registerRe = re.compile("^(\\s*)ChromeUtils.register([a-zA-Z]+)Actor\\((\"[^\"]+\"|[^\"]+), {$")

# XXX Need to make this echo the modified file to a tmp file, move it over.

# XXX Print out a list of actors we modified, saw but didn't modify etc.

# Some actors are registered using variable names instead of literals.
nameFixup = {
    ("browser_bug1622420.js", "ACTOR"): "Bug1622420",
    ("browser_fullscreen_api_fission.js", "actorName"): "FullscreenFrame",
    ("fxaccounts.sys.mjs", "AUTOFILL_ACTOR_NAME"): "TPSFxAAutofill",
    ("head_service_worker.js", "JS_ACTOR_NAME"): "TestWorkerWatcher",
    ("test_allowJavascript.js", "ACTOR"): "AllowJavascript",
    # This is a bit of a hack because actorName is also used for the actor
    # UserCharacteristicsCanvasRendering in this file, but they are both
    # used in web processes, so that's fine.
    ("UserCharacteristicsPageService.sys.mjs", "actorName"): "UserCharacteristicsWindowInfo",
}

ignoreFiles = set([
    # This file registers ASRouterNewTabMessage (which is non-web-content) via
    # TRAIN_HOPPING_COMPONENT_CONFIGURATIONS.actors.
    "browser/extensions/newtab/lib/ExternalComponentsFeed.sys.mjs",
    # These WebIDL files don't actually register actors.
    "dom/chrome-webidl/JSProcessActor.webidl",
    "dom/chrome-webidl/JSWindowActor.webidl",
    # These test do weird things and have been manually fixed up by the main patch.
    "dom/ipc/tests/JSProcessActor/browser_registerProcessActor.js",
    "dom/ipc/tests/JSProcessActor/head.js",
    "dom/ipc/tests/JSWindowActor/browser_registerWindowActor.js",
    "dom/ipc/tests/JSWindowActor/head.js",
    # This does something weird, so fix it manually.
    "devtools/server/actors/watcher/ParentProcessWatcherRegistry.sys.mjs",
    # This is the implementation used by mobile/shared/chrome/geckoview/geckoview.js,
    # which will be analyzed by big_safefor.py.
    "mobile/shared/modules/geckoview/GeckoViewActorManager.sys.mjs",
    # This is analyzed by big_safefor.py.
    "toolkit/modules/ActorManagerParent.sys.mjs",
])

def fixLittleActorDecls(seenWeb, baseFile, fileName):
    foundAny = False

    currActor = None
    safeFor = None
    endCurrActor = None
    actorAlreadySafe = False

    justTheFile = fileName.split("/")[-1]

    with open(baseFile + fileName, "r") as fi:
        for l in fi:
            m = registerRe.match(l)
            if m:
                foundAny = True
                assert currActor is None
                assert safeFor is None
                assert endCurrActor is None
                actorAlreadySafe = False

                indentWith = m.group(1)
                safeFor = indentWith + "  safeForUntrustedWebProcess: true,\n"
                endCurrActor = indentWith + "});\n"
                kind = m.group(2)
                assert kind == "Window" or kind == "Process"
                currActor = m.group(3)
                if currActor[0] == '"' and currActor[-1] == '"':
                    currActor = currActor[1:-1]
                else:
                    assert (justTheFile, currActor) in nameFixup, f"Unknown non-string actor {currActor} in {justTheFile}"
                    currActor = nameFixup[(justTheFile, currActor)]
                continue
            if currActor:
                if l == safeFor:
                    actorAlreadySafe = True
                elif l == endCurrActor:
                    okayForWeb = False
                    if currActor in manual:
                        if manual[currActor]:
                            okayForWeb = True
                    else:
                        assert currActor in seenWeb, f"Unknown actor {currActor} in {fileName}"
                        if seenWeb[currActor]:
                            okayForWeb = True
                    if okayForWeb:
                        if actorAlreadySafe:
                            print(f"ALREADY SAFEFOR: {currActor} in {justTheFile}")
                        else:
                            print(f"MATCHED: {currActor} in {justTheFile}: ==>{safeFor[:-1]}")
                    else:
                        assert not actorAlreadySafe
                        print(f"NOT WEB: {currActor} in {justTheFile}")
                    currActor = None
                    safeFor = None
                    endCurrActor = None

    # We should have found the end of an actor by the end of the file.
    assert currActor == None

    if foundAny:
        return

    assert fileName in ignoreFiles, f"Did not find any actor registrations in {fileName}"
    print("IGNORING: " + fileName)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fix individual JS actor registrations.")
    parser.add_argument("file_name",
                        help="File where first line is actors that have been "
                            "seen in web process during testing, and second "
                            "line is those that haven't")
    parser.add_argument("file_file_name",
                        help="File containing a list of files we should look at.")
    parser.add_argument("firefox_dir",
                        help="Root of Firefox source code directory.")
    args = parser.parse_args()

    firefoxDir = args.firefox_dir
    if not firefoxDir.endswith("/"):
        firefoxDir += "/"

    seenWeb = loadRemoteTypesFile(args.file_name)

    files = []
    with open(args.file_file_name, "r") as fi:
        for l in fi:
            assert len(l) > 2
            files.append(l[:-1])

    for f in files:
        fixLittleActorDecls(seenWeb, firefoxDir, f)

