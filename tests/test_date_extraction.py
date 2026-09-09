import pytest

from analyzers.ocr_analyzer import OCRAnalyzer


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("Nascimento: 22/05/2008", ["22/05/2008"]),
        ("Emissão: 2-9-2026", ["02/09/2026"]),
        ("Validade: 09.09.2030", ["09/09/2030"]),
        ("Dia: 22 / Mês: 05 / Ano: 2024", ["22/05/2024"]),
        ("Dia: 22 / Més: 05 / Ano: 2024", ["22/05/2024"]),
        ("Dia: 22\nMes: 05\nAno: 2024", ["22/05/2024"]),
        ("Ribeirão Pires, 7 de setembro de 2026", ["07/09/2026"]),
        ("São Paulo, 15 de março de 2025", ["15/03/2025"]),
    ],
)
def test_extrai_e_normaliza_formatos_de_data(texto, esperado):
    assert OCRAnalyzer()._extract_dates(texto) == esperado


def test_ignora_datas_impossiveis():
    texto = "Datas inválidas: 31/02/2025 e 40/15/2026"

    assert OCRAnalyzer()._extract_dates(texto) == []


def test_remove_datas_repetidas_preservando_a_ordem():
    texto = "Nascimento 22/05/2008. Confirmação: 22 de maio de 2008. Emissão 01/09/2026."

    assert OCRAnalyzer()._extract_dates(texto) == ["22/05/2008", "01/09/2026"]

