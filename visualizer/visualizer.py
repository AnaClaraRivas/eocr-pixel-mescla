import cv2 
import numpy as np 
 
 
def render_report( 
    image_path, 
    regions, 
    fused_scores, 
    pixel_maps, 
    output_path="results/hybrid_analysis.png", 
    xray_path="results/xray_heatmap.png" 
): 
 
    # abre a imagem original
    img = cv2.imread(image_path) 
 
    # pega a altura e a largura da imagem
    h, w, _ = img.shape 
 
    # usa o mapa ELA antigo para criar o mapa visual
    xray_mask = pixel_maps.get( 
        "ela_heatmap", 
        np.zeros( 
            (h, w), 
            dtype=np.float32 
        ) 
    ) 
 
    # normaliza os valores dos pixels para a faixa de 0 a 255
    xray_norm = cv2.normalize( 
        xray_mask, 
        None, 
        alpha=0, 
        beta=255, 
        norm_type=cv2.NORM_MINMAX 
    ) 
 
    # transforma os valores normalizados em inteiros de 8 bits
    xray_uint8 = np.uint8( 
        xray_norm 
    ) 
 
    # aplica um mapa de cores sobre os valores da ELA
    heatmap = cv2.applyColorMap( 
        xray_uint8, 
        cv2.COLORMAP_JET 
    ) 
 
    # mistura o mapa ELA com a imagem original
    xray_overlay = cv2.addWeighted( 
        img, 
        0.4, 
        heatmap, 
        0.6, 
        0 
    ) 
 
    # salva o mapa ELA resultante
    cv2.imwrite( 
        xray_path, 
        xray_overlay 
    ) 
 
    # pega os resultados individuais de cada regiao
    # produzidos pela fusao das analises
    regional_results = fused_scores.get( 
        "regions", 
        [] 
    ) 
 
    # percorre todas as regioes encontradas pelo EOCR
    # para desenhar os resultados sobre a imagem
    for i, r in enumerate(regions): 
 
        # evita erro caso alguma regiao nao possua
        # um resultado correspondente na fusao
        if i >= len(regional_results): 
            continue 
 
        # pega o resultado da regiao atual
        regional = regional_results[i] 
 
        # pega os pontos que formam a caixa da regiao
        pts = r["bbox"] 
 
        # pega o score calculado para a regiao
        score = float( 
            regional["regional_score"] 
        ) 
 
        # verifica se a regiao foi classificada
        # como uma regiao de alta suspeita
        is_risk = bool( 
            regional.get( 
                "is_high_risk", 
                False 
            ) 
        ) 
 
        # pega o texto identificado pelo EOCR
        text = r["text"] 
 
        # define a cor e o texto do alerta
        # de acordo com o nivel de suspeita da regiao
        if is_risk or score >= 25.0: 
 
            # vermelho indica suspeita alta
            color = (0, 0, 255) 
 
            # mostra a classificacao e o score da regiao
            label = ( 
                f"[SUSPEITA ALTA " 
                f"{score:.0f}%] " 
                f"{text}" 
            ) 
 
        elif score >= 12.0: 
 
            # amarelo indica uma regiao suspeita
            color = (0, 255, 255) 
 
            # mostra o alerta e o score da regiao
            label = ( 
                f"[ATENCAO " 
                f"{score:.0f}%] " 
                f"{text}" 
            ) 
 
        else: 
 
            # verde indica que a regiao nao foi sinalizada
            color = (0, 255, 0) 
 
            # nao escreve nenhum alerta na imagem
            label = "" 
 
        # desenha a caixa da regiao na imagem
        cv2.polylines( 
            img, 
            [pts], 
            isClosed=True, 
            color=color, 
            thickness=2 
        ) 
 
        # escreve o alerta somente quando a regiao foi sinalizada
        if label: 
 
            # pega a posicao inicial para escrever o texto
            x = pts[0][0] 
            y = pts[0][1] - 5 
 
            # escreve o resultado da regiao sobre a imagem
            cv2.putText( 
                img, 
                label, 
                ( 
                    max(x, 5), 
                    max(y, 15) 
                ), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.45, 
                color, 
                1, 
                cv2.LINE_AA 
            ) 
 
    # pega os resultados gerais da analise
    # produzidos pela fusao
    global_result = fused_scores.get( 
        "global", 
        {} 
    ) 
 
    # pega o score global combinado
    global_score = float( 
        global_result.get( 
            "combined_score", 
            0.0 
        ) 
    ) 
 
    # pega a classificacao geral da analise
    global_classification = global_result.get( 
        "classification", 
        "Sem classificação" 
    ) 
 
    # cria o texto que sera mostrado no topo da imagem
    # com o score e a classificacao global
    global_label = ( 
        f"PIXEL GLOBAL: " 
        f"{global_score:.1f}/100 - " 
        f"{global_classification}" 
    ) 
 
    # coloca o resultado global no topo da imagem
    cv2.putText( 
        img, 
        global_label, 
        (10, 30), 
        cv2.FONT_HERSHEY_SIMPLEX, 
        0.65, 
        (255, 255, 255), 
        2, 
        cv2.LINE_AA 
    ) 
 
    # salva a imagem final com os resultados da analise
    cv2.imwrite( 
        output_path, 
        img 
    )
  
