# Overview

Arxiv filter is similar to the standard arxiv email digests, but allows you to filter using keywords so that the email digests are significantly shorter. This is useful if you want to target a subset of a category (e.g., not all of cs.AI), and filter by areas of research (e.g, "reinforcement learning"), authors (e.g., "Yann LeCun"), or some other filter keyword.

# Installation

You should install this on a machine that is always on and has internet access. The installation has been tested on Ubuntu 16.04, but should be easy to replicate on other Unix systems. The installation process should take less than 10 minutes.

#### Choose categories and keywords

Arxiv filter works by finding all articles that
1. Were submitted in the past day
2. Are in one of the categories listed in categories.txt
3. Have at least one of the keywords listed in keywords.txt in either the title, author list, or abstract

You should change categories.txt and keywords.txt based on your interests. (Note: capitalization does not matter for keywords.)

#### Setup Mailgun

We use mailgun in order to send the arxiv filter digests.

Create a free account at [mailgun](https://www.mailgun.com/). You get 10,000 emails per month for free. Do not enter any credit card information if asked for.

Log in and click on "Domains" in the top menu. One sandbox will already exist, click on it, and do the following:
1. Copy the sandbox name into mailgun-sandbox-name.txt
2. Copy the API key into mailgun-api-key.txt
3. Click on "Manage Authorized Recipients" and add your email account. Also add your email account to mailgun-email-recipient.txt

Note: do not keep your mailgun sandbox or api key on github or any other publicly accessible place. Mailgun will notice it and disable your account.

#### Setup the script

Run the following to install the necessary python libraries:
```
$ sudo pip install datetime pytz requests arxiv
```
You need to use sudo because the system python installation will be used.

Next, we want the script to be called once a day. Edit crontab by running
```
$ sudo crontab -e
```
and add the following line
```
5 0 * * * /usr/bin/python2 /path/to/arxiv-filter/run.py
```
which will run the script once a day at 12:05am.

If you want to immediately test if the installation works, do
```
$ /usr/bin/python2 /path/to/arxiv-filter/run.py
```
(Note: arxiv filter searches over submissions from the past week and---after filtering---only emails you submission that it has not sent you before. If you want to start from scratch, delete the file previous_arxivs.txt)
