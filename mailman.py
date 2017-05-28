#!/usr/bin/env python
# -*- coding: cp1252 -*-

"""Mailingliste der `KSG Ilmenau <http://www.ksg-ilmenau.de>`_"""

from __future__ import unicode_literals

import imaplib
import smtplib
import email
from email.utils import getaddresses
import re
import json
from json import loads
from requests import post as POST
import copy

import getopt
import sys


ENVID = 'listingErrorEishi0vei6ahbeeg'

jsonfile = 'mail.json'
globalSpamScore = 2
verbose = False

options, remainder = getopt.gnu_getopt(sys.argv[1:], 'j:s:v', ['jsonfile=',
															 'verbose',
															 'spamscore=',
															 ])

for opt, arg in options:
	if opt in ('-s', '--spamscore'):
		globalSpamScore = int(arg)
	elif opt in ('-v', '--verbose'):
		verbose = True
	elif opt in ('-j', '--jsonfile'):
		jsonfile = str(arg)

if verbose:
	print 'SPAMSCORE   :', globalSpamScore
	print 'VERBOSE	 :', verbose
	print 'OUTPUT	  :', jsonfile
	print 'REMAINING   :', remainder

# sys.exit("debug schluss")

class SpamCheck():

	postmark_spamcheck_url = "http://spamcheck.postmarkapp.com/filter"

	def postmark_spamcheck(self, message, options):
		data = {'email': message, 'options': options}
		result = POST(self.postmark_spamcheck_url, data)
		result.raise_for_status()
		content = loads(result.content)
		if 'error' in content:
			raise Exception(content['message'])
		return content

	def GetScore(self, email):
		results = self.postmark_spamcheck(email, "short")
		if results['success']:
			return results['score']
		else:
			return 0

	def GetReport(self, email):
		results = self.postmark_spamcheck(email, "long")
		return results['report']


def removekey(d, key):
	r = dict(d)
	del r[key]
	return r


def move2spam(data):
	if data == "":
		return
	email_ids = data.split(' ')
	for email_id in email_ids:
		mail.uid("COPY", email_id, "Spam")
		mail.uid("STORE", email_id, "+FLAGS.SILENT", "(\\Deleted)")


def move2large(data):
	if data == "":
		return
	email_ids = data.split(' ')
	for email_id in email_ids:
		print "id to large: " + email_id
		mail.uid("COPY", email_id, "TooLarge")
		mail.uid("STORE", email_id, "+FLAGS.SILENT", "(\\Deleted)")


def move2archive(data):
	if data == "":
		return
	email_ids = data.split(' ')
	for email_id in email_ids:
		mail.uid("STORE", email_id, "+FLAGS.SILENT", "(\\Seen)")
		mail.uid("COPY", email_id, "Archive")
		mail.uid("STORE", email_id, "+FLAGS.SILENT", "(\\Deleted)")


# Datenbank
with open(jsonfile) as data_file:
	data = json.load(data_file)

mail = imaplib.IMAP4_SSL(data["config"]["IMAP"]["HOST"])
mail.login(
	data["config"]["IMAP"]["USERNAME"],
	 data["config"]["IMAP"]["PASSWORD"])

post_ausgang = smtplib.SMTP(data["config"]["SMTP"]["HOST"], 587)
post_ausgang.ehlo()
post_ausgang.starttls()
post_ausgang.ehlo

if('USERNAME' in data["config"]["SMTP"]):
	post_ausgang.login(
	data["config"]["SMTP"]["USERNAME"],
	 data["config"]["SMTP"]["PASSWORD"])

mail.select("INBOX")  # connect to inbox.

# SPAM aussortieren

result, [spamdata] = mail.uid(
	'search', None, 'HEADER Content-Type multipart/report HEADER Content-Type report-type=delivery-status')
move2spam(spamdata)
if ('SPAM' in data["config"]):
	for mailaddress in data["config"]["SPAM"]:
		result, [spamdata] = mail.uid(
			'search', None, '(HEADER From "'+mailaddress+'")')
		move2spam(spamdata)
		result, [spamdata] = mail.uid(
			'search', None, '(HEADER To "'+mailaddress+'")')
		move2spam(spamdata)
		result, [spamdata] = mail.uid(
			'search', None, '(HEADER Cc "'+mailaddress+'")')
		move2spam(spamdata)

# Search to large mails
result, [largedata] = mail.uid('search', None, '(LARGER 2000000)')
move2large(largedata)

# Spam aussortieren
mail.expunge()

data = removekey(data, "config")

