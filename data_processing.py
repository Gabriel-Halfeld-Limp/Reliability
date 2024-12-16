# Importando a biblioteca pandas para manipulação de dados tabulares
import pandas as pd

# Função para carregar todos os dados necessários a partir de arquivos CSV
def load_all_data():
    # Carregando o arquivo 'D_GEN.csv' que contém dados sobre geradores de energia
    D_GEN = pd.read_csv('DADOS/D_GEN.csv')
    
    # Carregando o arquivo 'D_LIN.csv' que contém dados sobre linhas de transmissão
    D_LIN = pd.read_csv('DADOS/D_LIN.csv')
    
    # Carregando o arquivo 'D_LOAD.csv' que contém dados sobre as cargas de energia
    D_LOAD = pd.read_csv('DADOS/D_LOAD.csv')
    
    # Retornando os dados carregados como um dicionário, com as chaves representando os tipos de dados
    return {
        'D_GEN': D_GEN,   # Dados dos geradores
        'D_LIN': D_LIN,   # Dados das linhas de transmissão
        'D_LOAD': D_LOAD  # Dados das cargas de energia
    }