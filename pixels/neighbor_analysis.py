# verifica se esse bloco é muito diferente dos blocos ao redor (vizinhos)

# importando o numpy (faz contas em matrizes)
import numpy as np

# recebe dois blocos e compara eles
def compare_blocks(block1, block2):


    # np.abs - deixa tudo posistivo

    # subtrai os numeros que formam um block
    difference = np.abs(
        # converte para float
        block1.astype(float)
        -
        block2.astype(float)
    )


    # calcula a média das diferenças
    return difference.mean()

# pegar uma imagem, dividir em blocos de 32×32 pixels e comparar cada bloco com seus vizinhos para descobrir quais regiões são diferentes do restante.
# vai gerar o neighbor_score

# criando uma função que 
def analyze_neighbor_difference(
        # image cinza e o tamanho (32x32)
        gray,
        block_size=16
):

    # descobrindo o tamanho da imagem 
    height, width = gray.shape

    # lista que vai guardar os blocos suspeitos
    results = []

    # para guardar a posiçãoe  eo bloco (x,y) e equal bloco (b1,b2,b3...)
    blocks = {}


    # mesma logica dos pixels

    for y in range(0, height-block_size, block_size):

        for x in range(0, width-block_size, block_size):

            # guarda os blocos no dicionario
            blocks[(x,y)] = gray[
                y:y+block_size,
                x:x+block_size
            ]



    # compara vizinhos

    # pega cada item do dicionario
    for (x,y), block in blocks.items():

        # guardar os blocos ao redor
        neighbors = []


        # posicões dos vizinhos
        positions = [

            (x-block_size,y), # esquerda

            (x+block_size,y), # direita

            (x,y-block_size), # cima

            (x,y+block_size)  # baixo

        ]


        # blocos do cantos não tem todos os vizinhos
        # antes de pegar um vizinho, verifica se ele realmente existe, se ele realmente existir, coloca na lista de vizinhos
        # pega uma posicao vizinha de cada vez 
        for pos in positions:

            if pos in blocks:

                neighbors.append(
                    blocks[pos]
                )

        # ja temos os vizinhos do bloco que esta endo analisado

        # ve se tem vizinho 
        if len(neighbors) > 0:

            # guardar as diferenças que vamos calcular
            differences = []

            # percorre cada vizinho
            for neighbor in neighbors:

                # função que criei la em cima 
                # block1 - block (que estamos analisando)
                # block2 - vizinho
                diff = compare_blocks(
                    block,
                    neighbor
                )

                # coloca o retorno da função na lista que criamos
                differences.append(diff)


            # media das diferenças
            anomaly = np.mean(
                differences
            )

            # guarda o resultado
            results.append({

                "x":x,

                "y":y,

                "neighbor_score":
                round(
                    float(anomaly),
                    2
                )

            })

    # entrega a lista para quem chamou (analyzer)
    return results