def prepare_mail(msg, id_):
	# Lösche einige Header
	del msg["X-UI-Out-Filterresults"]
	del msg["X-Provags-ID"]
	del msg["DKIM-Signature"]
	del msg["X-Google-DKIM-Signature"]
	del msg["X-Gm-Message-State"]
	del msg["Precedence"]
	
	msg.add_header("Precedence", "list")
	msg.add_header("List-ID", id_)
	msg.add_header("Delivered-To", id_)
	msg.add_header("List-Unsubscribe", "mailto:"+data[id_]["options"]["admin"])

	if(msg.has_key("Subject")):
		msg.replace_header("Subject", "[" + data[id_]["options"]["subject"] + "] " + re.sub(
			r"\s*" + re.escape("[" + data[id_]["options"]["subject"] + "]"), "", msg["Subject"]))
	else:
		msg.add_header(
	"Subject",
	 "[" + data[id_]["options"]["subject"] + "] no subject")

	if(msg.has_key("Return-Path")):
		msg.replace_header("Return-Path", data[id_]["options"]["admin"])
	else:
		msg.add_header("Return-Path", data[id_]["options"]["admin"])
	
	if(msg.has_key("Errors-To")):
		msg.replace_header("Errors-To", data[id_]["options"]["admin"])
	else:
		msg.add_header("Errors-To", data[id_]["options"]["admin"])
	
	if(msg.has_key("Reply-To")):
		msg.replace_header("Reply-To", id_)
	else:
		msg.add_header("Reply-To", id_)
	
	if(msg.has_key("ENVID")):
		msg.replace_header("ENVID", ENVID)
	else:
		msg.add_header("ENVID", ENVID)
	
	msg.replace_header("Message-ID", re.sub(r'@.*$', '', msg["Message-ID"], flags=re.IGNORECASE) +"@ksg-ilmenau.de>")
		
	return msg
	

def list_found(list_,msg,recipient):
	# Geschlossene Liste?
	if "closed" == list_["options"]["type"]:
		all_froms = getaddresses(msg.get_all('from', []))
		closed = True
		lastfrom = ""
		for from_ in all_froms:
			if (from_[1].lower() in list_["members"]) or (from_[1].lower() in list_["alias"]):
				closed = False
			lastfrom = from_[1].lower()
		if closed:
			# Warnmail schicken
			warnmail = "From: "+recipient.lower()+"\n"
			warnmail += "To: "+lastfrom+"\n"
			warnmail += "Presedence: bulk\n"
			warnmail += "Subject: Keine Berechtigung\n"
			warnmail += "\n"
			warnmail += "Du hast nicht die Berechtigung um auf dieser Liste zu schreiben.\n"
			post_ausgang.sendmail(recipient.lower(), lastfrom, warnmail)
			return(False)
	newMsg = prepare_mail(msg, recipient.lower())

	if verbose:
		print newMsg.as_string()
	
	post_ausgang.sendmail(recipient.lower(), list_["members"], newMsg.as_string())
	return(True)

spamchecker = SpamCheck()

result, liste = mail.uid('search', None, 'ALL')
for mList in liste[0].split(" "):
	if mList == "":
		continue

	localdata = copy.deepcopy(data)
	typ, maildata = mail.uid('fetch', mList, '(RFC822)')
	spamScore = float(spamchecker.GetScore(maildata[0][1]))
	if spamScore > globalSpamScore:
		print maildata[0][1]
		print spamchecker.GetReport(maildata[0][1])
		move2spam(mList)
		continue
	msg = email.message_from_string(maildata[0][1])
	# Teste, ob die Nachricht an uns geschickt wurde und an welche Liste
	tos = msg.get_all('to', [])
	ccs = msg.get_all('cc', [])
	resent_tos = msg.get_all('resent-to', [])
	resent_ccs = msg.get_all('resent-cc', [])
	all_recipients = getaddresses(tos + ccs + resent_tos + resent_ccs)
	for recipient in all_recipients:
		if verbose:
			print recipient
		if (localdata.has_key(recipient[1].lower())):
			if (list_found(localdata[recipient[1].lower()], msg, recipient[1])):
				del localdata[recipient[1].lower()]
	received = msg.get_all("received",[])
	for r in received:
		for k in localdata.keys():
			print k.lower()
			print r.lower()
			if(k.lower() in r.lower()):
				if(list_found(localdata[k.lower()],msg,k.lower())):
					del localdata[k.lower()]
	# Lösche die Nachricht
	move2archive(mList)

mail.expunge()
mail.close()
mail.logout()
post_ausgang.quit()
