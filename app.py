from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import os
import uuid
import math

from pixels.analyzer import analyze_continuity
from pixels.preprocessing import preprocess_image

from eocr.eocr_engine import run_eocr
from eocr.font_geometry import analyze_text_geometry
from eocr.pixel_analyzer import analyze_pixels_in_regions

from fusion.fusion_scorer import fuse_scores
from visualizer.visualizer import render_report
from valid_api import valid_bp


app = Flask(__name__)
CORS(app)
app.register_blueprint(valid_bp)


# =========================================================
# CONVERSÃO PARA JSON
# =========================================================

def converter_json(obj):

    if isinstance(obj, dict):
        return {
            str(chave): converter_json(valor)
            for chave, valor in obj.items()
        }

    if isinstance(obj, list):
        return [
            converter_json(valor)
            for valor in obj
        ]

    if isinstance(obj, tuple):
        return [
            converter_json(valor)
            for valor in obj
        ]

    if hasattr(obj, "item"):
        return converter_json(obj.item())

    if hasattr(obj, "tolist"):
        return converter_json(obj.tolist())

    # TRATA NaN E INFINITY
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return 0.0

    return obj


# =========================================================
# ROTA PRINCIPAL
# =========================================================

@app.route("/")
def home():
    return "API funcionando!"


# =========================================================
# ROTA PARA DISPONIBILIZAR AS IMAGENS
# =========================================================

@app.route("/results/<path:nome_arquivo>")
def resultados(nome_arquivo):

    pasta_results = os.path.join(
        app.root_path,
        "results"
    )

    return send_from_directory(
        pasta_results,
        nome_arquivo
    )


# =========================================================
# ROTA DE ANÁLISE
# =========================================================

@app.route("/analisar", methods=["POST"])
def analisar():

    # -----------------------------------------------------
    # VERIFICA SE UMA IMAGEM FOI ENVIADA
    # -----------------------------------------------------

    if "imagem" not in request.files:
        return jsonify({
            "erro": "Nenhuma imagem foi enviada."
        }), 400

    imagem = request.files["imagem"]

    # -----------------------------------------------------
    # VERIFICA SE O ARQUIVO FOI SELECIONADO
    # -----------------------------------------------------

    if imagem.filename == "":
        return jsonify({
            "erro": "Nenhuma imagem selecionada."
        }), 400

    # -----------------------------------------------------
    # CRIA NOME TEMPORÁRIO
    # -----------------------------------------------------

    nome = f"{uuid.uuid4()}.png"

    caminho = os.path.join(
        "temp",
        nome
    )

    os.makedirs(
        "temp",
        exist_ok=True
    )

    # -----------------------------------------------------
    # SALVA A IMAGEM
    # -----------------------------------------------------

    imagem.save(caminho)

    try:

        # =================================================
        # EXECUTA A ANÁLISE COMPLETA
        # =================================================

        resultado = analisar_documento(caminho)

        # =================================================
        # EXIBE RESULTADOS NO TERMINAL
        # =================================================

        print("\n================================")
        print("RESULTADO DA ANÁLISE")
        print("================================")

        print("\n--- ANÁLISE GLOBAL ---")

        print(
            "Pixel Score:",
            resultado["analise_global"]["pixel_score"]
        )

        print(
            "Continuidade:",
            resultado["analise_global"]["continuity_score"]
        )

        print(
            "Maior bloco:",
            resultado["analise_global"]["max_block_score"]
        )

        print(
            "Score de Geometria:",
            resultado["analise_global"]["geometry_score"]
        )

        print(
            "Score combinado:",
            resultado["analise_global"]["combined_score"]
        )

        print(
            "Classificação:",
            resultado["analise_global"]["classification"]
        )

        print(
            "Regiões suspeitas:",
            resultado["analise_global"][
                "suspicious_geometry_regions"
            ]
        )

        print(
            "Total de regiões:",
            resultado["analise_global"][
                "total_regions"
            ]
        )

        print("\n--- ANOMALIAS REGIONAIS ---")

        print(
            "Anomalia detectada:",
            resultado["anomalia_detectada"]
        )

        print(
            "Regiões sinalizadas:",
            len(
                resultado["lista_anomalias"]
            )
        )

        print("================================\n")

        # =================================================
        # CONVERTE PARA TIPOS COMPATÍVEIS COM JSON
        # =================================================

        resultado_json = converter_json(resultado)

        return jsonify(resultado_json)

    except Exception as erro:

        print("\n================================")
        print("ERRO NA ANÁLISE")
        print("================================")
        print(erro)
        print("================================\n")

        return jsonify({
            "erro": str(erro)
        }), 500

    finally:

        # -------------------------------------------------
        # REMOVE A IMAGEM TEMPORÁRIA
        # -------------------------------------------------

        if os.path.exists(caminho):
            os.remove(caminho)


