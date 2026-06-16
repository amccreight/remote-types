Log analyzer and updater for Firefox remote types.

`condense.py`: This script is run on the raw log files when MOZ_LOG
for JSActorService has been enabled, to eliminate all of the random
test log stuff we don't care about and all of the redundancy.

`rt.py`: This script performs various analyses of the condensed
remote types log.

Example of running `big_safefor.py`:

```
python3 big_safefor.py seenweb.txt ~/firefox
```

Example of running `little_safefor.py`:

```
python3 little_safefor.py seenweb.txt reg_files.txt ~/firefox
```

`seenweb.txt` is a file where the first line is the list of actors that have been seen in
web content processes, and the second line is a list of actors that haven't.

`reg_files.txt` is a list of files that contain either `ChromeUtils.registerWindowActor` or
`ChromeUtils.registerProcessActor`.
