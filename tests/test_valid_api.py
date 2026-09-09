from io import BytesIO
import sys
import types


class _LeitorEasyOCRFalso:
    def __init__(self, *args, **kwargs):
        pass

    def readtext(self, *args, **kwargs):
        return []


sys.modules.setdefault(
    "easyocr",
    types.SimpleNamespace(Reader=_LeitorEasyOCRFalso),
)

from app import app


def test_status_valid():
    cliente = app.test_client()
    resposta = cliente.get("/valid/")

    assert resposta.status_code == 200
    assert resposta.get_json()["status"] == "funcionando"


def test_analisar_exige_arquivo():
    cliente = app.test_client()
    resposta = cliente.post("/valid/analisar")

    assert resposta.status_code == 400
    assert "arquivo" in resposta.get_json()["erro"]


def test_analisar_rejeita_extensao_nao_permitida():
    cliente = app.test_client()
    resposta = cliente.post(
        "/valid/analisar",
        data={"arquivo": (BytesIO(b"texto"), "documento.txt")},
        content_type="multipart/form-data",
    )

    assert resposta.status_code == 400
    assert "Formato não permitido" in resposta.get_json()["erro"]


def test_rota_original_continua_disponivel():
    cliente = app.test_client()
    resposta = cliente.get("/")

    assert resposta.status_code == 200
    assert resposta.get_data(as_text=True) == "API funcionando!"
