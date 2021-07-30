# Importação dos Pacotes
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import settings

def save_review_urls(urlsdict):
    review_urls_df = pd.DataFrame(urlsdict.items(), columns=['review_url','collected'])
    review_urls_df.to_csv(settings.DATA_PATH + "review_urls.csv", index = False, header = True, mode='w+')
        
def load_review_urls():
    review_urls_df = pd.read_csv(settings.DATA_PATH + "review_urls.csv")
    return {row['review_url']:row['collected'] for i,row in review_urls_df.iterrows()}

def main():
    # Define sessão, cabeçalho 
    session = requests.Session()
    headers = {'User-Agent': settings.USER_AGENT}

    # Variáveis para coleta dos links
    base_url = 'https://www.winemag.com/wine_review-sitemap{}.xml'
    files_to_harvest = 150 # Quantidade de listas de URLs que serão coletadas
    list_urls =[]

    # Para cada requisição enviada ao site winemag.com é retornado um xml. A cada iteração a lista list_urls é acrescida das URLS
    # extraídas de cada arquivo após tratamento/"parseamento" em objeto BeautifulSoup.
    for i in range(files_to_harvest):
        sitemap_url = base_url.format(i + 1)
        r = session.get(sitemap_url, headers=headers)
        print('\rColetando URL: {}'.format(sitemap_url), end='')
        soup = BeautifulSoup(r.text, 'lxml-xml')
        list_urls.extend([url.text for url in soup.find_all('loc')])
        if settings.DELAY:
            time.sleep(settings.CRAW_DELAY)

    # Salva a lista de URLs em um arquivo csv e seta o status de coleta para Falso e fecha a sessão
    save_review_urls(dict.fromkeys(list_urls, False))
    session.close()

if __name__ == '__main__':
    main()