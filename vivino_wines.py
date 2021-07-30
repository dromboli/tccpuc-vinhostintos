#Importação dos pacotes
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time, logging, json, sys
from datetime import datetime
import settings, vivino_sitemap

def get_wine_json(bytes):
    # A função localiza o texto do json contido em tag script entre as contantes STR_BGN e STR_END
    # E retorna o json obtido após conversão
    STR_BGN = 'PRELOADED_STATE__.winePageInformation = '
    STR_END = 'window.__PRELOADED_WINE_PAGE_VIEW_EVENTS' 

    soup = BeautifulSoup(bytes, 'lxml')
    scripts = soup.find_all('script')
    for script in scripts:
        if (script.string is not None) and (script.string.find(STR_BGN) != -1):
            json_string = script.string[script.string.find(STR_BGN) + len(STR_BGN):script.string.find(STR_END) - 4]
            return json.loads(json_string)

def get_wine_id(url):
    # Retorna o id do vinho contido na url no site (número na última parte da url)
    return url[url.rfind('/')+1:]

def validate_info(winej, tastej):
    # Critérios para validação: ter nota válida, ter safra com nota válida e possuir estrutura de sabor
    if (
        winej['wine']['has_valid_ratings'] == False or
        not ([vintage for vintage in winej['wine']['vintages'] if vintage['has_valid_ratings']]) or
        tastej['tastes']['structure'] == None
    ):
        return False
    else:
        return True

def extract_wine_data(winej, tastej, url):
    # Dados gerais do vinho
    wine_dict = {}
    wine_dict['id'] = winej['wine']['id']
    wine_dict['full_name'] = winej['vintage']['name']
    wine_dict['name'] = winej['wine']['name']
    wine_dict['type_id'] = winej['wine']['type_id']
    wine_dict['type'] = winej['vintage']['wine']['rank']['wine_type']['description'].partition('Rank within all ')[2]
    wine_dict['wine_region'] = winej['wine']['region']['name']
    wine_dict['winery'] = winej['wine']['winery']['name']
    wine_dict['winery_region'] = winej['wine']['winery']['region']['name']
    wine_dict['country'] = winej['wine']['winery']['region']['country']['name']
    wine_dict['ratings_count'] = winej['wine']['statistics']['ratings_count']
    wine_dict['ratings_average'] = winej['wine']['statistics']['ratings_average']
    wine_dict['alcohol'] = winej['wine']['alcohol']
    wine_dict['acidity'] = tastej['tastes']['structure']['acidity']
    wine_dict['fizziness'] = tastej['tastes']['structure']['fizziness']
    wine_dict['intensity'] = tastej['tastes']['structure']['intensity']
    wine_dict['sweetness'] = tastej['tastes']['structure']['sweetness']
    wine_dict['tannin'] = tastej['tastes']['structure']['tannin']
    wine_dict['url'] = url

    # Dados das safras
    vintages_list = []
    for vintage in winej['wine']['vintages']:
        if vintage['has_valid_ratings'] == True and vintage['year'] != 0:
            vintage_dict = {}
            vintage_dict['year'] = vintage['year']
            vintage_dict['id'] = vintage['id']
            vintage_dict['wine_id'] = wine_dict['id']
            vintage_dict['vintage_ratings_count'] = vintage['statistics']['ratings_count']
            vintage_dict['vintage_ratings_average'] = vintage['statistics']['ratings_average']
            vintages_list.append(vintage_dict)

    return (wine_dict, vintages_list)

def save_wine_information(winel, vintagel, tastel):
    dtstring = datetime.now().strftime("%Y%m%d%H%M%S")
    # Salva dados do vinho
    wine_df = pd.DataFrame(winel)
    wine_df.to_csv(settings.DATA_PATH + settings.WINES_FILENAME + "{}.csv".format(dtstring), index = False, header = True)
    # Salva dados das safras
    vintage = pd.DataFrame(vintagel)
    vintage.to_csv(settings.DATA_PATH + settings.VINTAGES_FILENAME + "{}.csv".format(dtstring), index = False, header = True)
    # Salva dados dos grupos de sabores
    taste_df = pd.DataFrame(tastel)
    taste_df.to_csv(settings.DATA_PATH + settings.TASTES_FILENAME + "{}.csv".format(dtstring), index = False, header = True)

