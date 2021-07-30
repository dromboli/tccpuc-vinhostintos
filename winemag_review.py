#Importação dos pacotes
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time, logging
from datetime import datetime
import settings, winemag_sitemap

def extract_review_data(html, url):   
    """[summary]

    Args:
        html (bytes): Página HTML em formato bytes.
        url (string): URL do Review. 

    Returns:
        review_dict: dicionário com os dados de atributos do review extraídos do HTML 
    """    
    soup = BeautifulSoup(html, 'lxml')
    review_dict = dict()
    
    # Título do vinho está localizado na tag <h1> da <div> de classe "header__title"
    review_dict['Title'] = soup.find('div', class_='header__title').h1.text.strip()

    # <div> com id "review-gate" contém os demais dados alvo
    review_gate = soup.find('div', id='review-gate')
    # Descrição do vinho está contida no parágrafo de classe description
    review_dict['Description'] = review_gate.find('p', class_='description').contents[0].strip()
    # Nome do provador está localizado na tag <span> de classe "taster-area"
    review_dict['Taster'] = review_gate.find('span', class_='taster-area').text.strip() if(
                              review_gate.find('span', class_='taster-area')) else ''  
    # A nota atribuída ao vinho localiza-se na tag <div> de classe 'info medium-9 columns rating'
    review_dict['Rating'] = review_gate.find('div', class_='info medium-9 columns rating').text.strip()

    # Coleta dos dados de preço, designação, variedade, indicação geográfica e vinícula; se existirem no review
    review_dict['Price'] = soup.find('span',text='Price').findNext('div').findNext('span').findNext('span').contents[0].strip(',') if (
                            soup.find('span',text='Price').findNext('div').findNext('span').findNext('span')) else ''
    review_dict['Designation'] = soup.find('span',text='Designation').findNext('div').text.strip() if (
                                    soup.find('span',text='Designation')) else ''
    review_dict['Variety'] = soup.find('span',text='Variety').findNext('div').text.strip() if (
                                soup.find('span',text='Variety')) else ''
    review_dict['Appellation'] = soup.find('span',text='Appellation').findNext('div').text.strip() if (
                                    soup.find('span',text='Appellation')) else ''
    review_dict['Winery'] = soup.find('span',text='Winery').findNext('div').text.strip() if (
                                soup.find('span',text='Winery')) else ''

    # Coleta de dados de teor alcoólico, tamanho da garrafa e tipo de uva; se existirem no review
    review_dict['Alcohol'] = soup.find('span',text='Alcohol').findNext('div').text.strip() if (
                                soup.find('span',text='Alcohol')) else ''
    review_dict['Bottle Size'] = soup.find('span',text='Bottle Size').findNext('div').text.strip() if (
                                    soup.find('span',text='Bottle Size')) else ''
    review_dict['Category'] = soup.find('span',text='Category').findNext('div').text.strip() if (
                                soup.find('span',text='Category')) else ''
    
    review_dict['URL'] = url
    return review_dict

def save_review_collected(reviewdict):
    collected_df = pd.DataFrame(reviewdict)
    dtstring = datetime.now().strftime("%Y%m%d%H%M%S")
    collected_df.to_csv(settings.DATA_PATH + settings.REVIEWS_FILENAME + "{}.csv".format(dtstring), index = False, header = True)

def main():
    # Define sessão, cabeçalho 
    session = requests.Session()
    headers = {'User-Agent': settings.USER_AGENT}

    review_urls = winemag_sitemap.load_review_urls()
    review_collected = []
    i = 1
    total = len(review_urls)
    for url, status in review_urls.items(): 
        if status == True:  # Se a página já foi coletada retorna ao for
            i+=1
            continue
        # Requisita página do review ao servidor e imprime status
        try:
            r = session.get(url, headers=headers)
            
            # Extrai dados do review se acesso foi bem sucedido e atualiza status
            if r.status_code == 200:
                logging.info('Coletando URL #{} de {}. Status Code: {}'.format(i, total, r.status_code))
                review_collected.append(extract_review_data(r.content, url))
                review_urls[url] = True
            else:
                logging.warning('Problema ao requisitar a URL #{}: {}. Status Code: {}'.format(i, url, r.status_code))
        except Exception:
            logging.exception('Erro ao coletar URL #{}: {}'.format(i, url))
            
        if i % settings.MAX_REVIEW_PER_FILE == 0: #Salva o arquivo de url/status e as páginas coletadas a cada 250 iterações
            winemag_sitemap.save_review_urls(review_urls)
            save_review_collected(review_collected)
            review_collected = []

        i+=1

        if settings.DELAY:
            time.sleep(settings.CRAW_DELAY)

    session.close()

    # Salva o arquivo de url/status e as páginas coletadas
    if review_collected:
        winemag_sitemap.save_review_urls(review_urls)
        save_review_collected(review_collected)

    logging.info('{} URLs de {} URLs coletadas com sucesso.'.format(sum(1 for r in review_urls if review_urls[r]), total))

if __name__ == '__main__':
    main()