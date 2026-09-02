# pega as análises anteriores e transforma em uma nota final de suspeita de fraude

import numpy as np

# função que transforma um valor em uma escala de 0 a 100
def normalize(value, max_value):

    # calcula a porcentagem que o valor representa em relação ao valor máximo definido
    score = (value / max_value) * 100

    # verifica se o valor calculado ultrapassou o limite máximo de 100.
    if score > 100:
        score = 100

    return score


# função que combina as análises de blocos e vizinhos para gerar um score de fraude
def calculate_pixel_fraud_score(
        block_scores,
        neighbor_scores
):

    """
    Junta as duas análises:
    - continuidade interna
    - comparação com vizinhos
    """

    # se existem resultados da análise de blocos
    if len(block_scores) == 0:
        # retorna zero caso nenhum bloco tenha sido analisado.
        return 0


    # pega o maior score encontrado entre todos os blocos analisados
    max_block = max(block_scores)

    # pega o maior valor de diferença encontrado entre blocos vizinhos
    max_neighbor = max(
        # Cria uma lista contendo apenas os valores de diferença dos vizinhos
        [
            x["neighbor_score"]
            for x in neighbor_scores
        ]
        # define o valor como zero caso não existam análises de vizinhos
    ) if neighbor_scores else 0



    # transforma em 0-100
    # converte o maior score dos blocos para uma escala percentual de 0 a 100
    block_score = normalize(
        max_block,
        50
    )

    # converte o maior score dos vizinhos para uma escala percentual de 0 a 100
    neighbor_score = normalize(
        max_neighbor,
        100
    )


    # pesos

    final_score = (

        block_score * 0.4

        +

        neighbor_score * 0.6

    )


    return round(
        float(final_score),
        2
    )


# função que transforma o score numérico em uma classificação
def classify_score(score):


    if score >= 75:

        return "Alta suspeita"


    elif score >= 45:

        return "Média suspeita"


    else:

        return "Baixa suspeita"