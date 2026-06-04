#!/usr/bin/python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This takes two files as arguments. Each file is a list of actor names,
# separated by spaces, commas and newlines. If a line starts with "#" it is ignored.

# The script complains if the lists aren't the same. The goal is to check that
# all actors that were seen during testing have been seen by the rewriting script.

import argparse
from utils import manual

def actorFileParser(fileName):
    actors = []
    with open(fileName, "r") as f:
        for l in f:
            # Skip lines starting with '#'.
            if l[0] == "#":
                continue

            actors.extend([a2 for a1 in l.split() for a2 in a1.split(",")])

    actors = set(actors)
    if "" in actors:
        actors.remove("")
    return actors

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare logged and modified actors.")
    parser.add_argument("logged_actors_file",
                        help="File containing actors seen during logging.")
    parser.add_argument("modified_actors_file",
                        help="File containing actors seen during rewriting.")
    args = parser.parse_args()

    loggedActors = actorFileParser(args.logged_actors_file)
    modifiedActors = actorFileParser(args.modified_actors_file)

    s1 = loggedActors - modifiedActors
    if len(s1) == 0:
        print(f"Logged but not modified: none")
    else:
        print(f"Logged but not modified: {", ".join(sorted(list(s1)))}")

    s2 = modifiedActors - loggedActors
    actualModifiedButNotLogged = set([])
    for a in s2:
        if not a in manual:
            actualModifiedButNotLogged.add(a)
    s2 = actualModifiedButNotLogged
    if len(s2) == 0:
        print(f"Modified but not logged or in the manual list: none")
    else:
        print(f"Modified but not logged or in the manual list: {", ".join(sorted(list(s2)))}")