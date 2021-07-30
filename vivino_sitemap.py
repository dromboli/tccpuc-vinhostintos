#Importação dos pacotes
import requests
from bs4 import BeautifulSoup
import pandas as pd
from gzip import decompress
import time, logging
import settings

def save_vivino_urls(urlsdict, filename):
    vivino_urls_df = pd.DataFrame(urlsdict.items(), columns=['wine_url','collected'])
    vivino_urls_df.to_csv(settings.DATA_PATH + filename, index = False, header = True, mode='w+')
        
def load_vivino_urls(filename):
    vivino_urls_df = pd.read_csv(settings.DATA_PATH + filename)
    return {row['wine_url']:row['collected'] for i,row in vivino_urls_df.iterrows()}

def get_filename_from_url(url):
    return url.replace('https://sitemap.vivino.com/nsm/', '').replace('_en-GB.xml.gz', '.csv')

def main():
    # Define sessão, cabeçalho 
    session = requests.Session()
    headers = {'User-Agent': settings.USER_AGENT}

    # Coleta dos links dos xml compactados (.gz) que contém a lista de URLs com as páginas de cada vinho
    sitemap_url = 'https://www.vivino.com/sitemap.xml'
    r = session.get(sitemap_url, headers=headers)
    soup = BeautifulSoup(r.text, 'lxml-xml')
    sitemap_files = [url.text for url in soup.find_all('loc') if ('/wines_' in url.text) and ('_en-GB.xml.gz' in url.text)]

    # Coleta os links das páginas dos vinhos contidos em cada um dos arquivos de sitemap
    for sitemap in sitemap_files:
        try:
            r = session.get(sitemap, headers=headers)
            if r.status_code == 200:
                logging.info('Coletando URL: {}'.format(sitemap))
                soup = BeautifulSoup(decompress(r.content), 'lxml')
                url_list = [url.text for url in soup.find_all('loc')]
                save_vivino_urls(dict.fromkeys(url_list, False), get_filename_from_url(sitemap))
            else:
                logging.warning('Problema ao coletar a URL: {}. Status Code: {}'.format(sitemap, r.status_code))
        except:
            logging.exception('Erro ao coletar a URL: {}'.format(sitemap))
        if settings.DELAY:
            time.sleep(settings.CRAW_DELAY)

    session.close()

if __name__ == '__main__':
    main()