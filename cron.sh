#!/bin/sh

# Optionen:
# -v | --verbose
# Redet mehr, als einem lieb ist
# 
# -s | --spamscore = 2
# SpamScore, ab dem eine Mail als Spam klassifiziert werden soll
# Default: 2
# 
# -j | --jsonfile = mail.json
# Config-File für die Liste
# Default: mail.json
#
python mailman.py -j mail.json -s 2
