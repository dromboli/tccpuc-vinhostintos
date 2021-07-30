# Define constantes/configurações usadas
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0'
DELAY = True # Define se haverá delay entre as requisições enviadas ao servidor
CRAW_DELAY = 5 # Tempo (s) de espera  entre cada requisição enviada ao servidor
API_DELAY = 2 # Tempo de espera para chamada a API da Vivino após o carregamento da página principal
DATA_PATH = 'datasets/' # Caminho para a pasta de armazenamento dos datasets e outros arquivos correlatos

MAX_REVIEW_PER_FILE = 250 # Salva o arquivo de url/status e as páginas coletadas a cada n iterações
REVIEWS_FILENAME = 'collected_reviews-'
WINES_FILENAME = 'collected_wines-'
VINTAGES_FILENAME = 'collected_vintages-'

# Configurações do logging usado para gravar os registros dos eventos em arquivo de log e também exibí-los no console
import logging, sys
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    handlers=[logging.FileHandler("coleta.log"),
                              logging.StreamHandler(sys.stdout)])