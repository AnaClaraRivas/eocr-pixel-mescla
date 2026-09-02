import numpy as np

def analyze_text_geometry(regions):

    # vê se existem regiões de texto para analisar
    if not regions:
        return []
    
    # pega o ângulo de cada texto e limita o valor para uma volta de 90 graus
    angles = [r["angle"] % 90 for r in regions]

    # calcula o ângulo que aparece como padrão entre os textos
    median_angle = np.median(angles) if angles else 0.0

    # calcula a densidade de cada texto usando o tamanho do texto e o espaço
    densities = [max(r["size"][0], r["size"][1]) / max(len(r["text"].strip()), 1) for r in regions]

    # calcula a densidade média dos textos
    mean_density = np.mean(densities) if densities else 1.0

    # calcula o quanto as densidades variam entre os textos
    std_density = np.std(densities) if np.std(densities) > 0 else 1.0

    # cria uma lista para guardar os resultados da análise
    geo_results = []

    # analisa cada região de texto
    for i, r in enumerate(regions):

        # calcula a diferença entre o ângulo de um texto e o ângulo padrão dos outros 
        angle_diff = abs((r["angle"] % 90) - median_angle)

        # conta quantos caracteres existem no texto 
        text_len = max(len(r["text"].strip()), 1)

        # pega o maior valor entre largura e altura
        w = max(r["size"][0], r["size"][1])

        # calcula a densidade
        density = w / text_len

        # calcula o quanto essa densidade esta distante da média
        density_z = abs(density - mean_density) / std_density

        # guarda os resultados da análise daquela região
        geo_results.append({

            # mostra o quanto o ângulo do texto está diferente do padrão
            "angle_dev": round(float(angle_diff), 2),

            # mostra o quanto a densidade esta diferente da média
            "density_z": round(float(density_z), 2),

            # considera o texto suspeito quando o ângulo ou a densidade estão muito diferentes
            "geo_suspicious": angle_diff > 1.8 or density_z > 2.2
        })
        
    # retorna os resultados da análise de geometria
    return geo_results