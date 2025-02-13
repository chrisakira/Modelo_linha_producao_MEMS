from pulp import LpMaximize, LpProblem, LpVariable, lpSum

model = LpProblem(name="otimização linha de produção", sense=LpMaximize)

# Definição das constantes dos materiais base
tamanho_wafer = {
    "150mm": {"eficiencia": 0.95, "unidades_base": 75, "custo": 20},
    "250mm": {"eficiencia": 0.90, "unidades_base": 125, "custo": 29},
    "350mm": {"eficiencia": 0.80, "unidades_base": 175, "custo": 50}
}

fornecedores = {
    "fornecedor_1": {"eficiencia": 0.80, "custo": 20},
    "fornecedor_2": {"eficiencia": 0.90, "custo": 10},
    "fornecedor_3": {"eficiencia": 0.99, "custo": 60}
}

produtos = {
    "Accell": {"unidades_base": 2, "demanda": 500, "valor_venda": 10},
    "Gyro": {"unidades_base": 4, "demanda": 200, "valor_venda": 5},
    "Mag": {"unidades_base": 1, "demanda": 350, "valor_venda": 8},
    "BHI": {"unidades_base": 8, "demanda": 100, "valor_venda": 25}
}

max_trabalhadores = 50
horas_trabalhadas = 8
sensores_por_trabalhador = 10
salario_diario_trabalhador = 250
max_wafer_diario = 10

# Variáveis de decisão
# No maximo podemos utilizar 10 wafers por dia
wafer_var = {tamanho: LpVariable(name=f"wafer_{tamanho}", lowBound=0, upBound=max_wafer_diario, cat='Integer') for tamanho in tamanho_wafer}
fornecedor_vars = {sup: LpVariable(name=f"fornecedor_{sup}", cat='Binary') for sup in fornecedores}
produtos_var = {prod: LpVariable(name=f"produto_{prod}", lowBound=0, upBound=produtos[prod]["demanda"], cat='Integer') for prod in produtos}
trabalhadores_var = LpVariable(name="trabalhadores", lowBound=1, upBound=max_trabalhadores,  cat='Integer')
silicio_efetivo = LpVariable(name="silicio_efetivo", lowBound=0)

# Restrições
# Podemos ter apenas 1 fornecedor
model += lpSum(fornecedor_vars[sup] for sup in fornecedores) == 1, "Fornecedor_Unico"

# Limite máximo de sensores a serem produzidos por mão de obra
model += lpSum(produtos_var[prod] for prod in produtos) <= trabalhadores_var * sensores_por_trabalhador * horas_trabalhadas, "Limite_trabalho"

# Cálculo do total de wafers disponíveis
# Leva em consideração o numero de wafers utilizados e a quantidade de silicio possivel para extração apartir de cada wafer
total_wafers = lpSum(wafer_var[tamanho] * tamanho_wafer[tamanho]["unidades_base"] * tamanho_wafer[tamanho]["eficiencia"] for tamanho in tamanho_wafer)


# Restrições para definir o silício disponível com base no fornecedor escolhido
for sup in fornecedores:
    model += silicio_efetivo >= fornecedores[sup]["eficiencia"] * total_wafers - (1 - fornecedor_vars[sup]) * 1e6, f"silicio_efetivo_Lower_{sup}"
    model += silicio_efetivo <= fornecedores[sup]["eficiencia"] * total_wafers + (1 - fornecedor_vars[sup]) * 1e6, f"silicio_efetivo_Upper_{sup}"

# Restrição para garantir que a produção não exceda o silício disponível
model += lpSum(produtos_var[prod] * produtos[prod]["unidades_base"] for prod in produtos) <= silicio_efetivo, "Silicio_Disponivel"

# Cálculo dos custos
custo_wafers = lpSum(wafer_var[tamanho] * tamanho_wafer[tamanho]["custo"] for tamanho in tamanho_wafer)
custo_fornecedor = lpSum(fornecedor_vars[sup] * fornecedores[sup]["custo"] for sup in fornecedores)
custo_trabalho = trabalhadores_var * salario_diario_trabalhador
custos_totais = custo_wafers + custo_fornecedor + custo_trabalho

# Cálculo das receitas
receitas = lpSum(produtos_var[prod] * produtos[prod]["valor_venda"] for prod in produtos)

# Função objetivo: Maximizar o lucro
model += receitas - custos_totais, "Lucro_Total"

# Resolver o problema
model.solve()

# Exibir os resultados
total_trabalhadores = trabalhadores_var.varValue
print(f"Número mínimo de trabalhadores necessários: {total_trabalhadores}")
for var in model.variables():
    print(f"{var.name}: {var.varValue}")
print(f"Lucro Total: ${model.objective.value()}")