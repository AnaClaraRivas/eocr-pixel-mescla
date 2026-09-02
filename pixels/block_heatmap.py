# pega os resultados que já foram calculados e transforma em uma imagem

# importando
import cv2
import numpy as np

# image_path --> caminho da img original
# blocks --> a lista do block_analysis
# output --> onde vai salvar o mapa

# pegar os blocos que o algoritmo analisou, transformar os scores deles em cores e colocar essas cores em cima da imagem original para você enxergar onde estão as regiões suspeitas.

def create_block_heatmap(
    image,
    blocks,
    output="results/block_heatmap.png"
):


    # image.shape --> 2000 linhas, 1500 colunas, 3 cores

    # cria um mapa vazio
    heatmap = np.zeros(
        # linhas e colunas
        image.shape[:2],
        dtype=np.float32
    )

    # passa por cada bloco
    for block in blocks:

        # separa a latura, largura e score pra ficar melhor
        x = block["x"]
        y = block["y"]
        score = block["score"]


        # preenche a região com o score dela
        heatmap[
            y:y+16,
            x:x+16
        ] = score


    # transforma os valores em escala de imagem

    heatmap = cv2.normalize(
        heatmap,
        None,
        0,
        255,
        cv2.NORM_MINMAX
    )

    # converte para formato de imagem
    heatmap = heatmap.astype(
        np.uint8
    )


    # aplica cores

    colored = cv2.applyColorMap(
        heatmap,
        cv2.COLORMAP_JET
    )


    # mistura com imagem original

    overlay = cv2.addWeighted(
        image,
        0.6,
        colored,
        0.4,
        0
    )


    cv2.imwrite(
        output,
        overlay
    )


    return output