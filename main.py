import logging
import pickle
import boto3

import pandas as pd

from article_parser import get_article

FIRST_ARTICLE_ID = 768040
ARTICLES_TO_COLLECT = 20000

BUCKET = ""
PATH_TEMPLATE = ""
COLUMNS = ['id', 'title', 'text', 'time', 'hubs', 'tags']


_LOG = logging.getLogger()
_LOG.setLevel(logging.INFO)
_LOG.addHandler(logging.StreamHandler())

session = boto3.session.Session(profile_name='habr')
s3 = session.client(
    service_name='s3',
    endpoint_url='https://storage.yandexcloud.net'
)


def save_results(df, year):
    path = PATH_TEMPLATE.format(year)
    with open(path, 'wb') as f:
        f.write(pickle.dumps(df))
    
    data = pickle.dumps(df)
    s3.put_object(Bucket=BUCKET, Key=path, Body=data)


def get_year(ts):
    parts = ts.split(' ')
    if len(parts) < 5:
        return None

    year = parts[4] if parts[4] != '' else '2023'
    if not year.isdigit():
        return None
    
    return year

def main():
    _LOG.info("Starting to collect data")

    data = pd.DataFrame(columns=COLUMNS)

    errors = 0
    successes = 0

    error_streak = 0

    year = None

    article_id = FIRST_ARTICLE_ID
    i = 0
    while article_id > 0:
        if i % 1000 == 0 and year:
            _LOG.info("Current stats: {} errors, {} successes".format(errors, successes))
            _LOG.info("Creating backup of results")
            save_results(data, year)
            _LOG.info("Results saved")
        i += 1

        cur_article = get_article(article_id, _LOG)
        article_id -= 1
        if cur_article:
            if len(data) < ARTICLES_TO_COLLECT:
                data.loc[data.shape[0]] = cur_article
            else:
                # we collected enough articles for this year
                article_id -= 1001
            
            successes += 1
            error_streak = 0
        else:
            errors += 1
            error_streak += 1

            if error_streak > 100:
                _LOG.warning('Got {} errors in row, radically changing article id'.format(error_streak))
                article_id -= 10001
                error_streak = 0

            continue
        
        cur_year = get_year(cur_article['time'])
        if cur_year is None:
            _LOG.warning('Cannot parse year from article ts {}'.format(cur_article['time']))
            continue
        
        if year is None:
            year = cur_year
        elif year != cur_year:
            _LOG.info("Year changed: {} -> {}".format(year, cur_year))
            if len(data) > 10:
                save_results(data, year)
            data = pd.DataFrame(columns=COLUMNS)
            year = cur_year



if __name__ == "__main__":
    main()
