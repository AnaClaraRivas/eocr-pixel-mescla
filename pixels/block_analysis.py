# arquivo que vai mostrar a região que possui a maior variação entre os pixels

# importando o open cv
import cv2

# importando o numpy (faz contas em matrizes)
# uma imagem em python é tipo uma matriz
import numpy as np

# criando uma função que recebe a imagem cinza (gray) e informando quanto pixels quero em cada bloco que vou dividir a imagem (32)
def analyze_blocks(gray, block_size=16):

    # pega a largura e altura da matriz e coloca nas variaveis

    # tamanho = gray.shape
    # height = tamanho[0]
    # width = tamanho[1]

    height, width = gray.shape

    # dicionario onde vão ficar os blocos 
    blocks = []

    # onde vai ser colocado os scores de cada bloco
    scores = []

    # for y in range(inicio, parada, passo)
    #  iniciando em inicio, incrementando de acordo com o passo, até atingir ou ultrapassar a parada

    # height-block_size ---> serve para não ultrapassar os limites da imagem 

    # laço que divide a altura, então ele meio que faz as linhas horizontais
    for y in range(0, height-block_size, block_size):

        # mesma logica para a largura, faz as linhas verticais
        for x in range(0, width-block_size, block_size):

            # pega a image cinza e divide em blocos
            block = gray[
                y:y+block_size,
                x:x+block_size
            ]


            # diferença entre pixels vizinhos

            # horizontal --> guarda uma matriz com a diferença entre pixels vizinhos na horizontal

            # deixa os n positivos
            horizontal = np.abs(

                # calcula a diferença entre valores vizinhos
                np.diff(
                    # os pixels são n inteiros mas para fazer conta é melhor float
                    block.astype(float),
                    # permite comparar os pixels do lado (esquerda para direita)
                    axis=1
                )
            )


            vertical = np.abs(
                np.diff(
                    block.astype(float),
                    axis=0 # permite comparar os pixels do lado (cima para baixo)
                )
            )

            # resultado da analise de um bloco 
            score = (
                horizontal.mean() # media da diferença dos pixels do lado
                +
                vertical.mean() # media da diferença dos pixels de cima 
            ) / 2


            # add as infos (dicionario chave e valor) de um bloco na lista blocks
            blocks.append({
                "x":x,
                "y":y,
                "score":round(float(score),2)
            })

            # add o score do bloco que analisei na lista score
            scores.append(score)


    # retorna os blocos e scores
    return blocks, scores