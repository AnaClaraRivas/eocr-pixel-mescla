from analyzers.document_comparator import DocumentComparator
from core.analysis_result import AnalysisResult


def documento(nome=None, cpf=None, cpf_status=None, datas=None):
    return AnalysisResult(
        success=True,
        module="ocr",
        data={
            "fields": {
                "nome": nome,
                "cpf": cpf,
                "cpf_status": cpf_status,
                "datas": datas or [],
            }
        },
    )


def test_documentos_com_dados_validos_iguais_sao_compativeis():
    primeiro = documento("Ana de Souza", "11144477735", "valid", ["10/02/2000"])
    segundo = documento("ANA SOUZA", "111.444.777-35", "valid", ["10-02-2000"])

    resultado = DocumentComparator().compare(primeiro, segundo)

    assert resultado["status"] == "COMPATIVEL"
    assert resultado["compatibilidade"] == 100


def test_um_unico_campo_igual_nao_e_suficiente():
    primeiro = documento(datas=["01/01/2024"])
    segundo = documento(datas=["01/01/2024"])

    resultado = DocumentComparator().compare(primeiro, segundo)

    assert resultado["compatibilidade"] == 100
    assert resultado["status"] == "SEM DADOS SUFICIENTES"


def test_cpf_invalido_igual_exige_revisao():
    primeiro = documento("Ricardo Cavalcante", "34211988504", "invalid")
    segundo = documento("Ricardo Cavalcante", "34211988504", "invalid")

    resultado = DocumentComparator().compare(primeiro, segundo)

    assert resultado["campos"]["cpf"] == "INVALIDO"
    assert resultado["status"] == "REQUER_REVISAO"
    assert resultado["compatibilidade"] < 100


def test_nome_cortado_pelo_ocr_e_parcialmente_compativel():
    primeiro = documento("Ricardo Cavalcante de Albuquerque")
    segundo = documento("Ricardo Cavalcante")

    resultado = DocumentComparator().compare(primeiro, segundo)

    assert resultado["campos"]["nome"] == "PARCIALMENTE_COMPATIVEL"
    assert resultado["detalhes"]["nome_similaridade"] == 0.67


def test_cpfs_validos_diferentes_sao_divergentes():
    primeiro = documento("Ana Souza", "11144477735", "valid")
    segundo = documento("Ana Souza", "52998224725", "valid")

    resultado = DocumentComparator().compare(primeiro, segundo)

    assert resultado["campos"]["cpf"] == "DIVERGENTE"
    assert resultado["status"] == "INCONSISTENTE"

