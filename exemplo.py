import numpy as np

# Parâmetro λ
lambda_param = 0.001

# Gerar 10 tempos (durações) para uma variável aleatória exponencial
tempos = np.random.exponential(1/lambda_param, 100000)

# Calcular a média dos tempos
media_tempos = np.mean(tempos)

# MTTF (Mean Time To Failure)
MTTF = 1 / lambda_param

# Comparar a média dos tempos com o MTTF
print(f"Média dos tempos: {media_tempos}")
print(f"MTTF: {MTTF}")
print(f"A média dos tempos é {'menor' if media_tempos < MTTF else 'maior'} que o MTTF.")

