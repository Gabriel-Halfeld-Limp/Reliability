import pandas as pd

def load_all_data():
    D_GEN = pd.read_csv('DADOS/D_GEN.csv')
    D_LIN = pd.read_csv('DADOS/D_LIN.csv')
    D_LOAD = pd.read_csv('DADOS/D_LOAD.csv')
    return {
        'D_GEN': D_GEN,
        'D_LIN': D_LIN,
        'D_LOAD': D_LOAD
    }
