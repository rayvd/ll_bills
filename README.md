# ll_bills
A simple script to notify on balance due for City of Loma Linda utilities.  Why?  Just for fun mainly but also because the city doesn't support auto pay and rather than needing to log in to the site to check for a balance I just want to be notified.

## Requirements

* Python 2.7+ (we make use of a dict comprehension -- otherwise this might run fine on 2.6+)
* *nix environment of some sort.  It might work on Windows, but I didn't test it there.  See Notes below on email server.
* lxml
* texttable
* requests

## Usage

1. Copy the config file to ll_bills.conf and modify as appropriate.  It should reside in the same directory as the script.
2. Run the script

If all goes well, you'll receive an email similar to the following:

```
Account     Name               Balance
======================================
999999999   A NAME             $50.00
999999998   ANOTHER NAME        $5.00
```

I add to cron to run once every 24 hours.

## Notes

* Notifications happen via email using smtplib.  We aren't too sophisticated and don't give any options for providing username or password though you can override the SMTP server via the config file if you aren't running one locally.
