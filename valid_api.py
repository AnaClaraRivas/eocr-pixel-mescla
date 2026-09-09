"""Rotas do VALID integradas sem modificar o pipeline EOCR/Pixel existente."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
import os
import tempfile

from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

from analyzers.document_comparator import DocumentComparator
from analyzers.metadata_analyzer import MetadataAnalyzer
from analyzers.ocr_analyzer import OCRAnalyzer


valid_bp = Blueprint("valid", __name__, url_prefix="/valid")

EXTENSOES_PERMITIDAS = {".jpg", ".jpeg", ".png", ".pdf"}
ocr = OCRAnalyzer()
metadata = MetadataAnalyzer()
comparador = DocumentComparator()


def _json_seguro(valor):
    if is_dataclass(valor):
        return _json_seguro(asdict(valor))
    if isinstance(valor, dict):
        return {str(chave): _json_seguro(item) for chave, item in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_json_seguro(item) for item in valor]
    if hasattr(valor, "item"):
        return _json_seguro(valor.item())
    return valor


def _validar_arquivo(arquivo, campo):
    if arquivo is None or not arquivo.filename:
        raise ValueError(f"Envie o arquivo no campo '{campo}'.")

    nome = secure_filename(arquivo.filename)
    extensao = os.path.splitext(nome)[1].lower()
    if extensao not in EXTENSOES_PERMITIDAS:
        permitidas = ", ".join(sorted(EXTENSOES_PERMITIDAS))
        raise ValueError(f"Formato não permitido. Use: {permitidas}.")
    return extensao


def _salvar_temporario(arquivo, campo):
    extensao = _validar_arquivo(arquivo, campo)
    temporario = tempfile.NamedTemporaryFile(delete=False, suffix=extensao)
    temporario.close()
    arquivo.save(temporario.name)
    return temporario.name


def _analisar(caminho):
    resultado_ocr = ocr.analyze(caminho)
    resultado_metadata = metadata.analyze(caminho)
    return {
        "ocr": _json_seguro(resultado_ocr),
        "metadados": _json_seguro(resultado_metadata),
    }, resultado_ocr


@valid_bp.get("/")
def status():
    return jsonify({
        "sistema": "VALID",
        "status": "funcionando",
        "rotas": ["/valid/analisar", "/valid/comparar"],
    })


@valid_bp.post("/analisar")
def analisar_documento_valid():
    caminho = None
    try:
        caminho = _salvar_temporario(request.files.get("arquivo"), "arquivo")
        resultado, _ = _analisar(caminho)
        return jsonify(resultado)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    except Exception as erro:
        return jsonify({"erro": str(erro)}), 500
    finally:
        if caminho and os.path.exists(caminho):
            os.remove(caminho)


@valid_bp.post("/comparar")
def comparar_documentos_valid():
    caminhos = []
    try:
        caminho1 = _salvar_temporario(request.files.get("documento1"), "documento1")
        caminhos.append(caminho1)
        caminho2 = _salvar_temporario(request.files.get("documento2"), "documento2")
        caminhos.append(caminho2)

        resultado1, ocr1 = _analisar(caminho1)
        resultado2, ocr2 = _analisar(caminho2)

        if not ocr1.success or not ocr2.success:
            return jsonify({
                "erro": "Não foi possível analisar um ou ambos os documentos.",
                "documento1": resultado1,
                "documento2": resultado2,
            }), 422

        return jsonify({
            "documento1": resultado1,
            "documento2": resultado2,
            "comparacao": _json_seguro(comparador.compare(ocr1, ocr2)),
        })
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    except Exception as erro:
        return jsonify({"erro": str(erro)}), 500
    finally:
        for caminho in caminhos:
            if os.path.exists(caminho):
                os.remove(caminho)
