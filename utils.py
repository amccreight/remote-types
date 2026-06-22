#!/usr/bin/python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

manual = {}
manualWeb = [
    "ExtFind",
    "LayoutDebug",
    "SpeechDispatcher",
    "SwitchDocumentDirection",
    # Only seen in parent during testing but maybe it is used in web?
    "LinkPreview",
    # These are used in perf tests and I assume are used in web processes.
    "DampLoad",
    "TalosTabSwitch",
    # Used in the test_allowJavascript.js XPCShell test.
    "AllowJavascript",
    # Needed for use with staging server.
    "TPSFxAAutofill",
    # Used by head_service_worker.js for xpcshell tests.
    "TestWorkerWatcher",
    # Used in Android tests by test-api.js.
    "TestSupport",
    "TestSupportProcess",
]
manualNonWeb = [
    "AboutPDF",
    "AISmartBar",
    "HPKEConfigManager",
    "MozCachedOHTTP",
    "MozNewTabRemoteRendererProtocol",
    "Urlbar",
]
# GeckoViewStartup.sys.mjs has a bunch of actors. I wasn't able to get logging
# to work on Android but they look like they are all needed for web processes,
# and I couldn't find any Android-specific actors with a remoteTypes declaration.
manualAndroid = [
    "GeckoViewPermissionProcess",
    "GeckoViewPush",
    "LoadURIDelegate",
    "GeckoViewPermission",
    "GeckoViewPrompt",
    "GeckoViewFormValidation",
    "GeckoViewPdfjs",
]
for a in manualWeb:
    manual[a] = True
for a in manualNonWeb:
    manual[a] = False
for a in manualAndroid:
    manual[a] = True

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
    if len(actors) == 0:
        return

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