# =========================================================
# FUNÇÃO PRINCIPAL DE ANÁLISE
# =========================================================

def analisar_documento(caminho):

    # =====================================================
    # 1. ANÁLISE PIXEL GLOBAL
    # =====================================================

    print("\n[1/5] Executando análise de pixels...")

    pixel_result = analyze_continuity(
        caminho
    )


    # =====================================================
    # 2. PRÉ-PROCESSAMENTO
    # =====================================================

    print("[2/5] Executando pré-processamento...")

    image, gray = preprocess_image(
        caminho
    )


    # =====================================================
    # 3. EOCR
    # =====================================================

    print("[3/5] Executando EOCR...")

    text_regions = run_eocr(
        caminho
    )

    geo_results = analyze_text_geometry(
        text_regions
    )


    # =====================================================
    # 4. ANÁLISE PIXEL NAS REGIÕES DO EOCR
    # =====================================================

    print(
        "[4/5] Analisando pixels nas regiões textuais..."
    )

    pixel_regional_results, pixel_extras = (
        analyze_pixels_in_regions(
            gray,
            caminho,
            text_regions
        )
    )


    # =====================================================
    # 5. FUSÃO PIXEL + EOCR
    # =====================================================

    print("[5/5] Realizando fusão das análises...")

    fusion_result = fuse_scores(
        pixel_result,
        geo_results,
        pixel_regional_results
    )


    # =====================================================
    # GERA AS IMAGENS VISUAIS DA ANÁLISE
    # =====================================================

    os.makedirs("results", exist_ok=True)

    render_report(
        image_path=caminho,
        regions=text_regions,
        fused_scores=fusion_result,
        pixel_maps=pixel_extras,
        output_path="results/hybrid_analysis.png",
        xray_path="results/xray_heatmap.png"
    )


    # =====================================================
    # PREPARA LISTA DE ANOMALIAS
    # =====================================================

    lista_anomalias = []

    # controla se alguma região apresentou anomalia
    anomalies_found = False


    # =====================================================
    # ANALISA AS REGIÕES
    # =====================================================

    for i, region in enumerate(text_regions):

        # -------------------------------------------------
        # PEGA O RESULTADO DA FUSÃO
        # -------------------------------------------------

        if i >= len(fusion_result.get("regions", [])):
            continue

        regional = fusion_result["regions"][i]

        # -------------------------------------------------
        # PEGA O SCORE REGIONAL
        # -------------------------------------------------

        score = regional.get(
            "regional_score",
            0
        )

        # -------------------------------------------------
        # VERIFICA SE É ALTA SUSPEITA
        # -------------------------------------------------

        is_risk = (
            regional.get("classification")
            == "Alta suspeita"
        )

        # -------------------------------------------------
        # VERIFICA SE A REGIÃO É SUSPEITA
        # -------------------------------------------------

        if is_risk or score >= 12.0:

            anomalies_found = True

            # -------------------------------------------------
            # DEFINE CLASSIFICAÇÃO
            # -------------------------------------------------

            if is_risk:
                status = "SUSPEITA ALTA"
            else:
                status = "SUSPEITA"

            # -------------------------------------------------
            # PEGA RESULTADOS REGIONAIS
            # -------------------------------------------------

            pixel = (
                pixel_regional_results[i]
                if i < len(pixel_regional_results)
                else {}
            )

            geo = (
                geo_results[i]
                if i < len(geo_results)
                else {}
            )

            # -------------------------------------------------
            # CRIA DADOS DA ANOMALIA
            # -------------------------------------------------

            detalhe_anomalia = {

                "texto_identificado": str(
                    region.get(
                        "text",
                        ""
                    )
                ),

                "nivel_classificacao": status,

                "pontuacao_suspeita": round(
                    float(score),
                    1
                ),

                "desvio_maximo_ela": pixel.get(
                    "max_pixel_dev",
                    0
                ),

                "pixel_zscore": regional.get(
                    "pixel_zscore",
                    0
                ),

                "edge_contrast": regional.get(
                    "edge_contrast",
                    0
                ),

                "angle_dev": regional.get(
                    "angle_dev",
                    geo.get(
                        "angle_dev",
                        0
                    )
                ),

                "density_z": regional.get(
                    "density_z",
                    geo.get(
                        "density_z",
                        0
                    )
                )
            }

            # -------------------------------------------------
            # ADICIONA NA LISTA
            # -------------------------------------------------

            lista_anomalias.append(
                detalhe_anomalia
            )

            # -------------------------------------------------
            # MOSTRA NO TERMINAL
            # -------------------------------------------------

            print(
                f"\n • [{status}] "
                f"Região {i + 1}"
            )

            print(
                f"   Texto identificado : "
                f"'{region.get('text', '')}'"
            )

            print(
                f"   Score regional     : "
                f"{float(score):.2f}/100"
            )

            print(
                f"   Pixel Z-Score      : "
                f"{regional.get('pixel_zscore', 0)}"
            )

            print(
                f"   Pico Pixel (ELA)   : "
                f"{pixel.get('max_pixel_dev', 0)}"
            )

            print(
                f"   Edge Contrast      : "
                f"{regional.get('edge_contrast', 0)}"
            )

            print(
                f"   Desvio Angular     : "
                f"{regional.get('angle_dev', 0)}"
            )

            print(
                f"   Densidade Z        : "
                f"{regional.get('density_z', 0)}"
            )

            print("-" * 65)


    # =====================================================
    # RESULTADO NO FORMATO ANTIGO
    # =====================================================

    resultado = {

        # caminho da imagem analisada
        "caminho_imagem": caminho,

        # quantidade total de regiões encontradas
        "total_regioes_texto": len(
            text_regions
        ),

        # resultado global completo da fusão
        "analise_global": fusion_result["global"],

        # informa se alguma anomalia foi encontrada
        "anomalia_detectada": anomalies_found,

        # somente as regiões consideradas suspeitas
        "lista_anomalias": lista_anomalias,

        # arquivos gerados pela análise
        "arquivos_gerados": [
            "/results/hybrid_analysis.png",
            "/results/xray_heatmap.png",
            "/results/continuity_map.png",
            "/results/continuity_heatmap.png"
        ]
    }


    # =====================================================
    # MOSTRA O RESULTADO FINAL
    # =====================================================

    print("\n" + "=" * 65)
    print("              RESULTADO FINAL")
    print("=" * 65)

    if anomalies_found:

        print(
            " ⚠ Foram encontradas regiões "
            "com possíveis anomalias."
        )

        print(
            f" • Regiões sinalizadas: "
            f"{len(lista_anomalias)}"
        )

    else:

        print(
            " ✓ Nenhuma anomalia regional "
            "foi detectada."
        )

    print(
        f" • Classificação global: "
        f"{fusion_result['global']['classification']}"
    )

    print(
        f" • Score global: "
        f"{fusion_result['global']['combined_score']:.2f}/100"
    )

    print("=" * 65)

    print("\n Relatórios gerados:")

    print(
        "   1. results/hybrid_analysis.png"
        "       → análise regional"
    )

    print(
        "   2. results/xray_heatmap.png"
        "             → mapa ELA"
    )

    print(
        "   3. results/continuity_map.png"
        "        → mapa de continuidade"
    )

    print(
        "   4. results/continuity_heatmap.png"
        "  → mapa do Pixel Core"
    )


    # =====================================================
    # CONVERTE RESULTADO PARA JSON
    # =====================================================

    return converter_json(
        resultado
    )


# =========================================================
# EXECUÇÃO DO FLASK
# =========================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
