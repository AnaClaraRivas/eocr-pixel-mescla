import os 
import sys 
import cv2 
import json 
 
from core.eocr.eocr_engine import run_eocr 
from core.eocr.pixel_analyzer import analyze_pixels_in_regions 
from core.eocr.font_geometry import analyze_text_geometry 
from core.fusion.fusion_scorer import fuse_scores 
from core.visualizer.visualizer import render_report 
 
from core.pixels.analyzer import analyze_continuity 
 
def main(image_path): 
 
    # cria a pasta de resultados se ela ainda não existe 
    os.makedirs("results", exist_ok=True) 
 
    # mostra qual imagem esta sendo analisada 
    print(f"\n Processando análise: {image_path}...") 
 
    # abre a imagem em tons de cinza
    gray = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE) 
 
    # verifica se a imagem foi encontrada
    if gray is None: 
        print("ERRO Arquivo não encontrado.") 
        return 
 
    # usa o OCR para encontrar os textos da imagem
    # o EOCR identifica as regioes que serao analisadas
    regions = run_eocr(image_path) 
 
    # mostra quantas regioes de texto foram encontradas
    print(f" -> {len(regions)} regiões de texto identificadas.") 
 
    # analisa os pixels das regioes de texto encontradas pelo EOCR
    # usa a analise baseada em ELA
    # tambem calcula o contraste e o maior desvio de pixel
    # essa parte nao altera o funcionamento do EOCR
    pixel_res, pixel_maps = analyze_pixels_in_regions( 
        gray, 
        image_path, 
        regions 
    ) 
 
    # analisa a posicao e o formato dos textos encontrados
    # verifica principalmente o angulo e a densidade dos textos
    geo_res = analyze_text_geometry( 
        regions 
    ) 
 
    # executa o novo Pixel Core
    # essa analise observa a imagem de forma global
    # ela funciona independentemente das regioes encontradas pelo EOCR
    pixel_global = analyze_continuity( 
        image_path 
    ) 
 
    # junta os resultados das analises
    # o Pixel Core fornece o resultado global
    # o pixel analyzer fornece os resultados regionais 
    # a geometria fornece os resultados relacionados aos textos
    fused = fuse_scores( 
        pixel_global, 
        geo_res, 
        pixel_res 
    ) 
 
    # cria os relatorios visuais da analise
    # o hybrid_analysis mostra os resultados das regioes
    # o xray_heatmap mostra o mapa gerado pela analise ELA
    render_report(image_path, regions, fused, pixel_maps, 
                  output_path="results/hybrid_analysis.png", 
                  xray_path="results/xray_heatmap.png") 
 
    # cria os dados que serao utilizados no relatorio JSON
    relatorio_dados = { 
        "caminho_imagem": image_path, 
 
        # guarda a quantidade de regioes de texto encontradas
        "total_regioes_texto": len(regions), 
 
        # guarda os resultados globais da nova analise de pixels
        "analise_global": fused["global"], 
 
        # inicialmente nenhuma anomalia foi registrada
        # esse valor sera atualizado depois da analise regional
        "anomalia_detectada": False, 
 
        # lista que recebera os dados das regioes suspeitas
        "lista_anomalias": [], 
 
        # lista dos arquivos gerados durante a analise
        "arquivos_gerados": [ 
            "results/hybrid_analysis.png", 
            "results/xray_heatmap.png", 
            "results/continuity_map.png", 
            "results/continuity_heatmap.png" 
        ] 
    } 
 
    # mostra o começo do relatorio no terminal
    print("\n" + "=" * 65) 
    print("              RELATÓRIO DE ANÁLISE") 
    print("=" * 65) 
 
    # pega os resultados globais produzidos pela fusao
    global_result = fused["global"] 
 
    # mostra os resultados da analise global do novo Pixel Core
    print("\n[ ANÁLISE GLOBAL - PIXEL CORE ]") 
    print("-" * 65) 
 
    # mostra o score global calculado pelo novo Pixel Core
    print( 
        f" • Pixel Score Global      : " 
        f"{global_result['pixel_score']:.2f}/100" 
    ) 
 
    # mostra o score de continuidade encontrado na imagem
    print( 
        f" • Continuidade            : " 
        f"{global_result['continuity_score']:.2f}/100" 
    ) 
 
    # mostra o maior score encontrado entre os blocos analisados
    print( 
        f" • Maior Score de Bloco    : " 
        f"{global_result['max_block_score']:.2f}/100" 
    ) 
 
    # mostra o score relacionado a analise geometrica
    print( 
        f" • Score de Geometria      : " 
        f"{global_result['geometry_score']:.2f}/100" 
    ) 
 
    # mostra o score final da combinacao das analises globais
    print( 
        f" • Score Global Combinado  : " 
        f"{global_result['combined_score']:.2f}/100" 
    ) 
 
    # mostra a classificacao final da analise global
    print( 
        f" • Classificação Global    : " 
        f"{global_result['classification']}" 
    ) 
 
    # mostra a classificacao produzida pelo novo Pixel Core
    print( 
        f" • Classificação do Pixel  : " 
        f"{global_result['pixel_classification']}" 
    ) 
 
    # mostra quantas regioes apresentaram suspeita
    # de acordo com a analise geometrica
    print( 
        f" • Regiões suspeitas " 
        f"(geometria)              : " 
        f"{global_result['suspicious_geometry_regions']}/" 
        f"{global_result['total_regions']}" 
    ) 
 
    # mostra os resultados individuais das regioes encontradas
    print("\n" + "=" * 65) 
    print("              ANÁLISE DAS REGIÕES") 
    print("=" * 65) 
 
    # controla se alguma regiao apresentou uma possivel anomalia
    anomalies_found = False 
 
    # percorre todas as regioes encontradas pelo EOCR
    for i, r in enumerate(regions): 
 
        # pega o resultado da fusao correspondente a regiao atual
        regional = fused["regions"][i] 
 
        # pega o score calculado para a regiao
        score = regional["regional_score"] 
 
        # verifica se a regiao foi classificada como alta suspeita
        is_risk = ( 
            regional["classification"] 
            == "Alta suspeita" 
        ) 
 
        # verifica se a regiao apresenta alguma anomalia
        # regioes com score a partir de 12 sao consideradas suspeitas
        if is_risk or score >= 12.0: 
 
            # informa que uma anomalia regional foi encontrada
            anomalies_found = True 
 
            # define o nivel de suspeita que sera exibido
            if is_risk: 
                status = "SUSPEITA ALTA" 
            else: 
                status = "SUSPEITA" 
 
            # cria os dados da anomalia para salvar no JSON
            detalhe_anomalia = { 
                "texto_identificado": r["text"], 
                "nivel_classificacao": status, 
                "pontuacao_suspeita": round( 
                    float(score), 
                    1 
                ), 
 
                # guarda o maior desvio de pixel encontrado pela ELA
                "desvio_maximo_ela": 
                    pixel_res[i]["max_pixel_dev"], 
 
                # guarda o z-score da analise regional de pixels
                "pixel_zscore": 
                    regional["pixel_zscore"], 
 
                # guarda o contraste entre a regiao e seu entorno
                "edge_contrast": 
                    regional["edge_contrast"], 
 
                # guarda o desvio do angulo do texto
                "angle_dev": 
                    regional["angle_dev"], 
 
                # guarda o desvio da densidade do texto
                "density_z": 
                    regional["density_z"] 
            } 
 
            # adiciona os dados da regiao na lista de anomalias
            relatorio_dados[ 
                "lista_anomalias" 
            ].append( 
                detalhe_anomalia 
            ) 
 
            # mostra as informacoes da regiao suspeita no terminal
            print( 
                f"\n • [{status}] " 
                f"Região {i + 1}" 
            ) 
 
            # mostra o texto identificado pelo EOCR
            print( 
                f"   Texto identificado : " 
                f"'{r['text']}'" 
            ) 
 
            # mostra o score calculado para a regiao
            print( 
                f"   Score regional     : " 
                f"{score:.2f}/100" 
            ) 
 
            # mostra o z-score calculado pela analise de pixels
            print( 
                f"   Pixel Z-Score      : " 
                f"{regional['pixel_zscore']}" 
            ) 
 
            # mostra o maior desvio de pixel encontrado pela ELA
            print( 
                f"   Pico Pixel (ELA)   : " 
                f"{pixel_res[i]['max_pixel_dev']}" 
            ) 
 
            # mostra a diferenca de contraste encontrada
            # entre a regiao e seu entorno
            print( 
                f"   Edge Contrast      : " 
                f"{regional['edge_contrast']}" 
            ) 
 
            # mostra o desvio angular encontrado na regiao
            print( 
                f"   Desvio Angular     : " 
                f"{regional['angle_dev']}" 
            ) 
 
            # mostra o desvio da densidade textual
            print( 
                f"   Densidade Z        : " 
                f"{regional['density_z']}" 
            ) 
 
            # separa as informacoes de uma regiao da proxima
            print("-" * 65) 
 
    # salva no relatorio se alguma anomalia regional foi encontrada
    relatorio_dados[ 
        "anomalia_detectada" 
    ] = anomalies_found 
 
    # mostra o resultado final da analise no terminal
    print("\n" + "=" * 65) 
    print("              RESULTADO FINAL") 
    print("=" * 65) 
 
    # verifica se alguma regiao foi considerada suspeita
    if anomalies_found: 
 
        # informa que existem regioes com possiveis anomalias
        print( 
            " ⚠ Foram encontradas regiões " 
            "com possíveis anomalias." 
        ) 
 
        # mostra quantas regioes foram sinalizadas
        print( 
            f" • Regiões sinalizadas: " 
            f"{len(relatorio_dados['lista_anomalias'])}" 
        ) 
 
    else: 
 
        # informa que nenhuma regiao apresentou anomalia regional
        print( 
            " ✓ Nenhuma anomalia regional " 
            "foi detectada." 
        ) 
 
    # mostra a classificacao global obtida pela analise
    print( 
        f" • Classificação global: " 
        f"{global_result['classification']}" 
    ) 
 
    # mostra o score global final
    print( 
        f" • Score global: " 
        f"{global_result['combined_score']:.2f}/100" 
    ) 
 
    print("=" * 65) 
 
    # mostra os arquivos gerados durante o processamento
    print("\n Relatórios gerados:") 
 
    # mostra o relatorio visual com as regioes analisadas
    print( 
        "   1. results/hybrid_analysis.png" 
        "       → análise regional" 
    ) 
 
    # mostra o mapa gerado pela analise ELA antiga
    print( 
        "   2. results/xray_heatmap.png" 
        "             → mapa ELA" 
    ) 
 
    # mostra o mapa de continuidade gerado pelo novo Pixel Core
    print( 
        "   3. results/continuity_map.png" 
        "        → mapa de continuidade" 
    ) 
 
    # mostra o mapa de calor gerado pelo novo Pixel Core
    print( 
        "   4. results/continuity_heatmap.png" 
        "  → mapa do Pixel Core" 
    ) 
 
    # salva o resultado completo em um arquivo JSON
    json_path = "results/report.json" 
 
    # abre o arquivo JSON e salva os dados da analise
    with open(json_path, "w", encoding="utf-8") as f: 
        json.dump(relatorio_dados, f, ensure_ascii=False, indent=4) 
         
    # informa no terminal onde o relatorio JSON foi salvo
    print(f" Relatório JSON salvo em: '{json_path}'\n") 
 
    # retorna os dados completos da analise em formato JSON
    return json.dumps(relatorio_dados, ensure_ascii=False, indent=4) 
 
if __name__ == "__main__": 
    # pega o caminho da imagem dado pelo terminal
    file_arg = sys.argv[1] if len(sys.argv) > 1 else "documento.png" 
 
    # inicia a analise da imagem
    main(file_arg)
  