def main():
    # Define sessão, cabeçalho 
    session = requests.Session()
    headers = {'User-Agent': settings.USER_AGENT,
                'Accept-Language': 'en-US,en;q=0.8,pt-BR;q=0.5,pt;q=0.3'}
    base_api_url = 'https://www.vivino.com/api/wines/{}/tastes'

    wines_filepath = sys.argv[1] #nome do arquivo de links passado por parâmetro na chamada ao script 
    vivino_urls = vivino_sitemap.load_vivino_urls(wines_filepath)

    wines_info, vintages_info, tastes_info = [],[],[]
    i = 1
    total = len(vivino_urls)

    for url, status in vivino_urls.items(): 
        if status in [True, 'True', 'Rejected']:  # Se a página já foi coletada retorna ao for
            i+=1
            continue     
        try:
            r = session.get(url, headers=headers)
            
            # Acessa pagina principal do vinho no site e extrai contéudo json contido na página
            if r.status_code == 200:
                logging.info('Coletando URL #{} de {}. Status Code: {}'.format(i, total, r.status_code))
                wine_json = get_wine_json(r.content) #Obtén json com os dados do vinho a partir da requisição

                if settings.DELAY:
                    time.sleep(settings.API_DELAY) 

                # Requisita complementares de sabor do vinho para a API do site
                t = session.get(base_api_url.format(get_wine_id(url)), headers=headers) 
                if t.status_code == 200:
                    logging.info('Coletando API/Tastes - URL #{} de {}. Status Code: {}'.format(i, total, t.status_code))
                    taste_json = t.json()

                    if validate_info(wine_json, taste_json): # Testa se dados obtidos são válidos (dados mínimos)
                        # Coleta dados dos json (vinho e sabores) e incrementa listas correspondentes
                        wine_info, vintage_info, taste_info = extract_wine_data(wine_json, taste_json, url)
                        wines_info.append(wine_info)
                        vintages_info.extend(vintage_info)
                        tastes_info.append(taste_info)
                        vivino_urls[url] = True  

                    else:
                        vivino_urls[url] = 'Rejected' 
                        logging.info('URL #{} - {} - Rejeitada'.format(i, url))            
                else:
                    logging.warning('Problema ao requisitar a URL (API/Tastes) #{}: {}. Status Code: {}'.format(i, url, t.status_code))
            else:
                logging.warning('Problema ao requisitar a URL #{}: {}. Status Code: {}'.format(i, url, r.status_code))
        except:
            logging.exception('Erro ao coletar URL #{}: {}'.format(i, url))

        #Salva o arquivo de url/status e as páginas coletadas a cada 250 iterações
        if i % settings.MAX_REVIEW_PER_FILE == 0 and wines_info: 
            vivino_sitemap.save_vivino_urls(vivino_urls, filename = wines_filepath)
            save_wine_information(wines_info, vintages_info, tastes_info)
            wines_info, vintages_info, tastes_info = [],[],[]

        i+=1
        if settings.DELAY:
            time.sleep(settings.CRAW_DELAY)


    session.close()

    # Salva o arquivo de url/status e as informações coletadas
    vivino_sitemap.save_vivino_urls(vivino_urls, filename = wines_filepath)
    if wines_info:
        save_wine_information(wines_info, vintages_info, tastes_info)

    logging.info('{} URLs de {} URLs coletadas com sucesso. {} URLs rejeitadas'.format(
        sum(1 for r in vivino_urls if vivino_urls[r]  in [True, 'True']), total,
        sum(1 for r in vivino_urls if vivino_urls[r] == 'Rejected')))


if __name__ == '__main__':
    main()