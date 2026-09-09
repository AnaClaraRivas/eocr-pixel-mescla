import os
import re
import io
import time
import shutil
import platform
import unicodedata

from datetime import date

import fitz  # PyMuPDF
import pytesseract

from PIL import Image, ImageOps


def _configurar_tesseract():
    """
    Descobre o executável do Tesseract sem depender de um caminho fixo
    de Windows. Ordem de prioridade:

      1. Variável de ambiente TESSERACT_CMD, se o usuário quiser forçar
         um caminho específico (ex: instalação não padrão).
      2. `tesseract` já no PATH do sistema (funciona out-of-the-box em
         Linux/Mac quando instalado via apt/brew).
      3. Caminhos padrão conhecidos de instalação no Windows, como
         fallback só quando os anteriores falharem.

    Se nada for encontrado, deixa o pytesseract com o comportamento
    padrão (ele mesmo vai lançar um erro claro na hora do uso, em vez
    de travar silenciosamente aqui na importação do módulo).
    """

    caminho_env = os.environ.get("TESSERACT_CMD")
    if caminho_env and os.path.isfile(caminho_env):
        pytesseract.pytesseract.tesseract_cmd = caminho_env
        return

    caminho_path = shutil.which("tesseract")
    if caminho_path:
        pytesseract.pytesseract.tesseract_cmd = caminho_path
        return

    if platform.system() == "Windows":
        candidatos_windows = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ]
        for candidato in candidatos_windows:
            if os.path.isfile(candidato):
                pytesseract.pytesseract.tesseract_cmd = candidato
                return


_configurar_tesseract()

from core.analysis_result import AnalysisResult
from core.evidence import Evidence
from core.cpf_validator import find_cpf
from analyzers.cpf_from_image import extract_cpf_from_region


