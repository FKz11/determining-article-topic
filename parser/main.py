import logging
import pickle
import boto3

import pandas as pd

from article_parser import get_article

FIRST_ARTICLE_ID = 768040
ARTICLES_TO_COLLECT = 60000

BUCKET = "habr-hse"
PATH_TEMPLATE = "datasets/articles.pkl"
COLUMNS = ['id', 'title', 'text', 'time', 'hubs', 'tags']


_LOG = logging.getLogger()
_LOG.setLevel(logging.INFO)
_LOG.addHandler(logging.StreamHandler())

session = boto3.session.Session(profile_name='habr')
s3 = session.client(
    service_name='s3',
    endpoint_url='https://storage.yandexcloud.net'
)


def save_results(df):
    path = PATH_TEMPLATE
    with open(path, 'wb') as f:
        f.write(pickle.dumps(df))
    
    data = pickle.dumps(df)
    s3.put_object(Bucket=BUCKET, Key=path, Body=data)



def main():
    _LOG.info("Starting to collect data")

    data = pd.DataFrame(columns=COLUMNS)

    errors = 0
    successes = 0

    error_streak = 0

    article_id = FIRST_ARTICLE_ID
    i = 0
    while len(data) < ARTICLES_TO_COLLECT and article_id > 0:
        if i % 10000 == 0:
            _LOG.info("Current stats: {} errors, {} successes".format(errors, successes))
            _LOG.info("Creating backup of results")
            save_results(data)
            _LOG.info("Results saved")
        i += 1

        cur_article = get_article(article_id, _LOG)
        article_id -= 1
        if cur_article:
            data.loc[data.shape[0]] = cur_article
            
            successes += 1
            error_streak = 0
        else:
            errors += 1
            error_streak += 1

            if error_streak > 100:
                _LOG.warning('Got {} errors in row, radically changing article id'.format(error_streak))
                article_id -= 10001
                error_streak = 0
    
    save_results(data)
    

if __name__ == "__main__":
    main()
