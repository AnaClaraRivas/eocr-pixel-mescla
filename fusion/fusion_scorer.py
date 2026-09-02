import numpy as np  
 
def fuse_scores( 
    pixel_result, 
    geo_results, 
    pixel_regional_results=None 
): 
 
    # pega o resultado global produzido pelo novo Pixel Core
    pixel_score = float( 
        pixel_result["pixel_fraud_score"] 
    ) 
 
    # pega o score de continuidade da imagem
    continuity_score = float( 
        pixel_result.get( 
            "continuity_score", 
            0.0 
        ) 
    ) 
 
    # pega o maior score encontrado entre os blocos analisados
    max_block_score = float( 
        pixel_result.get( 
            "max_block_score", 
            0.0 
        ) 
    ) 
 
    # pega a classificacao produzida pelo novo Pixel Core
    pixel_classification = pixel_result.get( 
        "pixel_classification", 
        "Baixa suspeita" 
    ) 
 
    # conta quantas regioes apresentaram comportamento
    # suspeito de acordo com a analise geometrica
    suspicious_regions = sum( 
        1 
        for result in geo_results 
        if result["geo_suspicious"] 
    ) 
 
    # pega a quantidade total de regioes analisadas
    total_regions = len( 
        geo_results 
    ) 
 
    # calcula a proporcao de regioes suspeitas
    # em relacao ao total de regioes encontradas
    if total_regions > 0: 
 
        geo_ratio = ( 
            suspicious_regions 
            / total_regions 
        ) 
 
    else: 
 
        # caso nao existam regioes, considera a proporcao como zero
        geo_ratio = 0.0 
 
    # transforma a proporcao de regioes suspeitas
    # em um score de 0 a 100
    geo_score = geo_ratio * 100 
 
    # combina o resultado global do novo Pixel Core
    # com o resultado global da analise geometrica
    #
    # o Pixel novo representa 70% do resultado
    # e a geometria representa 30%
    final_score = ( 
        pixel_score * 0.7 
        + 
        geo_score * 0.3 
    ) 
 
    # limita o score final para permanecer entre 0 e 100
    final_score = min( 
        100.0, 
        max( 
            0.0, 
            final_score 
        ) 
    ) 
 
    # define a classificacao global de acordo com o score final
    if final_score >= 75: 
 
        classification = ( 
            "Alta suspeita" 
        ) 
 
    elif final_score >= 45: 
 
        classification = ( 
            "Média suspeita" 
        ) 
 
    else: 
 
        classification = ( 
            "Baixa suspeita" 
        ) 
 
    # cria uma lista para armazenar os resultados
    # individuais de cada regiao
    regional_results = [] 
 
    # verifica se existem resultados da analise regional antiga
    if pixel_regional_results is not None: 
 
        # pega os valores de ELA de todas as regioes
        ela_vals = [ 
            p["ela_val"] 
            for p in pixel_regional_results 
        ] 
 
        # calcula a media dos valores de ELA
        mean_ela = ( 
            np.mean(ela_vals) 
            if ela_vals 
            else 0.0 
        ) 
 
        # calcula o desvio padrao dos valores de ELA
        # caso nao seja possivel calcular, utiliza 1.0
        std_ela = ( 
            np.std(ela_vals) 
            if len(ela_vals) > 1 
            and np.std(ela_vals) > 0 
            else 1.0 
        ) 
 
        # percorre as regioes que possuem resultados
        # tanto da analise de pixels quanto da geometria
        for i in range( 
            min( 
                len(pixel_regional_results), 
                len(geo_results) 
            ) 
        ): 
 
            # pega os resultados da regiao atual
            p = pixel_regional_results[i] 
            g = geo_results[i] 
 
            # pega o valor de ELA da regiao
            ela_val = float( 
                p["ela_val"] 
            ) 
 
            # pega o contraste entre a regiao e seu entorno
            edge_contrast = float( 
                p["edge_contrast"] 
            ) 
 
            # pega o maior desvio de pixel encontrado na regiao
            max_pixel_dev = float( 
                p["max_pixel_dev"] 
            ) 
 
            # pega o desvio angular da regiao
            angle_dev = float( 
                g["angle_dev"] 
            ) 
 
            # pega o desvio da densidade textual
            density_z = float( 
                g["density_z"] 
            ) 
 
            # verifica se a geometria da regiao foi considerada suspeita
            geo_suspicious = bool( 
                g["geo_suspicious"] 
            ) 
 
            # calcula o z-score do valor de ELA
            # comparando a regiao com as demais regioes
            ela_zscore = ( 
                ela_val - mean_ela 
            ) / std_ela 
 
            # inicia o score da regiao com zero
            score = 0.0 
 
            # aplica a regra original para regioes
            # que apresentam um z-score de ELA muito alto
            if ela_zscore >= 2.0: 
 
                score = ( 
                    60.0 
                    + 
                    (ela_zscore - 2.0) * 20.0 
                    + 
                    (edge_contrast * 15.0) 
                ) 
 
            # aplica a regra original para regioes
            # que apresentam um z-score acima de 1.2
            elif ela_zscore > 1.2: 
 
                score = ( 
                    (ela_zscore - 1.2) * 30.0 
                    + 
                    (edge_contrast * 10.0) 
                ) 
 
            # adiciona o resultado da geometria
            # caso a regiao tenha sido considerada suspeita
            if geo_suspicious: 
 
                score += ( 
                    angle_dev * 15.0 
                ) 
 
            # limita o score regional entre 0 e 100
            score = max( 
                0.0, 
                min( 
                    100.0, 
                    round( 
                        float(score), 
                        2 
                    ) 
                ) 
            ) 
 
            # verifica se a regiao apresenta alta suspeita
            # usando o score ou o z-score original da ELA
            is_high_risk = ( 
                score >= 25.0 
                or ela_zscore >= 1.8 
            ) 
 
            # define a classificacao da regiao
            if is_high_risk: 
 
                regional_classification = ( 
                    "Alta suspeita" 
                ) 
 
            elif score >= 12.0: 
 
                regional_classification = ( 
                    "Média suspeita" 
                ) 
 
            else: 
 
                regional_classification = ( 
                    "Baixa suspeita" 
                ) 
 
            # adiciona todos os resultados da regiao
            # na lista de resultados regionais
            regional_results.append({ 
 
                # identifica qual regiao esta sendo analisada
                "index": i, 
 
                # guarda o score final calculado para a regiao
                "regional_score": 
                    score, 
 
                # guarda a classificacao da regiao
                "classification": 
                    regional_classification, 
 
                # informa se a regiao foi considerada
                # como uma regiao de alta suspeita
                "is_high_risk": 
                    is_high_risk, 
 
                # guarda o valor de ELA da analise regional antiga
                "ela_val": 
                    round( 
                        ela_val, 
                        2 
                    ), 
 
                # guarda o z-score calculado para o valor de ELA
                "pixel_zscore": 
                    round( 
                        float(ela_zscore), 
                        2 
                    ), 
 
                # guarda o maior desvio de pixel da regiao
                "max_pixel_dev": 
                    round( 
                        max_pixel_dev, 
                        2 
                    ), 
 
                # guarda o contraste entre a regiao e seu entorno
                "edge_contrast": 
                    round( 
                        edge_contrast, 
                        2 
                    ), 
 
                # guarda o desvio angular encontrado
                "angle_dev": 
                    round( 
                        angle_dev, 
                        2 
                    ), 
 
                # guarda o desvio da densidade textual
                "density_z": 
                    round( 
                        density_z, 
                        2 
                    ), 
 
                # informa se a geometria foi considerada suspeita
                "geo_suspicious": 
                    geo_suspicious 
            }) 
 
    # retorna todos os resultados produzidos pela fusao
    return { 
 
        # guarda os resultados gerais da analise
        "global": { 
 
            # guarda o score produzido pelo novo Pixel Core
            "pixel_score": 
                round( 
                    pixel_score, 
                    2 
                ), 
 
            # guarda o score de continuidade
            "continuity_score": 
                round( 
                    continuity_score, 
                    2 
                ), 
 
            # guarda o maior score encontrado entre os blocos
            "max_block_score": 
                round( 
                    max_block_score, 
                    2 
                ), 
 
            # guarda o score global calculado pela geometria
            "geometry_score": 
                round( 
                    float(geo_score), 
                    2 
                ), 
 
            # guarda o score final da fusao global
            "combined_score": 
                round( 
                    float(final_score), 
                    2 
                ), 
 
            # guarda a classificacao final global
            "classification": 
                classification, 
 
            # guarda a classificacao original do novo Pixel Core
            "pixel_classification": 
                pixel_classification, 
 
            # guarda a quantidade de regioes suspeitas
            # segundo a analise geometrica
            "suspicious_geometry_regions": 
                suspicious_regions, 
 
            # guarda a quantidade total de regioes analisadas
            "total_regions": 
                total_regions 
        }, 
 
        # guarda os resultados individuais das regioes
        "regions": 
            regional_results, 
 
        # guarda o resultado completo produzido
        # pelo novo Pixel Core
        "pixel_result": 
            pixel_result 
    }
  

