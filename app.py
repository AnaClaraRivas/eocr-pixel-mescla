from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import os
import uuid

from pixels.analyzer import analyze_continuity
from pixels.preprocessing import preprocess_image

from eocr.eocr_engine import run_eocr
from eocr.font_geometry import analyze_text_geometry
from eocr.pixel_analyzer import analyze_pixels_in_regions

from fusion.fusion_scorer import fuse_scores
from flask import Flask, request, jsonify, send_from_directory


app = Flask(__name__)
CORS(app)


# =========================================================
# CONVERSÃO PARA JSON
# =========================================================

def converter_json(obj):

    # Dicionário
    if isinstance(obj, dict):
        return {
            str(chave): converter_json(valor)
            for chave, valor in obj.items()
        }

    # Lista
    if isinstance(obj, list):
        return [
            converter_json(valor)
            for valor in obj
        ]

    # Tupla
    if isinstance(obj, tuple):
        return [
            converter_json(valor)
            for valor in obj
        ]

    # Tipos NumPy
    if hasattr(obj, "item"):
        return converter_json(obj.item())

    # Arrays NumPy
    if hasattr(obj, "tolist"):
        return converter_json(obj.tolist())

    # Outros valores
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

        # -------------------------------------------------
        # PIXEL
        # -------------------------------------------------

        print("\n--- PIXEL ---")

        print(
            "Pixel fraud score:",
            resultado["pixel"]["pixel_score"]
        )

        print(
            "Continuidade:",
            resultado["pixel"]["continuity_score"]
        )

        print(
            "Maior bloco:",
            resultado["pixel"]["max_block_score"]
        )

        print(
            "Classificação:",
            resultado["pixel"]["classification"]
        )

        print(
            "Blocos suspeitos:",
            len(
                resultado["pixel"]["suspicious_blocks"]
            )
        )

        print(
            "Anomalias de vizinhança:",
            len(
                resultado["pixel"]["neighbor_anomalies"]
            )
        )

        # -------------------------------------------------
        # EOCR
        # -------------------------------------------------

        print("\n--- EOCR ---")

        print(
            "Regiões analisadas:",
            resultado["eocr"]["total_regions"]
        )

        print(
            "Regiões suspeitas:",
            resultado["eocr"]["suspicious_regions"]
        )

        # -------------------------------------------------
        # FUSÃO
        # -------------------------------------------------

        print("\n--- FUSÃO ---")

        print(
            "Score Pixel:",
            resultado["fusion"]["pixel_score"]
        )

        print(
            "Score EOCR:",
            resultado["fusion"]["geometry_score"]
        )

        print(
            "Score combinado:",
            resultado["fusion"]["combined_score"]
        )

        print(
            "Classificação final:",
            resultado["fusion"]["classification"]
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
    # PREPARA REGIÕES DO EOCR
    # =====================================================

    eocr_regions = []

    for i, region in enumerate(text_regions):

        # -------------------------------------------------
        # Resultado geométrico
        # -------------------------------------------------

        geo = (
            geo_results[i]
            if i < len(geo_results)
            else {}
        )

        # -------------------------------------------------
        # Resultado pixel regional
        # -------------------------------------------------

        pixel = (
            pixel_regional_results[i]
            if i < len(pixel_regional_results)
            else {}
        )

        # -------------------------------------------------
        # Monta região
        # -------------------------------------------------

        eocr_regions.append({

            "index": int(i),

            "text": str(
                region.get(
                    "text",
                    ""
                )
            ),

            "confidence": round(
                float(
                    region.get(
                        "confidence",
                        0
                    )
                ),
                2
            ),

            "angle": round(
                float(
                    region.get(
                        "angle",
                        0
                    )
                ),
                2
            ),

            "angle_dev": round(
                float(
                    geo.get(
                        "angle_dev",
                        0
                    )
                ),
                2
            ),

            "density_z": round(
                float(
                    geo.get(
                        "density_z",
                        0
                    )
                ),
                2
            ),

            "geo_suspicious": bool(
                geo.get(
                    "geo_suspicious",
                    False
                )
            ),

            "ela_val": round(
                float(
                    pixel.get(
                        "ela_val",
                        0
                    )
                ),
                2
            ),

            "max_pixel_dev": round(
                float(
                    pixel.get(
                        "max_pixel_dev",
                        0
                    )
                ),
                2
            ),

            "edge_contrast": round(
                float(
                    pixel.get(
                        "edge_contrast",
                        0
                    )
                ),
                2
            )
        })


    # =====================================================
    # CONTA REGIÕES SUSPEITAS
    # =====================================================

    suspicious_regions = sum(

        1

        for region in eocr_regions

        if bool(
            region["geo_suspicious"]
        )
    )


    # =====================================================
    # RESULTADO FINAL
    # =====================================================

    resultado = {

        # =================================================
        # PIXEL
        # =================================================

        "pixel": {

            "pixel_score":
                fusion_result["global"]["pixel_score"],

            "continuity_score":
                fusion_result["global"]["continuity_score"],

            "max_block_score":
                fusion_result["global"]["max_block_score"],

            "classification":
                fusion_result["global"]["pixel_classification"],

            "suspicious_blocks":
                pixel_result.get(
                    "suspicious_blocks",
                    []
                ),

            "neighbor_anomalies":
                pixel_result.get(
                    "neighbor_anomalies",
                    []
                ),

            "heatmap":
                pixel_result.get(
                    "heatmap",
                    None
                )
        },


        # =================================================
        # EOCR
        # =================================================

        "eocr": {

            "total_regions":
                len(eocr_regions),

            "suspicious_regions":
                suspicious_regions,

            "regions":
                eocr_regions
        },


        # =================================================
        # FUSÃO
        # =================================================

        "fusion": {

            "pixel_score":
                fusion_result["global"]["pixel_score"],

            "geometry_score":
                fusion_result["global"]["geometry_score"],

            "combined_score":
                fusion_result["global"]["combined_score"],

            "classification":
                fusion_result["global"]["classification"],

            "suspicious_geometry_regions":
                fusion_result["global"][
                    "suspicious_geometry_regions"
                ],

            "total_regions":
                fusion_result["global"][
                    "total_regions"
                ]
        },


        # =================================================
        # RESULTADOS REGIONAIS DA FUSÃO
        # =================================================

        "regions":
            fusion_result.get(
                "regions",
                []
            )
    }


    # =====================================================
    # RETORNA RESULTADO
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

# imagens
@app.route("/results/<path:nome_arquivo>")
def resultados(nome_arquivo):
    return send_from_directory(
        "results",
        nome_arquivo
    )