# Importando a biblioteca pyomo para otimização
from pyomo.environ import *

# Importando a função que carrega os dados necessários para o modelo
from data_processing import load_all_data  

# Importando a biblioteca numpy para operações numéricas
import numpy as np

# Função que realiza o cálculo do despacho ótimo de potência (FPO)
def calcular_fpo(z_ger, z_line, flag_print):

    # Carregando os dados de geradores, linhas e cargas a partir dos arquivos CSV
    dados = load_all_data()  # Chama a função que carrega os dados
    D_GEN = dados['D_GEN']  # Dados dos geradores
    D_LIN = dados['D_LIN']  # Dados das linhas de transmissão
    D_LOAD = dados['D_LOAD']  # Dados das cargas

    # Número de geradores, linhas e cargas
    Ng = len(D_GEN)  # Quantidade de geradores
    geradores = np.arange(1, Ng + 1)  # Índices dos geradores
    Nl = len(D_LIN)  # Quantidade de linhas
    linhas = np.arange(1, Nl + 1)  # Índices das linhas
    Nc = len(D_LOAD)  # Quantidade de cargas
    cargas = np.arange(1, Nc + 1)  # Índices das cargas

    # Definindo a base de potência (S_base)
    S_base = 100  # Base de potência

    # Criando o modelo do Pyomo (Modelo de Programação Matemática)
    model = ConcreteModel()

    # Criando Sets do Problema:
    model.ger = RangeSet(Ng)  # Set de geradores
    model.line = RangeSet(Nl)  # Set de linhas de transmissão
    model.carga = RangeSet(Nc)  # Set de cargas
    model.bus = RangeSet(6)  # Set de barras (nós)

    # Definindo Parâmetros do Modelo:
    # Parâmetros relacionados às cargas (potência e barra associada)
    model.p_carga = Param(model.carga, initialize={cargas[i]: D_LOAD.loc[i, 'Carga'] / S_base for i in range(len(cargas))})
    model.carga_bus = Param(model.carga, initialize={cargas[i]: D_LOAD.loc[i, 'Barra'] for i in range(len(cargas))})

    # Parâmetros das Linhas de Transmissão (barra de origem, barra de destino, reatância e capacidade)
    model.barra_de = Param(model.line, initialize={linhas[i]: D_LIN.loc[i, 'Barra De'] for i in range(len(linhas))})
    model.barra_para = Param(model.line, initialize={linhas[i]: D_LIN.loc[i, 'Barra Para'] for i in range(len(linhas))})
    model.x = Param(model.line, initialize={linhas[i]: D_LIN.loc[i, 'Reatância'] for i in range(len(linhas))})
    model.flux_max = Param(model.line, initialize={linhas[i]: D_LIN.loc[i, 'Capacidade'] / S_base for i in range(len(linhas))})

    # Parâmetros dos Geradores (barra associada e capacidade máxima)
    model.ger_bus = Param(model.ger, initialize={geradores[i]: D_GEN.loc[i, 'Barra'] for i in range(len(geradores))})
    model.ger_max = Param(model.ger, initialize={geradores[i]: D_GEN.loc[i, 'Cap Ind'] / S_base for i in range(len(geradores))})

    # Parâmetros binários para controlar o estado de geradores e linhas (ligado/desligado)
    model.z_ger = Param(model.ger, initialize={geradores[i]: z_ger[i] for i in range(len(geradores))})
    model.z_line = Param(model.line, initialize={linhas[i]: z_line[i] for i in range(len(linhas))})

    # Variáveis do Modelo:
    model.pd = Var(model.carga, domain=NonNegativeReals)  # Potência de carga a ser cortada
    model.pg = Var(model.ger, domain=NonNegativeReals)  # Potência gerada por cada gerador
    model.theta = Var(model.bus, bounds=(-np.pi, np.pi), domain=Reals)  # Ângulo de tensão nas barras
    model.flux = Var(model.line, domain=Reals)  # Fluxo de potência nas linhas

    # Restrições do Modelo:

    # Restrições de balanço de potência nas barras (garante que a potência gerada e consumida seja balanceada)
    def balance_power_rule(model, barra):
        PG = sum(model.pg[ger] for ger in model.ger if model.ger_bus[ger] == barra)  # Potência gerada nas barras
        PL = sum(model.p_carga[car] for car in model.carga if model.carga_bus[car] == barra)  # Carga nas barras
        fluxo_sum = 0  # Soma dos fluxos de potência
        for line in model.line:
            if model.barra_de[line] == barra:
                fluxo_sum += model.flux[line]  # Fluxo de potência da barra de origem
            elif model.barra_para[line] == barra:
                fluxo_sum -= model.flux[line]  # Fluxo de potência da barra de destino
        PD = sum(model.pd[carga] for carga in model.carga if model.carga_bus[carga] == barra)  # Potência de carga cortada
        return PG + PD - fluxo_sum - PL == 0  # Equação de balanço de potência
    model.balance_power = Constraint(model.bus, rule=balance_power_rule)

    # Restrições para limitar a geração de cada gerador conforme o estado (ligado/desligado)
    def ger_rule(model, ger):
        ger_max = model.ger_max[ger] * model.z_ger[ger]  # Capacidade máxima de geração (dependente do estado do gerador)
        return (0, model.pg[ger], ger_max)  # Geração não pode ser maior que a capacidade do gerador
    model.ger_rule = Constraint(model.ger, rule=ger_rule)

    # Restrições de fluxo nas linhas (equação para calcular o fluxo de potência nas linhas)
    def flow_rule(model, line):
        bus1 = model.barra_de[line]
        bus2 = model.barra_para[line]
        flux = (model.theta[bus1] - model.theta[bus2]) / model.x[line]  # Fluxo de potência baseado na diferença de ângulo e reatância
        return model.flux[line] == flux
    model.flow_rule = Constraint(model.line, rule=flow_rule)

    # Restrições para definir a barra slack (referência de ângulo)
    def barra_slack(model):
        return model.theta[1] == 0  # A barra 1 é definida com ângulo 0
    model.slack_rule = Constraint(rule=barra_slack)

    # Limitação do fluxo nas linhas (considerando a capacidade máxima de cada linha e seu estado)
    def flow_limit_rule(model, line):
        limite = model.flux_max[line] * model.z_line[line]  # Limite de fluxo baseado na capacidade da linha e seu estado
        return (-limite, model.flux[line], limite)  # Fluxo deve estar dentro do limite
    model.flow_limit = Constraint(model.line, rule=flow_limit_rule)

    # Restrições para corte de carga (garante que a carga cortada não ultrapasse a carga total)
    def corte_carga_rule(model, carga):
        return (0, model.pd[carga], model.p_carga[carga])  # A carga cortada não pode ser maior que a carga disponível
    model.corte_carga = Constraint(model.carga, rule=corte_carga_rule)

    # Função Objetivo: Minimizar a perda de carga (minimizar a potência cortada)
    def objective_function(model):
        PD_sum = sum(model.pd[carga] for carga in model.carga)  # Soma da potência cortada
        return PD_sum  # Minimizar a perda de carga
    model.objective = Objective(rule=objective_function, sense=minimize)

    # Resolver o modelo com o solver GLPK (Simplex ou outros algoritmos)
    solver = SolverFactory('glpk')
    solver.solve(model)

    # Extrair os resultados:
    resultados = {}
    resultados['pg'] = {ger: model.pg[ger].value for ger in model.ger}  # Potência gerada por cada gerador
    resultados['pd'] = {carga: model.pd[carga].value for carga in model.carga}  # Potência cortada por carga
    resultados['theta'] = {barra: model.theta[barra].value for barra in model.bus}  # Ângulo de cada barra
    resultados['flux'] = {line: model.flux[line].value for line in model.line}  # Fluxo de potência por linha
    
    # Se flag_print for True, imprimir os resultados detalhados
    if flag_print:
        print("Função Objetivo: Menor perda de carga =", model.objective.expr())  # Imprime a função objetivo
        print("Resultados:")
        print("Geração por gerador:", resultados['pg'])  # Geração de cada gerador
        print("Corte de Carga por Barra:", resultados['pd'])  # Corte de carga em cada barra
        print("Ângulo de tensão por barra:", resultados['theta'])  # Ângulo de tensão por barra
        print("Fluxo por linha:", resultados['flux'])  # Fluxo de potência por linha

    # Retorna o valor da função objetivo (perda de carga) multiplicado pela base de potência
    return model.objective.expr() * S_base