class OCRAnalyzer:

    # Padrões usados para localizar datas no texto reconhecido pelo OCR.
    # O CPF não usa mais regex simples aqui: a extração, validação de
    # dígito verificador e correção de erros de OCR ficam a cargo de
    # core.cpf_validator.find_cpf(), que é bem mais robusto.
    DATE_NUMERIC_PATTERN = re.compile(
        r"(?<!\d)(\d{1,2})\s*[/.-]\s*(\d{1,2})\s*[/.-]\s*(\d{4})(?!\d)"
    )
    DATE_FIELDS_PATTERN = re.compile(
        r"(?i)dia\s*:?\s*(\d{1,2})\s*[/|,;\-]*\s*"
        # O OCR pode trocar o acento circunflexo de "Mês" por agudo
        # ("Més") ou remover o acento ("Mes"). Aceitamos as três formas.
        r"m[eéê]s\s*:?\s*(\d{1,2})\s*[/|,;\-]*\s*"
        r"ano\s*:?\s*(\d{4})"
    )
    DATE_WRITTEN_PATTERN = re.compile(
        r"(?i)(?<!\d)(\d{1,2})\s+de\s+"
        r"([a-záàâãéêíóôõúç]+)\s+de\s+(\d{4})(?!\d)"
    )
    _MESES = {
        "janeiro": 1, "fevereiro": 2, "marco": 3, "abril": 4,
        "maio": 5, "junho": 6, "julho": 7, "agosto": 8,
        "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
    }
    # "Nome:" seguido do valor, aceitando tanto TUDO EM MAIÚSCULAS (comum em
    # certidões/documentos oficiais brasileiros, ex: "RICARDO CAVALCANTE")
    # quanto Title Case (comum em RGs de modelo mais novo, ex: "Ana Souza").
    # Cada palavra precisa começar com maiúscula; o resto pode ser
    # maiúsculo ou minúsculo. Tolerância de distância generosa (até 40
    # caracteres) cobre rótulos bilíngues tipo "Nome / Name" com o valor
    # na linha seguinte. O lookahead negativo evita casar com "Nome
    # Social", que costuma vir logo depois e ficar vazio na maioria dos
    # documentos.
    NAME_PATTERN = re.compile(
        r"(?i:nome)(?!\s*social).{0,40}?"
        r"([A-ZÀ-Ú][A-Za-zà-ú]*"
        r"(?:[ \t]+(?!(?i:nome\s+social))[A-ZÀ-Ú][A-Za-zà-ú]*)+)",
        re.DOTALL,
    )

    # Palavras comuns em cabeçalhos institucionais, usadas para DESCARTAR
    # linhas que claramente não são nome de pessoa, no fallback heurístico
    # abaixo (usado quando não existe rótulo "Nome:" explícito no
    # documento — comum em carteirinhas/crachás/cartões diversos).
    _PALAVRAS_NAO_NOME = {
        "GOVERNO", "ESTADO", "FEDERAL", "FEDERATIVA", "REPUBLICA", "REPÚBLICA",
        "BRASIL", "SECRETARIA", "SEGURANCA", "SEGURANÇA", "DISTRITO",
        "CARTEIRA", "IDENTIDADE", "REGISTRO", "GERAL", "PERSONAL", "NUMBER",
        "CENTRO", "PAULA", "SOUZA", "ENSINO", "MEDIO", "MÉDIO", "INFO", "NET",
        "MANHA", "MANHÃ", "ETEC", "PROFA", "PROFESSORA", "SAO", "SÃO", "PAULO",
        "RIBEIRAO", "RIBEIRÃO", "PIRES", "ESCOLAR", "GRATUITO", "STUD",
        "CARTAO", "CARTÃO", "ATENDIMENTO", "CENTRAL", "GOVERNO", "TIPO",
    }

    # Abaixo desse valor (0-100), consideramos o texto pouco confiável
    MIN_CONFIDENCE = 60


    def _linha_parece_nome(self, linha):
        """
        Heurística simples: uma linha 'parece nome de pessoa' se tem entre
        2 e 6 palavras, todas compostas só de letras, e a MAIORIA delas não
        é uma palavra institucional conhecida (ver _PALAVRAS_NAO_NOME).
        Não é infalível — é só um fallback para quando não há rótulo
        explícito no documento.
        """
        limpo = linha.strip().rstrip(".").strip()
        palavras = limpo.split()

        if not (2 <= len(palavras) <= 6):
            return False

        if not all(re.fullmatch(r"[A-ZÀ-Ú][A-Za-zà-ú]*", p) for p in palavras):
            return False

        palavras_maiusculas = {p.upper() for p in palavras}
        intersecao = palavras_maiusculas & self._PALAVRAS_NAO_NOME

        # se metade ou mais das palavras da linha são termos institucionais
        # conhecidos, não tratamos como nome
        if len(intersecao) >= len(palavras) / 2:
            return False

        return True


    def _extract_name_heuristic(self, text):
        """
        Fallback para documentos sem rótulo 'Nome:' explícito (ex: cards
        que listam o nome direto, sem label). Varre as linhas do texto
        procurando a que mais parece um nome de pessoa, priorizando a
        linha com mais palavras (nomes completos tendem a ter mais).
        """
        candidatos = [
            linha.strip().rstrip(".")
            for linha in text.splitlines()
            if self._linha_parece_nome(linha)
        ]

        if not candidatos:
            return None

        candidatos.sort(key=lambda linha: len(linha.split()), reverse=True)
        return candidatos[0]


    def analyze(self, file_path):

        start = time.time()

        try:

            extension = os.path.splitext(file_path)[1].lower()


            if extension == ".pdf":

                data, evidences = self._analyze_pdf(file_path)


            elif extension in [".jpg", ".jpeg", ".png"]:

                data, evidences = self._analyze_image(file_path)


            else:

                return AnalysisResult(
                    success=False,
                    module="ocr",
                    warnings=[
                        "Formato de arquivo não suportado."
                    ]
                )


            score = sum(evidence.weight for evidence in evidences)


            return AnalysisResult(

                success=True,

                module="ocr",

                score=score,

                data=data,

                evidences=evidences,

                execution_time=time.time() - start

            )


        except Exception as e:

            return AnalysisResult(

                success=False,

                module="ocr",

                warnings=[
                    str(e)
                ]

            )


    # ---------- PDF ----------

    def _analyze_pdf(self, file_path):

        pdf = fitz.open(file_path)

        full_text = ""
        confidences = []
        primeira_pagina_imagem = None

        for indice, page in enumerate(pdf):

            # renderiza a página em resolução maior para melhorar a leitura do OCR
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            image = Image.open(io.BytesIO(pix.tobytes("png")))

            if indice == 0:
                primeira_pagina_imagem = image

            text, page_confidences = self._ocr_image(image)

            full_text += text + "\n"
            confidences.extend(page_confidences)

        fields = self._extract_fields(full_text, image=primeira_pagina_imagem)
        avg_confidence = self._average_confidence(confidences)

        evidences = self._build_evidences(full_text, fields, avg_confidence)

        return {

            "type": "PDF",
            "pages": len(pdf),
            "text": full_text.strip(),
            "fields": fields,
            "confidence": avg_confidence

        }, evidences


    # ---------- IMAGEM ----------

    def _analyze_image(self, file_path):

        # Fotos tiradas com celular frequentemente têm uma tag EXIF de
        # orientação (rotação) que os visualizadores de imagem aplicam
        # automaticamente na hora de exibir, mas o PIL NÃO aplica sozinho
        # ao abrir o arquivo. Sem essa correção, o Tesseract lê os pixels
        # crus (a imagem "deitada"), o que produz texto completamente
        # embaralhado, mesmo a foto aparecendo em pé em qualquer visualizador.
        image = ImageOps.exif_transpose(Image.open(file_path))

        text, confidences = self._ocr_image(image)

        fields = self._extract_fields(text, image=image)
        avg_confidence = self._average_confidence(confidences)

        evidences = self._build_evidences(text, fields, avg_confidence)

        return {

            "type": "IMAGE",
            "text": text.strip(),
            "fields": fields,
            "confidence": avg_confidence

        }, evidences


    # ---------- OCR ----------

    def _ocr_image(self, image):

        # texto puro reconhecido
        text = pytesseract.image_to_string(image, lang="por")

        # dados detalhados, incluindo confiança por palavra reconhecida
        details = pytesseract.image_to_data(
            image, lang="por", output_type=pytesseract.Output.DICT
        )

        confidences = [
            int(c) for c in details.get("conf", [])
            if str(c).lstrip("-").isdigit() and int(c) >= 0
        ]

        return text, confidences


    def _average_confidence(self, confidences):

        if not confidences:
            return 0.0

        return round(sum(confidences) / len(confidences), 2)


    # ---------- EXTRAÇÃO DE CAMPOS ----------

    @staticmethod
    def _normalizar_texto(texto):
        return "".join(
            caractere
            for caractere in unicodedata.normalize("NFD", texto.lower())
            if unicodedata.category(caractere) != "Mn"
        )


    @staticmethod
    def _formatar_data_valida(dia, mes, ano):
        try:
            valor = date(int(ano), int(mes), int(dia))
        except (TypeError, ValueError):
            return None

        return valor.strftime("%d/%m/%Y")


    def _extract_dates(self, text):
        """Extrai, valida e normaliza datas encontradas no texto do OCR."""
        encontradas = []

        def adicionar(dia, mes, ano):
            data_formatada = self._formatar_data_valida(dia, mes, ano)
            if data_formatada and data_formatada not in encontradas:
                encontradas.append(data_formatada)

        for match in self.DATE_NUMERIC_PATTERN.finditer(text):
            adicionar(*match.groups())

        for match in self.DATE_FIELDS_PATTERN.finditer(text):
            adicionar(*match.groups())

        for match in self.DATE_WRITTEN_PATTERN.finditer(text):
            dia, nome_mes, ano = match.groups()
            mes = self._MESES.get(self._normalizar_texto(nome_mes))
            if mes:
                adicionar(dia, mes, ano)

        return encontradas

    def _extract_fields(self, text, image=None):

        cpf_result = find_cpf(text)
        resolvido_via_regiao = False

        # Se a leitura no texto de página inteira ficou ambígua ou não
        # encontrou nada, tentamos uma segunda passada: isolar só a região
        # do campo CPF na imagem e reprocessar com whitelist de dígitos.
        # Isso resolve erros de OCR na origem (confirmado com documentos
        # reais: um CPF que dava "ambíguo" no texto corrido saiu correto
        # isolando a região), em vez de depender só de correção estatística
        # sobre um texto que já saiu degradado.
        #
        # Não fazemos essa segunda tentativa quando o status já é "invalid":
        # nesse caso o texto de página inteira já leu 11 dígitos bem
        # formatados, então não é uma ambiguidade de OCR — é um CPF
        # provavelmente inconsistente no próprio documento. Substituir esse
        # resultado por uma segunda leitura poderia mascarar um indício
        # real de adulteração.
        if image is not None and cpf_result.status in ("ambiguous", "not_found"):

            try:
                cpf_result_regiao = extract_cpf_from_region(image)
            except Exception:
                cpf_result_regiao = None

            if cpf_result_regiao is not None and cpf_result_regiao.status in ("valid", "corrected"):
                cpf_result = cpf_result_regiao
                resolvido_via_regiao = True

        date_matches = self._extract_dates(text)
        name_match = self.NAME_PATTERN.search(text)

        if name_match:
            nome_valor = name_match.group(1).strip()
            nome_fonte = "rotulo"
        else:
            nome_valor = self._extract_name_heuristic(text)
            nome_fonte = "heuristica" if nome_valor else None

        # "cpf" continua sendo o campo simples (string de dígitos ou None),
        # para não quebrar quem já consome fields["cpf"] (ex: DocumentComparator).
        # Em caso de status "ambiguous", deixamos None de propósito: não dá
        # pra afirmar qual dos candidatos é o correto sem revisão humana.
        if cpf_result.status in ("valid", "corrected", "invalid"):
            cpf_valor = cpf_result.value or (
                cpf_result.candidates[0] if cpf_result.candidates else None
            )
        else:
            cpf_valor = None

        return {

            "nome": nome_valor,
            "nome_fonte": nome_fonte,
            "cpf": cpf_valor,
            "cpf_status": cpf_result.status,
            "cpf_candidates": cpf_result.candidates,
            "cpf_raw_ocr": cpf_result.raw_ocr_text,
            "cpf_resolved_via_region": resolvido_via_regiao,
            "datas": date_matches

        }


    # ---------- EVIDÊNCIAS ----------

    def _build_evidences(self, text, fields, avg_confidence):

        evidences = []


        if not text.strip():

            evidences.append(

                Evidence(
                    code="OCR_NO_TEXT",
                    message="Não foi possível extrair texto do documento.",
                    severity="high",
                    weight=25
                )

            )

            # se não há texto nenhum, não faz sentido checar os campos
            return evidences


        if avg_confidence and avg_confidence < self.MIN_CONFIDENCE:

            evidences.append(

                Evidence(
                    code="OCR_LOW_CONFIDENCE",
                    message=f"Confiança média do OCR baixa ({avg_confidence}%), "
                            f"o texto extraído pode estar incorreto.",
                    severity="medium",
                    weight=10
                )

            )


        if not fields["nome"]:

            evidences.append(

                Evidence(
                    code="OCR_NAME_NOT_FOUND",
                    message="Não foi possível identificar um nome no documento.",
                    severity="low",
                    weight=5
                )

            )

        elif fields.get("nome_fonte") == "heuristica":

            # O nome não veio de um rótulo explícito ("Nome:") — foi
            # inferido por heurística (linha que "parece nome"). Mais
            # sujeito a falso positivo/negativo que a extração por rótulo,
            # então vale sinalizar para quem for revisar o resultado.
            evidences.append(

                Evidence(
                    code="OCR_NAME_HEURISTIC",
                    message=f"Nome identificado por heurística, sem rótulo "
                            f"'Nome:' explícito no documento ({fields['nome']!r}). "
                            f"Recomenda-se revisão manual.",
                    severity="low",
                    weight=5
                )

            )


        cpf_status = fields.get("cpf_status")

        if fields.get("cpf_resolved_via_region") and cpf_status in ("valid", "corrected"):

            evidences.append(

                Evidence(
                    code="OCR_CPF_RESOLVED_VIA_REGION",
                    message="A leitura do CPF no texto de página inteira ficou "
                            "ambígua ou não foi encontrada; resolvida isolando "
                            "a região do campo e reprocessando com maior precisão.",
                    severity="low",
                    weight=0
                )

            )

        if cpf_status == "not_found":

            evidences.append(

                Evidence(
                    code="OCR_CPF_NOT_FOUND",
                    message="Não foi possível identificar um CPF no documento.",
                    severity="low",
                    weight=5
                )

            )

        elif cpf_status == "corrected":

            # O OCR provavelmente errou a leitura (10 ou 12 dígitos), mas
            # havia só UM candidato que resultava em CPF matematicamente
            # válido, então a correção automática é razoavelmente segura.
            # Ainda assim registramos como evidência informativa, para
            # rastreabilidade no relatório final.
            evidences.append(

                Evidence(
                    code="OCR_CPF_CORRECTED",
                    message=f"CPF corrigido automaticamente a partir de leitura "
                            f"de OCR inconsistente (texto bruto: "
                            f"{fields.get('cpf_raw_ocr')!r}).",
                    severity="low",
                    weight=5
                )

            )

        elif cpf_status == "ambiguous":

            # Mais de um candidato de CPF resultou em checksum válido:
            # não dá pra confirmar automaticamente qual é o correto.
            evidences.append(

                Evidence(
                    code="OCR_CPF_AMBIGUOUS",
                    message=f"Leitura do CPF ambígua, requer revisão manual. "
                            f"Candidatos válidos: {fields.get('cpf_candidates')}.",
                    severity="medium",
                    weight=15
                )

            )

        elif cpf_status == "invalid":

            # 11 dígitos, formatação correta, mas o dígito verificador
            # NÃO bate. Diferente dos casos acima, aqui não é um provável
            # erro de OCR (o formato já veio "redondo") — é um indício de
            # que o dado no próprio documento é inconsistente, o que pode
            # apontar para adulteração.
            evidences.append(

                Evidence(
                    code="CPF_CHECKSUM_INVALID",
                    message=f"CPF com formatação válida, mas dígito verificador "
                            f"incorreto ({fields.get('cpf')}). Pode indicar "
                            f"documento adulterado ou erro de preenchimento.",
                    severity="high",
                    weight=25
                )

            )


        if not fields["datas"]:

            evidences.append(

                Evidence(
                    code="OCR_DATE_NOT_FOUND",
                    message="Não foi possível identificar nenhuma data no documento.",
                    severity="low",
                    weight=5
                )

            )


        return evidences

