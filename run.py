import os
import time
import re
from datetime import datetime 
from pytz import timezone
import requests
import arxiv


class Query(object):
    def __init__(self, query):
        self.date = datetime(*query['updated_parsed'][:6], tzinfo=timezone('GMT'))
        self.url = query['arxiv_url']
        self.title = query['title']
        self.authors = ', '.join(query['authors'])
        self.abstract = query['summary']
        self.date_str = query['published']
        self.id = 'v'.join(query['id'].split('v')[:-1])
        self.categories = [tag['term'] for tag in query['tags']]

    @property
    def is_recent(self):
        curr_time = datetime.now(timezone('GMT'))
        delta_time = curr_time - self.date
        assert delta_time.total_seconds() > 0
        return delta_time.days < 8

    def __hash__(self):
        return self.id

    def __str__(self):
        s = ''
        s += self.title + '\n'
        s += self.url + '\n'
        s += self.authors + '\n'
        s += ', '.join(self.categories) + '\n'
        s += self.date.ctime() + ' GMT \n'
        s += '\n' + self.abstract + '\n'
        return s.encode('utf-8')

class ArxivFilter(object):
    def __init__(self, categories, keywords, mailgun_sandbox_name, mailgun_api_key, mailgun_email_recipient):
        self._categories = categories
        self._keywords = keywords
        self._mailgun_sandbox_name = mailgun_sandbox_name
        self._mailgun_api_key = mailgun_api_key
        self._mailgun_email_recipient = mailgun_email_recipient

    @property
    def _previous_arxivs_fname(self):
        return os.path.join(os.path.dirname(os.path.realpath(__file__)), 'previous_arxivs.txt')
        
    def _get_previously_sent_arxivs(self):
        if os.path.exists(self._previous_arxivs_fname):
            with open(self._previous_arxivs_fname, 'r') as f:
                return set(f.read().split('\n'))
        else:
            return set()

    def _save_previously_sent_arxivs(self, new_queries):
        prev_arxivs = list(self._get_previously_sent_arxivs())
        prev_arxivs += [q.id for q in new_queries]
        prev_arxivs = list(set(prev_arxivs))
        with open(self._previous_arxivs_fname, 'w') as f:
            f.write('\n'.join(prev_arxivs))
        
    def _get_queries_from_last_day(self, max_results=10):
        queries = []

        # get all queries in the categories in the last day
        for category in self._categories:
            num_category_added = 0
            while True:
                new_queries = [Query(q) for q in arxiv.query(search_query=category, sort_by='submittedDate', start=num_category_added, max_results=max_results)]
                num_category_added += len(new_queries)
                queries += [q for q in new_queries if q.is_recent]

                if len(new_queries) == 0 or not new_queries[-1].is_recent:
                    break

        # get rid of duplicates
        queries_dict = {q.id: q for q in queries}
        unique_keys = set(queries_dict.keys())
        queries = [queries_dict[k] for k in unique_keys]

        # only keep queries that contain keywords
        queries = [q for q in queries if max([k in str(q).lower() for k in self._keywords])]

        # sort from most recent to least
        queries = sorted(queries, key=lambda q: (datetime.now(timezone('GMT')) - q.date).total_seconds())

        # filter if previously sent
        prev_arxivs = self._get_previously_sent_arxivs()
        queries = [q for q in queries if q.id not in prev_arxivs]
        self._save_previously_sent_arxivs(queries)
        
        return queries

    def _send_email(self, txt):
        request = requests.post(
                "https://api.mailgun.net/v3/{0}/messages".format(self._mailgun_sandbox_name),
                auth=("api", self._mailgun_api_key),
                data={"from": "arxivfilter@arxivfilter.com",
                      "to": [self._mailgun_email_recipient],
                      "subject": "ArxivFilter {0}".format(datetime.now(timezone('GMT')).ctime()),
                      "text": txt})

        print('Status: {0}'.format(request.status_code))
        print('Body:   {0}'.format(request.text))

    def run(self):
        queries = self._get_queries_from_last_day()
        queries_str = '\n-----------------------------\n'.join([str(q) for q in queries])
        for keyword in self._keywords:
            queries_str_insensitive = re.compile(re.escape(keyword), re.IGNORECASE)
            queries_str = queries_str_insensitive.sub('**' + keyword + '**', queries_str)
        queries_str = 'Categories: ' + ', '.join(self._categories) + '\n' + \
                      'Keywords: ' + ', '.join(self._keywords) + '\n\n' + \
                      '\n-----------------------------\n' + \
                      queries_str
        self._send_email(queries_str)

FILE_DIR = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(FILE_DIR, 'categories.txt'), 'r') as f:
    categories = [line.strip() for line in f.read().split('\n') if len(line.strip()) > 0]

with open(os.path.join(FILE_DIR, 'keywords.txt'), 'r') as f:
    keywords = [line.strip() for line in f.read().split('\n') if len(line.strip()) > 0]

with open(os.path.join(FILE_DIR, 'mailgun-sandbox-name.txt'), 'r') as f:
    mailgun_sandbox_name = f.read().strip()

with open(os.path.join(FILE_DIR, 'mailgun-api-key.txt'), 'r') as f:
    mailgun_api_key = f.read().strip()

with open(os.path.join(FILE_DIR, 'mailgun-email-recipient.txt'), 'r') as f:
    mailgun_email_recipient = f.read().strip()


af = ArxivFilter(categories=categories,
                 keywords=keywords,
                 mailgun_sandbox_name=mailgun_sandbox_name,
                 mailgun_api_key=mailgun_api_key,
                 mailgun_email_recipient=mailgun_email_recipient)
af.run()



