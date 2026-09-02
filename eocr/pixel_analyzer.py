import cv2
import numpy as np


def analyze_pixels_in_regions(image_gray, image_path, regions):

    # abre a imagem original
    orig = cv2.imread(image_path)

    # configura a qualidade da imagem que será comprimida em jpg
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 85]

    # comprime a imagem usando jpg
    _, compressed = cv2.imencode('.jpg', orig, encode_param)

    # abre a imagem que foi comprimida
    decompressed = cv2.imdecode(compressed, 1)

    # compara os pixels da imagem original com os pixels da imagem comprimida
    # essa diferença é usada para encontrar possíveis alterações na imagem
    ela_diff = cv2.absdiff(
        orig,
        decompressed
    ).astype(np.float32)

    # calcula a média da diferença entre as cores de cada pixel
    ela_pixel_map = np.mean(
        ela_diff,
        axis=2
    )

    # cria uma lista para guardar os resultados de cada região
    pixel_results = []

    # pega a altura e a largura da imagem
    h_img, w_img = image_gray.shape

    # calcula a média geral dos valores de ela da imagem
    global_ela_mean = np.mean(ela_pixel_map)

    # analisa cada região de texto encontrada pelo ocr
    for r in regions:

        # pega a posição e o tamanho da região
        x, y, w, h = r["rect_box"]

        # recorta apenas a área do texto no mapa de ela
        crop_ela = ela_pixel_map[y:y+h, x:x+w]

        # verifica se o recorte está vazio
        if crop_ela.size == 0:

            # se estiver vazio, coloca valores zerados
            pixel_results.append({
                "ela_val": 0.0,
                "edge_contrast": 0.0,
                "max_pixel_dev": 0.0
            })

            continue

        # calcula a média dos valores de ela naquela região
        ela_val = float(np.mean(crop_ela))

        # encontra o maior valor de diferença entre os pixels da região
        max_pixel_dev = float(np.max(crop_ela))

        # define uma margem ao redor do texto
        # essa área vai ser usada para comparar o texto com o fundo
        margin = 4

        # define os limites da área ao redor do texto
        x1, y1 = max(
            0,
            x - margin
        ), max(
            0,
            y - margin
        )

        x2, y2 = min(
            w_img,
            x + w + margin
        ), min(
            h_img,
            y + h + margin
        )

        # recorta a área ao redor do texto
        crop_outer = image_gray[y1:y2, x1:x2]

        # recorta somente a área do texto
        crop_gray = image_gray[y:y+h, x:x+w]

        # calcula a variação dos pixels dentro da região do texto
        var_inner = float(np.var(crop_gray))

        # calcula a variação dos pixels na região ao redor do texto
        var_outer = float(np.var(crop_outer))

        # compara a variação do texto com a variação ao redor dele
        edge_contrast = abs(
            var_inner - var_outer
        ) / (
            var_outer + 1e-5
        )

        # guarda os resultados encontrados 
        pixel_results.append({
            # valor médio da diferença dos pixels
            "ela_val": round(ela_val, 2),

            # maior diferença encontrada em um único pixel
            "max_pixel_dev": round(max_pixel_dev, 2),

            # diferença entre o texto e a região ao redor
            "edge_contrast": round(
                float(edge_contrast),
                2
            )
        })

    return pixel_results, {
        "ela_heatmap": ela_pixel_map
    }