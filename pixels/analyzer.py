# importa as funções que vai precisar
from .block_heatmap import create_block_heatmap
from .neighbor_analysis import analyze_neighbor_difference


from .preprocessing import preprocess_image

from .metrics import (
    create_continuity_map,
    calculate_continuity_score
)

from .block_analysis import analyze_blocks

from .pixel_score import (
    calculate_pixel_fraud_score,
    classify_score
)

# importando bibliotecas
import cv2
import os

# função principal que recebe o caminho da imagem e executa toda a análise
def analyze_continuity(image_path):

    image, gray = preprocess_image(image_path)

    # divide a imagem em blocos e calcula o nível de diferença dentro de cada bloco
    blocks, block_scores = analyze_blocks(gray)

    # mapa
    heatmap_path = create_block_heatmap(
        image,
        blocks
    )

    # vizinhos
    neighbor_scores = analyze_neighbor_difference(
        gray
    )

    # pixel score
    pixel_score = calculate_pixel_fraud_score(
        block_scores,
        neighbor_scores
    )

    # classificacao
    classification = classify_score(
        pixel_score
    )


    # calcula continuidade
    continuity_map = create_continuity_map(gray)


    score = calculate_continuity_score(
        continuity_map
    )

    # criando pasta de resultados
    os.makedirs(
        "results",
        exist_ok=True
    )


    # converte os valores do mapa para uma escala de imagem
    normalized = cv2.normalize(
        continuity_map,
        None,
        0,
        255,
        cv2.NORM_MINMAX
    )


    normalized = normalized.astype("uint8")


    # mapa preto e branco
    cv2.imwrite(
        "results/continuity_map.png",
        normalized
    )


    # cria mapa colorido
    heatmap = cv2.applyColorMap(
        normalized,
        cv2.COLORMAP_JET
    )

    # salva mapa colorido
    cv2.imwrite(
        "results/continuity_heatmap.png",
        heatmap
    )


    return {

        "continuity_score": float(score),


        "max_block_score":
        float(max(block_scores)),


        "pixel_fraud_score":
        pixel_score,


        "pixel_classification":
        classification,

        # ordena os blocos do maior score para o menor e pega os 10 mais suspeitos
        "suspicious_blocks":
        sorted(
            blocks,
            key=lambda x:x["score"],
            reverse=True
        )[:10],


        "neighbor_anomalies":
        sorted(
            neighbor_scores,
            key=lambda x:x["neighbor_score"],
            reverse=True
        )[:10],


        "heatmap":
        heatmap_path

    }