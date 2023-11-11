import requests
from bs4 import BeautifulSoup

ARTICLE_URL_TEMPLATE = 'https://habr.com/ru/articles/{}/'

HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}


def get_article(article_id, log):
    # выгрузка документа
    r = requests.get(ARTICLE_URL_TEMPLATE.format(article_id), headers=HEADERS)

    if r.status_code != 200:
        log.warning('Returned status code {} for article {}'.format(r.status_code, article_id))

    # парсинг документа
    soup = BeautifulSoup(r.text, 'html5lib') # instead of html.parser
    
    doc = {}
    doc['id'] = article_id
    if not soup.find("h1", {"class": "tm-title"}):
        # такое бывает, если статья не существовала или удалена
        return None
    else:
        doc['title'] = soup.find("h1", {"class": "tm-title"}).text
        doc['text'] = soup.find("div", {"id": "post-content-body"}).text
        doc['time'] = soup.find("span", {"class": "tm-article-datetime-published"}).text
        doc['hubs'] = "|".join(list(map(lambda s: s.text, soup.find_all('span', {'class': 'tm-publication-hub__link-container'}))))
        doc['tags'] = "|".join(list(map(lambda s: s.text, soup.find_all('a', {'class': 'tm-tags-list__link'}))))

    return doc