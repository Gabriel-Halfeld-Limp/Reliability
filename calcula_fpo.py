from pyomo.environ import *
from data_processing import load_all_data  # Importando a função que lê os dados
import numpy as np

def calcular_fpo(z_ger, z_line, flag_print):

    # Carregando os dados do arquivo CSV
    dados = load_all_data()  # Chama a função que carrega os dados
    D_GEN = dados['D_GEN']
    D_LIN = dados['D_LIN']
    D_LOAD = dados['D_LOAD']

    #Número de geradores, linhas e cargas
    Ng = len(D_GEN)
    geradores = np.arange(1,Ng+1)
    Nl = len(D_LIN)
    linhas = np.arange(1,Nl+1)
    Nc = len(D_LOAD)
    cargas = np.arange(1,Nc+1)

    S_base = 100

    #Criando o modelo
    model = ConcreteModel()

    #Criando Sets do Problema
    model.ger = RangeSet(Ng) #Geradores
    model.line = RangeSet(Nl) #Linhas
    model.carga = RangeSet(Nc) #Cargas
    model.bus = RangeSet(6) #Barras

    #Parâmetros do Modelo
    #Parâmetros da Carga
    model.p_carga = Param(model.carga,initialize={cargas[i]: D_LOAD.loc[i, 'Carga']/S_base for i in range(len(cargas))})
    model.carga_bus = Param(model.carga,initialize={cargas[i]: D_LOAD.loc[i, 'Barra'] for i in range(len(cargas))})

    #Parâmetros das Linhas
    model.barra_de = Param(model.line,initialize={linhas[i]: D_LIN.loc[i, 'Barra De'] for i in range(len(linhas))})
    model.barra_para = Param(model.line,initialize={linhas[i]: D_LIN.loc[i, 'Barra Para'] for i in range(len(linhas))})
    model.x = Param(model.line,initialize={linhas[i]: D_LIN.loc[i, 'Reatância'] for i in range(len(linhas))})
    model.flux_max = Param(model.line,initialize={linhas[i]: D_LIN.loc[i, 'Capacidade']/S_base for i in range(len(linhas))})

    #Parâmetros dos Geradores
    model.ger_bus = Param(model.ger,initialize={geradores[i]: D_GEN.loc[i, 'Barra'] for i in range(len(geradores))})
    model.ger_max = Param(model.ger,initialize={geradores[i]: D_GEN.loc[i, 'Cap Ind']/S_base for i in range(len(geradores))})

    #Parâmetros binários que representam o estado do componente: 0:down e 1:up
    model.z_ger = Param(model.ger, initialize={geradores[i]: z_ger[i] for i in range(len(geradores))})
    model.z_line = Param(model.line, initialize={linhas[i]: z_line[i] for i in range(len(linhas))})

    #Variáveis:
    model.pd = Var(model.carga, domain=NonNegativeReals) #Variável de corte de carga
    model.pg = Var(model.ger, domain=NonNegativeReals) #Variável de geração
    model.theta = Var(model.bus, bounds=(-np.pi, np.pi), domain=Reals) #Variável de ângulo nas barras
    model.flux = Var(model.line, domain=Reals) #Variável de fluxo, opcional mas facilita a implementação

    #Restrições:
    #Balanço de Potência nas Barras
    def balance_power_rule(model, barra):
        PG = sum(model.pg[ger] for ger in model.ger if model.ger_bus[ger] == barra)
        PL = sum(model.p_carga[car] for car in model.carga if model.carga_bus[car] == barra)
        fluxo_sum = 0
        for line in model.line:
            if model.barra_de[line] == barra:
                fluxo_sum += model.flux[line]
            elif model.barra_para[line] == barra:
                fluxo_sum -= model.flux[line]
        PD = sum(model.pd[carga] for carga in model.carga if model.carga_bus[carga] == barra)
        return PG + PD - fluxo_sum - PL == 0
    model.balance_power = Constraint(model.bus, rule=balance_power_rule)

    #Restrição que limita a geração de cada gerador:
    def ger_rule(model, ger):
        ger_max = model.ger_max[ger]*model.z_ger[ger]
        return (0, model.pg[ger], ger_max)
    model.ger_rule = Constraint(model.ger, rule=ger_rule)

    #Restrição de igualdade em que se define os fluxos nas linhas:
    def flow_rule(model, line):
        bus1 = model.barra_de[line]
        bus2 = model.barra_para[line]
        flux = (model.theta[bus1] - model.theta[bus2]) / model.x[line]
        return model.flux[line] == flux
    model.flow_rule = Constraint(model.line, rule=flow_rule)

    def barra_slack(model):
        return model.theta[1] == 0
    model.slack_rule = Constraint(rule=barra_slack)

    #Limites de Fluxo nas Linhas:
    def flow_limit_rule(model, line):
        limite = model.flux_max[line]*model.z_line[line]
        return (-limite, model.flux[line], limite)
    model.flow_limit = Constraint(model.line, rule=flow_limit_rule)

    #Restrição de corte de carga:
    def corte_carga_rule(model, carga):
        return (0, model.pd[carga], model.p_carga[carga])
    model.corte_carga = Constraint(model.carga, rule=corte_carga_rule)

    #Função Objetivo: Menor perda de carga:
    def objective_function(model):
        PD_sum = sum(model.pd[carga] for carga in model.carga)
        return PD_sum
    model.objective = Objective(rule=objective_function, sense=minimize)

    #Resolver o modelo
    solver = SolverFactory('glpk')
    solver.solve(model)

    #Extrair os resultados
    resultados = {}
    resultados['pg'] = {ger: model.pg[ger].value for ger in model.ger}
    resultados['pd'] = {carga: model.pd[carga].value for carga in model.carga}
    resultados['theta'] = {barra: model.theta[barra].value for barra in model.bus}
    resultados['flux'] = {line: model.flux[line].value for line in model.line}
    
    if flag_print:

        #model.pprint()
    
        #Extrair os resultados:
        #Imprimir a função objetivo
        print("Função Objetivo: Menor perda de carga =", model.objective.expr())
        
            #Imprimir os resultados
        print("Resultados:")
        print("Geração por gerador:", resultados['pg'])
        print("Corte de Carga por Barra:", resultados['pd'])
        print("Ângulo de tensão por barra:", resultados['theta'])
        print("Fluxo por linha:", resultados['flux'])

    return model.objective.expr()*S_base


z_ger = [1,1,1,1,1,1,1,1,1,1,1]
z_line = [1,1,1,1,1,1,1,1,1,1,1]

pd = calcular_fpo(z_ger, z_line, False)
print(pd)