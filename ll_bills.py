#!/usr/bin/python
#
# The City of Loma Linda doesn't do auto-pay and I'm too forgetful to log in
# and check if I have a balance due.
#
# This script logs into the City of Loma Linda website and checks for any
# accounts with non-zero balances.  If it finds any, it sends an email
# reminding me.
#
# I almost certainly could have done this much more sipmly using cURL and
# grep, but it was an excuse to mess with lxml and HTML scraping.  And the way
# it's written handles multiple accounts flexibly.
#
# Copyright 2019 Ray Van Dolson (rayvd@bludgeon.org)
# Licensed under the Apache License, Version 2.0
#

import os
import re
import requests
import smtplib
import ConfigParser

from lxml import html
from decimal import Decimal
from texttable import Texttable
from email.mime.text import MIMEText

# Configuration file.  Should be in same directory as this script resides.
CONFIGFILE = "{}/ll_bills.conf".format(os.path.dirname(os.path.realpath(__file__)))

# The URL of the login page.
LOGIN_URL = "https://secure.lomalinda-ca.gov/OneStop/login.aspx"

# Generate notification only if balance exceeds this amount.  You can set this
# to a value less than zero for testing.
MINBALANCE = 0

def main():
    config = ConfigParser.ConfigParser()
    config.read(CONFIGFILE)

    # Initialize variables from configuration file.
    username = config.get('general', 'username')
    password = config.get('general', 'password')
    email_subject = config.get('general', 'email_subject')
    email_from = config.get('general', 'email_from')
    email_to = config.get('general', 'email_to')
    smtp_server = config.get('general', 'smtp_server')

    # Data structure to store output
    owed_table = {}

    # Let's retrieve the login page and grab the hidden form input variables.
    page = requests.get(LOGIN_URL)
    tree = html.fromstring(page.content)
    form = tree.xpath('//form[@id="Form1"]')[0]

    # Look for <input> elements with type=hidden.  Grab their names and values
    # and store in our form data dict.  This is a dict comprehension that is
    # available only in Python 2.7+.
    formdata = { i.name: i.value for i in form.xpath('.//input') if i.type == 'hidden' }

    # We still need to manually handle one more input.
    formdata['LoginControl1:OSLoginBN'] = 'Login'

    # Now add our username and password.
    formdata['LoginControl1:OSUserNameTB'] = username
    formdata['LoginControl1:OSPasswordTB'] = password

    # Set up our querystring.
    querystring = {'ReturnUrl': '/OneStop/default.aspx'}

    # The requests module can automatically follow the redirect from a
    # successful login.  We don't really do any graceful error handling here.
    page = requests.post(LOGIN_URL, data=formdata, allow_redirects=True, 
        params=querystring)

    # Grab our "root" and then find the structure with the information we
    # want.
    tree = html.fromstring(page.content)
    accounts = tree.xpath('//*[@id="AccountDetailsDG"]')[0]

    # Plan:
    #  - Iterate by child table element under AccountDetailsDG.
    #  - If we find BalanceDue > 0, gather display relevant account info

    for acct_table in accounts.xpath('.//table'):
        balance = acct_table.xpath(r".//span[re:match(@id, '.*BalanceDueLBL.*')]", 
            namespaces={"re": 'http://exslt.org/regular-expressions'})[0].text_content()
        owed = Decimal(re.sub(r'[^\d.]', '', balance))

        if owed > MINBALANCE:
            # Get the account number
            acct_num = acct_table.xpath(r".//span[re:match(@id, '.*AccountNumberLBL.*')]", 
                namespaces={"re": 'http://exslt.org/regular-expressions'})[0].text_content()

            # Initialize a dictionary for storing our results.
            owed_table[acct_num] = {}
            # Store the owed balance
            owed_table[acct_num]['balance'] = balance

            # Get the name on the account
            acct_name = acct_table.xpath(r".//span[re:match(@id, '.*AccountNameLBL.*')]", 
                namespaces={"re": 'http://exslt.org/regular-expressions'})[0].text_content()
            # Store the account name
            owed_table[acct_num]['acct_name'] = acct_name

    # If we have data to share, prep it and email it out.
    if len(owed_table.keys()) > 0:
        # Initiate a Texttable object for display
        t = Texttable(max_width=78)
        t.set_deco(Texttable.HEADER)
        t.set_cols_dtype(['t', 't', 'a'])
        t.set_cols_align(['l', 'l', 'r'])
        t.set_header_align(['l', 'l', 'l'])
        t.header(["Account", "Name", "Balance"])

        # Populate content.
        for x in owed_table.keys():
            t.add_row([ x, owed_table[x]['acct_name'], owed_table[x]['balance'] ])

        # Print the content to stdout
        output = t.draw()

        msg = MIMEText(output)
        msg['Subject'] = email_subject
        msg['From'] = email_from
        msg['To'] = email_to

        s = smtplib.SMTP(smtp_server)
        s.sendmail(email_from, [email_to], msg.as_string())
        s.quit()

if __name__ == '__main__':
    main()
