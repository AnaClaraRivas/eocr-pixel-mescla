# continuidade dos pixels

# importando o numpy (faz contas em matrizes)
import numpy as np

# criando uma função que compara com o pixel do lado 
def horizontal_difference(gray):


    # Compara cada pixel com o pixel da direita

    # esquerda para direita 

    # : --> pegue tudo
    # linhas, colunas 
    # gray[:,1:] ---> todas as linhas, a partir da coluna 1
    # gray[:,:-1] ---> todas as linhas, ate a ultima coluna
    diff = np.abs(
        gray[:,1:].astype(float)
        -
        gray[:,:-1].astype(float)
    )

    return diff


# mesma logica, so que agora cima para baixo 
def vertical_difference(gray):


    # Compara cada pixel com o pixel abaixo


    diff = np.abs(
        gray[1:,:].astype(float)
        -
        gray[:-1,:].astype(float)
    )

    return diff



def diagonal_difference(gray):


    # Compara pixels diagonais


    diff = np.abs(
        gray[1:,1:].astype(float)
        -
        gray[:-1,:-1].astype(float)
    )

    return diff


# junta todas as analises
def create_continuity_map(gray):

    horizontal = horizontal_difference(gray)

    vertical = vertical_difference(gray)

    diagonal = diagonal_difference(gray)


    # ajusta tamanhos
    h = horizontal[:-1,:]

    v = vertical[:,:-1]


    continuity = (
        h +
        v +
        diagonal
    ) / 3


    return continuity



def calculate_continuity_score(map):

   # retorna percentual de descontinuidade

    # qual é a diferença média dos pixels dessa imagem
    mean_value = np.mean(map)

    # exemplo
    # mean_value = 25.5
    # 25.5 / 255 = 0.1

    # 10% da diferença máxima possível
    score = (
        mean_value / 255
    ) * 100


    return round(float(score),2)