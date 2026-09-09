"""
cpf_from_image.py

Extração de CPF diretamente da IMAGEM, não só do texto corrido do OCR.

Por que isso ajuda mais que corrigir o texto depois?
    Quando o Tesseract roda em modo "página inteira" (--psm 3, o padrão), ele
    tenta decidir sozinho o que é letra e o que é número em cada palavra,
    então erros como "0"->"O" ou perder um dígito colado são comuns.

    Se a gente já sabe ONDE está o campo CPF (via image_to_data, que devolve
    a posição de cada palavra reconhecida), dá pra recortar só aquela região
    e reprocessar ela sozinha com:
        --psm 7                          -> trata a região como 1 linha só
        -c tessedit_char_whitelist=0-9.-  -> proíbe o Tesseract de "ver" letras

    Isso reduz MUITO os erros de confusão letra/dígito, porque tira a
    ambiguidade do próprio motor de OCR, em vez de tentar adivinhar depois.

Fluxo:
    1. image_to_data() na imagem inteira -> acha a palavra "CPF" e sua posição
    2. Recorta uma faixa à direita/abaixo do rótulo (onde o valor deve estar)
    3. Reprocessa essa faixa recortada com whitelist de dígitos
    4. Passa o resultado pelo cpf_utils.find_cpf() já existente

Requisitos: pytesseract, Pillow (já devem estar no requirements.txt do projeto,
como o OCR já é usado no core/analyzers).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pytesseract
from PIL import Image

from core.cpf_validator import CpfResult, find_cpf


@dataclass
class CpfRegion:
    """Coordenadas (em pixels) da região onde o valor do CPF deve estar."""
    left: int
    top: int
    width: int
    height: int


def locate_cpf_label(image: Image.Image) -> Optional[CpfRegion]:
    """
    Roda OCR na imagem inteira em modo 'dados' (não só texto) para achar
    a posição da palavra 'CPF' e, a partir dela, das palavras seguintes
    NA MESMA LINHA que compõem o valor do CPF.

    Importante: não assumimos uma largura fixa de recorte. Documentos reais
    costumam ter outros campos logo depois do CPF na mesma linha (ex:
    "CPF 470.764.086-91 RG: 58.347.217-5"), então cortar por uma largura
    fixa em pixels facilmente gruda o campo seguinte junto — foi
    exatamente o que aconteceu ao testar com um documento real, onde
    "RG:" ficava a poucos pixels do CPF.

    Em vez disso, usamos as PRÓPRIAS palavras que o Tesseract já
    reconheceu (via line_num) e paramos de incluir palavras assim que
    encontramos uma que contenha letra — um valor de CPF só deve ter
    dígitos, ponto e hífen.
    """
    data = pytesseract.image_to_data(image, lang="por", output_type=pytesseract.Output.DICT)

    candidatos_rotulo = {"CPF", "CPF:", "CPE", "GPF", "OPF"}

    n = len(data["text"])

    for i in range(n):
        palavra = data["text"][i].strip().upper().rstrip(":")

        if palavra not in candidatos_rotulo and not palavra.startswith("CPF"):
            continue

        linha_rotulo = data["line_num"][i]
        bloco_rotulo = data["block_num"][i]
        paragrafo_rotulo = data["par_num"][i]

        # percorre as próximas palavras da MESMA linha, coletando só as
        # que parecem parte do valor do CPF (dígitos/pontuação, sem letra)
        caixas_valor = []

        for j in range(i + 1, n):

            mesma_linha = (
                data["block_num"][j] == bloco_rotulo
                and data["par_num"][j] == paragrafo_rotulo
                and data["line_num"][j] == linha_rotulo
            )

            if not mesma_linha:
                break

            candidato = data["text"][j].strip()

            if not candidato:
                continue

            # para assim que a palavra tiver qualquer letra (ex: "RG:",
            # "ELEITOR", etc.) — o valor do CPF não deveria conter letras
            if any(c.isalpha() for c in candidato):
                break

            caixas_valor.append((
                data["left"][j], data["top"][j],
                data["width"][j], data["height"][j],
            ))

            # um CPF formatado cabe numa única palavra reconhecida
            # (ex: "470.764.086-91"); se já achamos uma, não precisa
            # continuar juntando mais palavras
            if len(candidato) >= 8:
                break

        if not caixas_valor:
            continue

        esquerda = min(c[0] for c in caixas_valor)
        topo = min(c[1] for c in caixas_valor)
        direita = max(c[0] + c[2] for c in caixas_valor)
        base = max(c[1] + c[3] for c in caixas_valor)

        # pequena folga ao redor da caixa real, só o suficiente para não
        # cortar bordas de caracteres — não é mais um chute de largura
        margem = 6

        return CpfRegion(
            left=esquerda - margem,
            top=topo - margem,
            width=(direita - esquerda) + margem * 2,
            height=(base - topo) + margem * 2,
        )

    return None


def crop_region(image: Image.Image, region: CpfRegion) -> Image.Image:
    box = (
        max(region.left, 0),
        max(region.top, 0),
        max(region.left, 0) + region.width,
        max(region.top, 0) + region.height,
    )
    return image.crop(box)


def ocr_digits_only(cropped: Image.Image) -> str:
    """
    Reprocessa a região recortada com configuração restrita a dígitos e
    pontuação de CPF. Isso é o que realmente reduz os erros na origem.
    """
    config = "--psm 7 -c tessedit_char_whitelist=0123456789.-"
    return pytesseract.image_to_string(cropped, config=config)


def extract_cpf_from_region(image: Image.Image) -> Optional[CpfResult]:
    """
    Recebe uma imagem JÁ ABERTA em memória (ex: a mesma imagem que o
    OCRAnalyzer já carregou) e tenta extrair o CPF isolando a região do
    campo. Retorna None se o rótulo "CPF" nem foi encontrado na imagem
    (nesse caso, quem chamou deve continuar usando o resultado do texto
    de página inteira, não há nada de novo a tentar aqui).

    Esta função não decide sozinha entre a leitura de página inteira e a
    leitura isolada — quem chama (ex: OCRAnalyzer) é responsável por essa
    escolha, com base no que faz mais sentido para o pipeline.
    """
    region = locate_cpf_label(image)
    if region is None:
        return None

    recorte = crop_region(image, region)
    texto_regiao = ocr_digits_only(recorte)

    return find_cpf(f"CPF {texto_regiao}")  # reaproveita o parser do cpf_validator


def extract_cpf_from_image(image_path: str) -> CpfResult:
    """
    Ponto de entrada para uso standalone (linha de comando): recebe o
    caminho da imagem do documento e devolve um CpfResult.
    """
    image = Image.open(image_path)

    resultado = extract_cpf_from_region(image)

    # Se o rótulo não foi achado, ou mesmo isolando a região o resultado
    # não veio limpo, cai pro texto de página inteira como reforço.
    if resultado is None or resultado.status in ("not_found", "invalid"):
        texto_completo = pytesseract.image_to_string(image, lang="por")
        resultado_completo = find_cpf(texto_completo)

        if resultado is None:
            return resultado_completo

        if resultado_completo.status in ("valid", "corrected"):
            return resultado_completo

    return resultado


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("uso: python cpf_from_image.py <caminho_da_imagem>")
        sys.exit(1)

    resultado = extract_cpf_from_image(sys.argv[1])
    print(f"status: {resultado.status}")
    print(f"value: {resultado.value}")
    print(f"candidates: {resultado.candidates}")
    print(f"raw_ocr_text: {resultado.raw_ocr_text!r}")
