import fitz
from PIL import Image

from analyzers.metadata_analyzer import MetadataAnalyzer


def test_imagem_sem_exif_nao_aumenta_score(tmp_path):
    caminho = tmp_path / "sem_exif.jpg"
    Image.new("RGB", (20, 10), "white").save(caminho)

    resultado = MetadataAnalyzer().analyze(str(caminho))

    assert resultado.success
    assert resultado.score == 0
    assert resultado.evidences[0].code == "NO_EXIF"


def test_detecta_software_de_edicao_no_exif(tmp_path):
    caminho = tmp_path / "editada.jpg"
    exif = Image.Exif()
    exif[305] = "Adobe Photoshop"
    Image.new("RGB", (20, 10), "white").save(caminho, exif=exif)

    resultado = MetadataAnalyzer().analyze(str(caminho))

    assert resultado.data["software"] == "Adobe Photoshop"
    assert resultado.score == 5
    assert resultado.evidences[0].code == "EDITING_SOFTWARE"
    assert "não comprova adulteração" in resultado.evidences[0].message


def test_detecta_software_de_edicao_em_pdf(tmp_path):
    caminho = tmp_path / "editado.pdf"
    pdf = fitz.open()
    pdf.new_page()
    pdf.set_metadata({"creator": "Canva", "producer": "Gerador PDF"})
    pdf.save(caminho)
    pdf.close()

    resultado = MetadataAnalyzer().analyze(str(caminho))

    assert resultado.success
    assert resultado.data["pages"] == 1
    assert resultado.score == 5
    assert resultado.evidences[0].code == "EDITING_SOFTWARE"


def test_arquivo_nao_suportado_retorna_falha(tmp_path):
    caminho = tmp_path / "arquivo.txt"
    caminho.write_text("teste", encoding="utf-8")

    resultado = MetadataAnalyzer().analyze(str(caminho))

    assert not resultado.success
    assert resultado.warnings == ["Formato de arquivo não suportado."]

