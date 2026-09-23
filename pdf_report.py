from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
    KeepTogether,
    HRFlowable
)
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

import os
import re
from datetime import datetime


# identidade visual das cores utilizadas no relatório

VERDE = colors.HexColor("#00A279")
VERDE_ESCURO = colors.HexColor("#007A5A")
VERDE_PROFUNDO = colors.HexColor("#005C46")

VERDE_CLARO = colors.HexColor("#EAF7F3")
VERDE_MUITO_CLARO = colors.HexColor("#F5FBF9")

BRANCO = colors.white

PRETO = colors.HexColor("#17211D")
CINZA_ESCURO = colors.HexColor("#3F4A46")
CINZA = colors.HexColor("#69736F")
CINZA_MEDIO = colors.HexColor("#AAB3AF")
CINZA_CLARO = colors.HexColor("#DDE5E1")
CINZA_MUITO_CLARO = colors.HexColor("#F1F5F3")

VERMELHO = colors.HexColor("#D9534F")
VERMELHO_CLARO = colors.HexColor("#FCEDEC")

AMARELO = colors.HexColor("#C68A18")
AMARELO_CLARO = colors.HexColor("#FFF7E5")


# tamanho da página e margens

LARGURA_PAGINA, ALTURA_PAGINA = A4

MARGEM_ESQUERDA = 18 * mm
MARGEM_DIREITA = 18 * mm
MARGEM_SUPERIOR = 29 * mm
MARGEM_INFERIOR = 23 * mm

LARGURA_UTIL = (
    LARGURA_PAGINA
    - MARGEM_ESQUERDA
    - MARGEM_DIREITA
)

# fontes

def configurar_fontes():

    fontes_possiveis = [

        (
            "Poppins",
            "C:/Windows/Fonts/Poppins-Regular.ttf",
            "C:/Windows/Fonts/Poppins-Bold.ttf"
        ),

        (
            "Arial",
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/arialbd.ttf"
        )
    ]

    for nome, normal, bold in fontes_possiveis:

        if os.path.exists(normal) and os.path.exists(bold):

            try:

                pdfmetrics.registerFont(
                    TTFont(nome, normal)
                )

                pdfmetrics.registerFont(
                    TTFont(f"{nome}-Bold", bold)
                )

                return nome

            except Exception:
                continue

    return "Helvetica"


FONTE = configurar_fontes()


# estilos

def criar_estilos():

    return {

        # titulo

        "titulo": ParagraphStyle(
            "Titulo",
            fontName=f"{FONTE}-Bold",
            fontSize=24,
            leading=29,
            textColor=PRETO,
            alignment=TA_LEFT,
            spaceAfter=7
        ),

        # sub

        "subtitulo": ParagraphStyle(
            "Subtitulo",
            fontName=FONTE,
            fontSize=10,
            leading=16,
            textColor=CINZA,
            alignment=TA_LEFT
        ),

        # titulo secao

        "secao": ParagraphStyle(
            "Secao",
            fontName=f"{FONTE}-Bold",
            fontSize=17,
            leading=22,
            textColor=PRETO,
            spaceAfter=5
        ),

        "eyebrow": ParagraphStyle(
            "Eyebrow",
            fontName=f"{FONTE}-Bold",
            fontSize=7.5,
            leading=10,
            textColor=VERDE,
            spaceAfter=4,
            tracking=1
        ),

        # texto

        "texto": ParagraphStyle(
            "Texto",
            fontName=FONTE,
            fontSize=9,
            leading=14,
            textColor=PRETO,
            spaceAfter=5
        ),

        "pequeno": ParagraphStyle(
            "Pequeno",
            fontName=FONTE,
            fontSize=7.5,
            leading=11,
            textColor=CINZA
        ),

        "centralizado": ParagraphStyle(
            "Centralizado",
            fontName=FONTE,
            fontSize=9,
            leading=13,
            textColor=CINZA,
            alignment=TA_CENTER
        ),

        # score

        "score": ParagraphStyle(
            "Score",
            fontName=f"{FONTE}-Bold",
            fontSize=38,
            leading=42,
            textColor=VERDE_ESCURO,
            alignment=TA_CENTER
        ),

        # classificacao

        "classificacao": ParagraphStyle(
            "Classificacao",
            fontName=f"{FONTE}-Bold",
            fontSize=11,
            leading=15,
            textColor=VERDE_ESCURO,
            alignment=TA_CENTER
        ),

        # capa

        "capa_mini": ParagraphStyle(
            "CapaMini",
            fontName=f"{FONTE}-Bold",
            fontSize=8,
            leading=11,
            textColor=VERDE,
            tracking=1.2
        ),

        "capa": ParagraphStyle(
            "Capa",
            fontName=f"{FONTE}-Bold",
            fontSize=29,
            leading=34,
            textColor=PRETO,
            alignment=TA_LEFT
        ),

        "capa_sub": ParagraphStyle(
            "CapaSub",
            fontName=FONTE,
            fontSize=11,
            leading=17,
            textColor=CINZA,
            alignment=TA_LEFT
        ),

        # -------------------------------------------------
        # NÚMEROS DOS CARDS
        # -------------------------------------------------

        "numero_card": ParagraphStyle(
            "NumeroCard",
            fontName=f"{FONTE}-Bold",
            fontSize=8,
            leading=10,
            textColor=VERDE,
            alignment=TA_LEFT
        ),

        # -------------------------------------------------
        # TÍTULO CARD
        # -------------------------------------------------

        "card_titulo": ParagraphStyle(
            "CardTitulo",
            fontName=f"{FONTE}-Bold",
            fontSize=10,
            leading=14,
            textColor=PRETO,
            alignment=TA_LEFT
        ),

        # -------------------------------------------------
        # VALOR CARD
        # -------------------------------------------------

        "card_valor": ParagraphStyle(
            "CardValor",
            fontName=f"{FONTE}-Bold",
            fontSize=17,
            leading=21,
            textColor=VERDE_ESCURO,
            alignment=TA_LEFT
        ),

        # -------------------------------------------------
        # VALOR GRANDE
        # -------------------------------------------------

        "valor_grande": ParagraphStyle(
            "ValorGrande",
            fontName=f"{FONTE}-Bold",
            fontSize=23,
            leading=27,
            textColor=VERDE_ESCURO,
            alignment=TA_LEFT
        ),

        # -------------------------------------------------
        # LABEL
        # -------------------------------------------------

        "label": ParagraphStyle(
            "Label",
            fontName=f"{FONTE}-Bold",
            fontSize=7,
            leading=9,
            textColor=CINZA,
            alignment=TA_LEFT
        ),

        # -------------------------------------------------
        # CONCLUSÃO
        # -------------------------------------------------

        "conclusao": ParagraphStyle(
            "Conclusao",
            fontName=FONTE,
            fontSize=9.5,
            leading=16,
            textColor=PRETO,
            alignment=TA_LEFT
        )
    }


# =========================================================
# CABEÇALHO E RODAPÉ
# =========================================================

def desenhar_pagina(canvas, doc):

    canvas.saveState()

    largura, altura = A4

    # =====================================================
    # FUNDO
    # =====================================================

    canvas.setFillColor(BRANCO)

    canvas.rect(
        0,
        0,
        largura,
        altura,
        stroke=0,
        fill=1
    )

    # =====================================================
    # MOLDURA EXTERNA (BORDA VERDE MAIOR)
    # =====================================================

    canvas.setStrokeColor(VERDE)
    canvas.setLineWidth(3.0)

    canvas.roundRect(
        8 * mm,
        8 * mm,
        largura - 16 * mm,
        altura - 16 * mm,
        3 * mm,
        stroke=1,
        fill=0
    )

    # =====================================================
    # DETALHE VERDE SUPERIOR
    # =====================================================

    canvas.setFillColor(VERDE)

    canvas.roundRect(
        18 * mm,
        altura - 17 * mm,
        12 * mm,
        2 * mm,
        1 * mm,
        stroke=0,
        fill=1
    )

    # =====================================================
    # LOGO VALID
    # =====================================================

    canvas.setFont(
        f"{FONTE}-Bold",
        11
    )

    canvas.setFillColor(
        VERDE_ESCURO
    )

    canvas.drawString(
        18 * mm,
        altura - 19 * mm,
        "VALID"
    )

    # =====================================================
    # TÍTULO DO DOCUMENTO
    # =====================================================

    canvas.setFont(
        FONTE,
        7
    )

    canvas.setFillColor(
        CINZA
    )

    canvas.drawRightString(
        largura - 18 * mm,
        altura - 19 * mm,
        "RELATÓRIO DE ANÁLISE DOCUMENTAL"
    )

    # =====================================================
    # LINHA DO CABEÇALHO
    # =====================================================

    canvas.setStrokeColor(
        CINZA_CLARO
    )

    canvas.setLineWidth(
        0.5
    )

    canvas.line(
        18 * mm,
        altura - 24 * mm,
        largura - 18 * mm,
        altura - 24 * mm
    )

    # =====================================================
    # RODAPÉ
    # =====================================================

    canvas.line(
        18 * mm,
        17 * mm,
        largura - 18 * mm,
        17 * mm
    )

    canvas.setFont(
        FONTE,
        6.8
    )

    canvas.setFillColor(
        CINZA
    )

    canvas.drawString(
        18 * mm,
        12 * mm,
        "VALID • Sistema de Análise de Autenticidade Documental"
    )

    canvas.drawRightString(
        largura - 18 * mm,
        12 * mm,
        f"{doc.page:02d}"
    )

    canvas.restoreState()


# =========================================================
# LINHA DECORATIVA
# =========================================================

def linha_verde():

    return HRFlowable(
        width="100%",
        thickness=1.2,
        color=VERDE,
        spaceBefore=3,
        spaceAfter=9
    )


# =========================================================
# CARD MODERNO
# =========================================================

def criar_card(
    conteudo,
    largura,
    fundo=BRANCO,
    borda=CINZA_CLARO,
    padding=10
):

    tabela = Table(
        [[conteudo]],
        colWidths=[largura]
    )

    tabela.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                fundo
            ),

            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.7,
                borda
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                padding
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                padding
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                padding
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                padding
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            )

        ])
    )

    return tabela


# =========================================================
# CARD DE MÉTRICA
# =========================================================

def criar_card_metrica(
    numero,
    titulo,
    valor,
    descricao,
    largura
):

    conteudo = [

        Paragraph(
            numero,
            ParagraphStyle(
                "NumeroTemporario",
                fontName=f"{FONTE}-Bold",
                fontSize=7,
                textColor=VERDE
            )
        ),

        Spacer(
            1,
            4
        ),

        Paragraph(
            titulo.upper(),
            ParagraphStyle(
                "TituloTemporario",
                fontName=f"{FONTE}-Bold",
                fontSize=7.5,
                leading=10,
                textColor=CINZA
            )
        ),

        Spacer(
            1,
            3
        ),

        Paragraph(
            valor,
            ParagraphStyle(
                "ValorTemporario",
                fontName=f"{FONTE}-Bold",
                fontSize=18,
                leading=22,
                textColor=VERDE_ESCURO
            )
        ),

        Spacer(
            1,
            3
        ),

        Paragraph(
            descricao,
            ParagraphStyle(
                "DescricaoTemporaria",
                fontName=FONTE,
                fontSize=7.2,
                leading=10,
                textColor=CINZA
            )
        )
    ]

    return criar_card(
        conteudo,
        largura,
        fundo=VERDE_MUITO_CLARO,
        borda=VERDE_CLARO,
        padding=9
    )


# =========================================================
# IMAGEM PROPORCIONAL
# =========================================================

def adicionar_imagem(
    caminho,
    largura_max,
    altura_max
):

    if not os.path.exists(caminho):
        return None

    try:

        from PIL import Image as PILImage

        imagem_original = PILImage.open(caminho)

        largura_original, altura_original = (
            imagem_original.size
        )

        if largura_original <= 0 or altura_original <= 0:
            return None

        proporcao = min(
            largura_max / largura_original,
            altura_max / altura_original
        )

        largura = largura_original * proporcao
        altura = altura_original * proporcao

        imagem = Image(
            caminho,
            width=largura,
            height=altura
        )

        return imagem

    except Exception as erro:

        print(
            f"Erro ao carregar imagem {caminho}: {erro}"
        )

        return None


# =========================================================
# CLASSIFICAÇÃO VISUAL
# =========================================================

def cores_classificacao(classificacao):

    texto = str(
        classificacao
    ).lower()

    if "alta" in texto:

        return (
            VERMELHO,
            VERMELHO_CLARO
        )

    if "média" in texto or "media" in texto:

        return (
            AMARELO,
            AMARELO_CLARO
        )

    return (
        VERDE_ESCURO,
        VERDE_CLARO
    )


# =========================================================
# LIMPA NOME PARA EXIBIÇÃO
# =========================================================

def limpar_nome_arquivo(nome):

    if not nome:
        return "Documento analisado"

    nome = str(nome)

    return nome.replace(
        "<",
        ""
    ).replace(
        ">",
        ""
    )


# =========================================================
# GERAÇÃO DO PDF
# =========================================================

def gerar_relatorio_pdf(
    resultado,
    nome_arquivo,
    caminho_pdf
):

    estilos = criar_estilos()

    # =====================================================
    # DOCUMENTO
    # =====================================================

    doc = SimpleDocTemplate(

        caminho_pdf,

        pagesize=A4,

        rightMargin=MARGEM_DIREITA,
        leftMargin=MARGEM_ESQUERDA,

        topMargin=MARGEM_SUPERIOR,
        bottomMargin=MARGEM_INFERIOR,

        title="VALID - Relatório de Análise Documental",
        author="VALID",
        subject="Análise automatizada de autenticidade documental"
    )

    elementos = []

    # =====================================================
    # DADOS DA ANÁLISE
    # =====================================================

    global_data = resultado.get(
        "analise_global",
        {}
    )

    score = float(
        global_data.get(
            "combined_score",
            0
        ) or 0
    )

    classificacao = global_data.get(
        "classification",
        "Não informado"
    )

    pixel_score = float(
        global_data.get(
            "pixel_score",
            0
        ) or 0
    )

    geometry_score = float(
        global_data.get(
            "geometry_score",
            0
        ) or 0
    )

    continuity_score = float(
        global_data.get(
            "continuity_score",
            0
        ) or 0
    )

    max_block_score = float(
        global_data.get(
            "max_block_score",
            0
        ) or 0
    )

    total_regioes = resultado.get(
        "total_regioes_texto",
        global_data.get(
            "total_regions",
            0
        )
    )

    regioes_suspeitas = global_data.get(
        "suspicious_geometry_regions",
        len(
            resultado.get(
                "lista_anomalias",
                []
            )
        )
    )

    lista_anomalias = resultado.get(
        "lista_anomalias",
        []
    )

    agora = datetime.now()

    nome_arquivo = limpar_nome_arquivo(
        nome_arquivo
    )

    # =====================================================
    # CORES DA CLASSIFICAÇÃO
    # =====================================================

    cor_classificacao, fundo_classificacao = (
        cores_classificacao(
            classificacao
        )
    )

    # =====================================================
    # CAPA
    # =====================================================

    elementos.append(
        Spacer(
            1,
            18 * mm
        )
    )

    # -----------------------------------------------------
    # MARCA
    # -----------------------------------------------------

    elementos.append(
        Paragraph(
            "VALID",
            ParagraphStyle(
                "LogoCapa",
                fontName=f"{FONTE}-Bold",
                fontSize=24,
                leading=28,
                textColor=VERDE,
                spaceAfter=4
            )
        )
    )

    elementos.append(
        Paragraph(
            "SISTEMA DE ANÁLISE DOCUMENTAL",
            estilos["capa_mini"]
        )
    )

    elementos.append(
        Spacer(
            1,
            18 * mm
        )
    )

    # -----------------------------------------------------
    # TÍTULO
    # -----------------------------------------------------

    elementos.append(
        Paragraph(
            "RELATÓRIO<br/>DE ANÁLISE",
            estilos["capa"]
        )
    )

    elementos.append(
        Paragraph(
            "DE AUTENTICIDADE<br/>DOCUMENTAL",
            ParagraphStyle(
                "CapaVerde",
                parent=estilos["capa"],
                textColor=VERDE_ESCURO,
                spaceAfter=8
            )
        )
    )

    elementos.append(
        Spacer(
            1,
            6 * mm
        )
    )

    elementos.append(
        Paragraph(
            "Relatório técnico produzido a partir da análise "
            "automatizada de características visuais, "
            "pixel-a-pixel e geométricas do documento.",
            estilos["capa_sub"]
        )
    )

    elementos.append(
        Spacer(
            1,
            15 * mm
        )
    )

    # -----------------------------------------------------
    # SCORE PRINCIPAL
    # -----------------------------------------------------

    score_conteudo = [

        Paragraph(
            "RESULTADO DA ANÁLISE",
            ParagraphStyle(
                "ScoreMini",
                fontName=f"{FONTE}-Bold",
                fontSize=7.5,
                leading=10,
                textColor=VERDE,
                alignment=TA_CENTER
            )
        ),

        Spacer(
            1,
            5
        ),

        Paragraph(
            f"{score:.1f}%",
            estilos["score"]
        ),

        Paragraph(
            "SCORE FINAL",
            estilos["centralizado"]
        ),

        Spacer(
            1,
            7
        ),

        Table(
            [[
                Paragraph(
                    str(classificacao),
                    ParagraphStyle(
                        "ClassificacaoCapa",
                        fontName=f"{FONTE}-Bold",
                        fontSize=9,
                        leading=12,
                        textColor=cor_classificacao,
                        alignment=TA_CENTER
                    )
                )
            ]],
            colWidths=[75 * mm],
            style=TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    fundo_classificacao
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    fundo_classificacao
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                )
            ])
        )
    ]

    score_card = criar_card(
        score_conteudo,
        105 * mm,
        fundo=BRANCO,
        borda=VERDE_CLARO,
        padding=12
    )

    score_wrapper = Table(
        [[score_card]],
        colWidths=[LARGURA_UTIL]
    )

    score_wrapper.setStyle(
        TableStyle([
            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER"
            )
        ])
    )

    elementos.append(
        score_wrapper
    )

    elementos.append(
        Spacer(
            1,
            12 * mm
        )
    )

    # -----------------------------------------------------
    # IDENTIFICAÇÃO DO DOCUMENTO
    # -----------------------------------------------------

    identificacao = [

        [
            Paragraph(
                "DOCUMENTO",
                estilos["label"]
            ),

            Paragraph(
                nome_arquivo,
                estilos["texto"]
            )
        ],

        [
            Paragraph(
                "DATA DA ANÁLISE",
                estilos["label"]
            ),

            Paragraph(
                agora.strftime(
                    "%d/%m/%Y • %H:%M"
                ),
                estilos["texto"]
            )
        ],

        [
            Paragraph(
                "REGIÕES TEXTUAIS",
                estilos["label"]
            ),

            Paragraph(
                str(total_regioes),
                estilos["texto"]
            )
        ]

    ]

    tabela_identificacao = Table(
        identificacao,
        colWidths=[
            43 * mm,
            115 * mm
        ]
    )

    tabela_identificacao.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                VERDE_MUITO_CLARO
            ),

            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.6,
                CINZA_CLARO
            ),

            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.3,
                CINZA_CLARO
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                8
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                8
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                6
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                6
            )

        ])
    )

    elementos.append(
        tabela_identificacao
    )

    elementos.append(
        PageBreak()
    )

    # =====================================================
    # 01 — RESULTADO DA ANÁLISE
    # =====================================================

    elementos.append(
        Paragraph(
            "01",
            estilos["eyebrow"]
        )
    )

    elementos.append(
        Paragraph(
            "Resultado da análise",
            estilos["secao"]
        )
    )

    elementos.append(
        linha_verde()
    )

    elementos.append(
        Paragraph(
            "O sistema realizou uma análise automatizada "
            "combinando indicadores relacionados à estrutura "
            "dos pixels, continuidade visual e características "
            "geométricas das regiões textuais identificadas.",
            estilos["texto"]
        )
    )

    elementos.append(
        Spacer(
            1,
            5 * mm
        )
    )

    # -----------------------------------------------------
    # CARDS PRINCIPAIS
    # -----------------------------------------------------

    largura_card = (
        (LARGURA_UTIL - 8 * mm) / 3
    )

    cards_resultado = Table(
        [[

            criar_card_metrica(
                "01",
                "Score final",
                f"{score:.1f}%",
                "Resultado consolidado da análise.",
                largura_card
            ),

            criar_card_metrica(
                "02",
                "Análise de pixels",
                f"{pixel_score:.1f}",
                "Indicadores relacionados aos pixels.",
                largura_card
            ),

            criar_card_metrica(
                "03",
                "Análise EOCR",
                f"{geometry_score:.1f}",
                "Indicadores geométricos textuais.",
                largura_card
            )

        ]],
        colWidths=[
            largura_card,
            largura_card,
            largura_card
        ]
    )

    cards_resultado.setStyle(
        TableStyle([
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                0
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                4
            )
        ])
    )

    elementos.append(
        cards_resultado
    )

    elementos.append(
        Spacer(
            1,
            7 * mm
        )
    )

    # -----------------------------------------------------
    # MÉTRICAS COMPLEMENTARES
    # -----------------------------------------------------

    metricas_secundarias = [

        [
            Paragraph(
                "CONTINUIDADE",
                estilos["label"]
            ),
            Paragraph(
                f"{continuity_score:.2f}",
                estilos["card_valor"]
            ),
            Paragraph(
                "MAIOR BLOCO",
                estilos["label"]
            ),
            Paragraph(
                f"{max_block_score:.2f}",
                estilos["card_valor"]
            )
        ],

        [
            Paragraph(
                "REGIÕES TEXTUAIS",
                estilos["label"]
            ),
            Paragraph(
                str(total_regioes),
                estilos["card_valor"]
            ),
            Paragraph(
                "REGIÕES SINALIZADAS",
                estilos["label"]
            ),
            Paragraph(
                str(regioes_suspeitas),
                estilos["card_valor"]
            )
        ]

    ]

    tabela_secundaria = Table(
        metricas_secundarias,
        colWidths=[
            37 * mm,
            42 * mm,
            43 * mm,
            36 * mm
        ]
    )

    tabela_secundaria.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                BRANCO
            ),

            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.6,
                CINZA_CLARO
            ),

            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.3,
                CINZA_CLARO
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                8
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                8
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                7
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                7
            )

        ])
    )

    elementos.append(
        tabela_secundaria
    )

    elementos.append(
        Spacer(
            1,
            10 * mm
        )
    )

    # -----------------------------------------------------
    # CLASSIFICAÇÃO
    # -----------------------------------------------------

    classificacao_card = criar_card(
        [
            Paragraph(
                "CLASSIFICAÇÃO OBTIDA",
                estilos["label"]
            ),

            Spacer(
                1,
                4
            ),

            Paragraph(
                str(classificacao),
                ParagraphStyle(
                    "ClassificacaoResultado",
                    fontName=f"{FONTE}-Bold",
                    fontSize=17,
                    leading=21,
                    textColor=cor_classificacao
                )
            ),

            Spacer(
                1,
                3
            ),

            Paragraph(
                "A classificação representa o resultado "
                "dos critérios computacionais aplicados "
                "durante a análise.",
                estilos["pequeno"]
            )
        ],
        LARGURA_UTIL,
        fundo=fundo_classificacao,
        borda=fundo_classificacao,
        padding=11
    )

    elementos.append(
        classificacao_card
    )

    elementos.append(
        PageBreak()
    )

    # =====================================================
    # 02 — METODOLOGIA
    # =====================================================

    elementos.append(
        Paragraph(
            "02",
            estilos["eyebrow"]
        )
    )

    elementos.append(
        Paragraph(
            "Metodologia",
            estilos["secao"]
        )
    )

    elementos.append(
        linha_verde()
    )

    elementos.append(
        Paragraph(
            "A análise combina diferentes etapas computacionais "
            "para observar características visuais e estruturais "
            "do documento.",
            estilos["texto"]
        )
    )

    elementos.append(
        Spacer(
            1,
            6 * mm
        )
    )

    metodologia = [

        (
            "01",
            "ANÁLISE DE PIXELS",
            "Avalia características e variações na estrutura "
            "visual dos pixels do documento."
        ),

        (
            "02",
            "CONTINUIDADE",
            "Observa variações locais e padrões de continuidade "
            "na imagem analisada."
        ),

        (
            "03",
            "ANÁLISE DE BLOCOS",
            "Examina regiões localizadas em busca de "
            "comportamentos visuais que possam se diferenciar "
            "do restante do documento."
        ),

        (
            "04",
            "ANÁLISE GEOMÉTRICA / EOCR",
            "Avalia características geométricas e estruturais "
            "das regiões textuais identificadas."
        )

    ]

    largura_metodologia = (
        (LARGURA_UTIL - 5 * mm) / 2
    )

    for indice in range(0, len(metodologia), 2):

        linha_cards = []

        for item in metodologia[indice:indice + 2]:

            numero, titulo, descricao = item

            card = criar_card(
                [
                    Paragraph(
                        numero,
                        estilos["numero_card"]
                    ),

                    Spacer(
                        1,
                        5
                    ),

                    Paragraph(
                        titulo,
                        estilos["card_titulo"]
                    ),

                    Spacer(
                        1,
                        5
                    ),

                    Paragraph(
                        descricao,
                        estilos["pequeno"]
                    )
                ],
                largura_metodologia,
                fundo=BRANCO,
                borda=CINZA_CLARO,
                padding=11
            )

            linha_cards.append(
                card
            )

        tabela_cards = Table(
            [linha_cards],
            colWidths=[
                largura_metodologia,
                largura_metodologia
            ]
        )

        tabela_cards.setStyle(
            TableStyle([

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    0
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    4
                )

            ])
        )

        elementos.append(
            tabela_cards
        )

        elementos.append(
            Spacer(
                1,
                5 * mm
            )
        )

    # -----------------------------------------------------
    # COMPOSIÇÃO
    # -----------------------------------------------------

    elementos.append(
        Spacer(
            1,
            5 * mm
        )
    )

    composicao = criar_card(
        [
            Paragraph(
                "COMPOSIÇÃO DO RESULTADO",
                estilos["label"]
            ),

            Spacer(
                1,
                5
            ),

            Paragraph(
                "30%",
                estilos["valor_grande"]
            ),

            Paragraph(
                "ANÁLISE DE PIXELS",
                estilos["label"]
            ),

            Spacer(
                1,
                4
            ),

            Paragraph(
                "70%",
                estilos["valor_grande"]
            ),

            Paragraph(
                "ANÁLISE GEOMÉTRICA / EOCR",
                estilos["label"]
            ),

            Spacer(
                1,
                5
            ),

            Paragraph(
                "A composição acima corresponde à configuração "
                "atualmente utilizada pelo sistema VALID.",
                estilos["pequeno"]
            )
        ],
        LARGURA_UTIL,
        fundo=VERDE_MUITO_CLARO,
        borda=VERDE_CLARO,
        padding=12
    )

    elementos.append(
        composicao
    )

    elementos.append(
        Spacer(
            1,
            7 * mm
        )
    )

    elementos.append(
        Paragraph(
            "Observação: os indicadores apresentados são "
            "resultados computacionais e devem ser interpretados "
            "em conjunto com as evidências visuais e o contexto "
            "documental disponível.",
            estilos["pequeno"]
        )
    )

    elementos.append(
        PageBreak()
    )

    # =====================================================
    # 03 — EVIDÊNCIAS VISUAIS
    # =====================================================

    imagens = [

        (
            "01",
            "ANÁLISE HÍBRIDA EOCR",
            "Visualização das regiões textuais analisadas "
            "e dos resultados combinados.",
            "results/hybrid_analysis.png"
        ),

        (
            "02",
            "MAPA DE ELA",
            "Visualização das variações identificadas "
            "pela análise de erro de nível de pixel.",
            "results/xray_heatmap.png"
        ),

        (
            "03",
            "MAPA DE CONTINUIDADE",
            "Visualização das variações de continuidade "
            "encontradas no documento.",
            "results/continuity_map.png"
        ),

        (
            "04",
            "MAPA DE CONTINUIDADE / PIXEL CORE",
            "Visualização complementar dos indicadores "
            "relacionados à continuidade dos pixels.",
            "results/continuity_heatmap.png"
        )

    ]

    imagens_existentes = [
        item
        for item in imagens
        if os.path.exists(item[3])
    ]

    for posicao, (
        numero,
        titulo,
        descricao,
        caminho
    ) in enumerate(imagens_existentes):

        elementos.append(
            Paragraph(
                "03",
                estilos["eyebrow"]
            )
        )

        elementos.append(
            Paragraph(
                "Evidências visuais",
                estilos["secao"]
            )
        )

        elementos.append(
            linha_verde()
        )

        # -------------------------------------------------
        # CABEÇALHO DA EVIDÊNCIA
        # -------------------------------------------------

        cabecalho_imagem = Table(
            [[

                Paragraph(
                    numero,
                    ParagraphStyle(
                        "NumeroImagem",
                        fontName=f"{FONTE}-Bold",
                        fontSize=8,
                        textColor=VERDE
                    )
                ),

                Paragraph(
                    titulo,
                    ParagraphStyle(
                        "TituloImagem",
                        fontName=f"{FONTE}-Bold",
                        fontSize=12,
                        leading=15,
                        textColor=PRETO
                    )
                )

            ]],
            colWidths=[
                13 * mm,
                LARGURA_UTIL - 13 * mm
            ]
        )

        cabecalho_imagem.setStyle(
            TableStyle([

                (
                    "BACKGROUND",
                    (0, 0),
                    (0, 0),
                    VERDE_CLARO
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    7
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    7
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7
                ),

                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    CINZA_CLARO
                )

            ])
        )

        elementos.append(
            cabecalho_imagem
        )

        elementos.append(
            Spacer(
                1,
                4 * mm
            )
        )

        elementos.append(
            Paragraph(
                descricao,
                estilos["pequeno"]
            )
        )

        elementos.append(
            Spacer(
                1,
                6 * mm
            )
        )

        # -------------------------------------------------
        # IMAGEM
        # -------------------------------------------------

        imagem = adicionar_imagem(
            caminho,
            168 * mm,
            195 * mm
        )

        if imagem:

            area_imagem = Table(
                [[imagem]],
                colWidths=[
                    LARGURA_UTIL
                ]
            )

            area_imagem.setStyle(
                TableStyle([

                    (
                        "ALIGN",
                        (0, 0),
                        (-1, -1),
                        "CENTER"
                    ),

                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE"
                    ),

                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.6,
                        CINZA_CLARO
                    ),

                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        CINZA_MUITO_CLARO
                    ),

                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        8
                    ),

                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        8
                    )

                ])
            )

            elementos.append(
                area_imagem
            )

        elementos.append(
            Spacer(
                1,
                5 * mm
            )
        )

        elementos.append(
            Paragraph(
                f"Evidência visual {numero} • VALID",
                estilos["pequeno"]
            )
        )

        # -------------------------------------------------
        # SÓ QUEBRA SE NÃO FOR A ÚLTIMA
        # -------------------------------------------------

        if posicao < len(imagens_existentes) - 1:

            elementos.append(
                PageBreak()
            )

    # =====================================================
    # 04 — REGIÕES DE ATENÇÃO
    # =====================================================

    elementos.append(
        PageBreak()
    )

    elementos.append(
        Paragraph(
            "04",
            estilos["eyebrow"]
        )
    )

    elementos.append(
        Paragraph(
            "Regiões de atenção",
            estilos["secao"]
        )
    )

    elementos.append(
        linha_verde()
    )

    elementos.append(
        Paragraph(
            "As regiões abaixo correspondem aos trechos "
            "sinalizados pelos critérios utilizados na "
            "análise automatizada.",
            estilos["texto"]
        )
    )

    elementos.append(
        Spacer(
            1,
            5 * mm
        )
    )

    if lista_anomalias:

        for indice, anomalia in enumerate(
            lista_anomalias,
            start=1
        ):

            nivel = anomalia.get(
                "nivel_classificacao",
                "Não informado"
            )

            pontuacao = float(
                anomalia.get(
                    "pontuacao_suspeita",
                    0
                ) or 0
            )

            cor_nivel, fundo_nivel = (
                cores_classificacao(
                    nivel
                )
            )

            texto_identificado = (
                str(
                    anomalia.get(
                        "texto_identificado",
                        ""
                    )
                ).strip()
            )

            if not texto_identificado:

                texto_identificado = (
                    f"Região {indice}"
                )

            cabecalho_regiao = Table(
                [[

                    Paragraph(
                        f"{indice:02d}",
                        ParagraphStyle(
                            "NumeroRegiao",
                            fontName=f"{FONTE}-Bold",
                            fontSize=12,
                            textColor=VERDE
                        )
                    ),

                    Paragraph(
                        "REGIÃO DE ATENÇÃO",
                        ParagraphStyle(
                            "TituloRegiao",
                            fontName=f"{FONTE}-Bold",
                            fontSize=8,
                            textColor=CINZA
                        )
                    ),

                    Table(
                        [[
                            Paragraph(
                                str(nivel),
                                ParagraphStyle(
                                    "NivelRegiao",
                                    fontName=f"{FONTE}-Bold",
                                    fontSize=7.5,
                                    textColor=cor_nivel,
                                    alignment=TA_CENTER
                                )
                            )
                        ]],
                        colWidths=[32 * mm],
                        style=TableStyle([
                            (
                                "BACKGROUND",
                                (0, 0),
                                (-1, -1),
                                fundo_nivel
                            ),
                            (
                                "BOX",
                                (0, 0),
                                (-1, -1),
                                0.4,
                                fundo_nivel
                            ),
                            (
                                "TOPPADDING",
                                (0, 0),
                                (-1, -1),
                                4
                            ),
                            (
                                "BOTTOMPADDING",
                                (0, 0),
                                (-1, -1),
                                4
                            )
                        ])
                    )

                ]],
                colWidths=[
                    14 * mm,
                    102 * mm,
                    42 * mm
                ]
            )

            cabecalho_regiao.setStyle(
                TableStyle([

                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE"
                    ),

                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        VERDE_MUITO_CLARO
                    ),

                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.6,
                        CINZA_CLARO
                    ),

                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        7
                    ),

                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        7
                    ),

                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        7
                    ),

                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        7
                    )

                ])
            )

            elementos.append(
                cabecalho_regiao
            )

            # -------------------------------------------------
            # TEXTO
            # -------------------------------------------------

            elementos.append(
                criar_card(
                    [
                        Paragraph(
                            "TEXTO IDENTIFICADO",
                            estilos["label"]
                        ),

                        Spacer(
                            1,
                            4
                        ),

                        Paragraph(
                            f"“{texto_identificado}”",
                            ParagraphStyle(
                                "TextoIdentificado",
                                fontName=FONTE,
                                fontSize=10,
                                leading=15,
                                textColor=PRETO
                            )
                        ),

                        Spacer(
                            1,
                            7
                        ),

                        Paragraph(
                            "PONTUAÇÃO DA REGIÃO",
                            estilos["label"]
                        ),

                        Spacer(
                            1,
                            2
                        ),

                        Paragraph(
                            f"{pontuacao:.1f}",
                            estilos["valor_grande"]
                        )

                    ],
                    LARGURA_UTIL,
                    fundo=BRANCO,
                    borda=CINZA_CLARO,
                    padding=10
                )
            )

            elementos.append(
                Spacer(
                    1,
                    4 * mm
                )
            )

            # -------------------------------------------------
            # MÉTRICAS DA REGIÃO
            # -------------------------------------------------

            metricas_regiao = [

                [
                    Paragraph(
                        "ELA",
                        estilos["label"]
                    ),

                    Paragraph(
                        str(
                            anomalia.get(
                                "desvio_maximo_ela",
                                0
                            )
                        ),
                        estilos["card_valor"]
                    ),

                    Paragraph(
                        "PIXEL Z-SCORE",
                        estilos["label"]
                    ),

                    Paragraph(
                        str(
                            anomalia.get(
                                "pixel_zscore",
                                0
                            )
                        ),
                        estilos["card_valor"]
                    )
                ],

                [
                    Paragraph(
                        "EDGE CONTRAST",
                        estilos["label"]
                    ),

                    Paragraph(
                        str(
                            anomalia.get(
                                "edge_contrast",
                                0
                            )
                        ),
                        estilos["card_valor"]
                    ),

                    Paragraph(
                        "DESVIO ANGULAR",
                        estilos["label"]
                    ),

                    Paragraph(
                        str(
                            anomalia.get(
                                "angle_dev",
                                0
                            )
                        ),
                        estilos["card_valor"]
                    )
                ],

                [
                    Paragraph(
                        "DENSIDADE Z",
                        estilos["label"]
                    ),

                    Paragraph(
                        str(
                            anomalia.get(
                                "density_z",
                                0
                            )
                        ),
                        estilos["card_valor"]
                    ),

                    Paragraph(
                        "STATUS",
                        estilos["label"]
                    ),

                    Paragraph(
                        str(nivel),
                        ParagraphStyle(
                            "StatusRegiao",
                            fontName=f"{FONTE}-Bold",
                            fontSize=9,
                            textColor=cor_nivel
                        )
                    )
                ]

            ]

            tabela_metricas_regiao = Table(
                metricas_regiao,
                colWidths=[
                    39 * mm,
                    40 * mm,
                    45 * mm,
                    34 * mm
                ]
            )

            tabela_metricas_regiao.setStyle(
                TableStyle([

                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        CINZA_CLARO
                    ),

                    (
                        "INNERGRID",
                        (0, 0),
                        (-1, -1),
                        0.3,
                        CINZA_CLARO
                    ),

                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE"
                    ),

                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        7
                    ),

                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        7
                    ),

                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        6
                    ),

                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        6
                    )

                ])
            )

            elementos.append(
                tabela_metricas_regiao
            )

            elementos.append(
                Spacer(
                    1,
                    7 * mm
                )
            )

    else:

        elementos.append(
            criar_card(
                [
                    Paragraph(
                        "NENHUMA REGIÃO SINALIZADA",
                        estilos["card_titulo"]
                    ),

                    Spacer(
                        1,
                        5
                    ),

                    Paragraph(
                        "Nenhuma região de atenção foi identificada "
                        "pelos critérios atualmente utilizados pelo "
                        "sistema.",
                        estilos["texto"]
                    )
                ],
                LARGURA_UTIL,
                fundo=VERDE_MUITO_CLARO,
                borda=VERDE_CLARO,
                padding=12
            )
        )

    # =====================================================
    # CONCLUSÃO
    # =====================================================

    elementos.append(
        PageBreak()
    )

    elementos.append(
        Paragraph(
            "05",
            estilos["eyebrow"]
        )
    )

    elementos.append(
        Paragraph(
            "Conclusão técnica",
            estilos["secao"]
        )
    )

    elementos.append(
        linha_verde()
    )

    texto_conclusao = (

        f"A análise automatizada apresentou score final "
        f"de <b>{score:.2f}</b>, com classificação "
        f"<b>{classificacao}</b>. "

        f"Foram analisadas <b>{total_regioes}</b> regiões "
        f"textuais, das quais <b>{regioes_suspeitas}</b> "
        f"foram sinalizadas pelos critérios utilizados "
        f"pelo sistema. "

        "Os resultados apresentados representam indicadores "
        "computacionais obtidos durante a análise e devem "
        "ser interpretados em conjunto com os elementos "
        "visuais e documentais disponíveis. "

        "A classificação automatizada não constitui, "
        "isoladamente, uma determinação definitiva sobre "
        "a autenticidade ou falsificação do documento."
    )

    # -----------------------------------------------------
    # CARD PRINCIPAL DA CONCLUSÃO
    # -----------------------------------------------------

    elementos.append(
        criar_card(
            [
                Paragraph(
                    "SÍNTESE DO RESULTADO",
                    estilos["label"]
                ),

                Spacer(
                    1,
                    7
                ),

                Paragraph(
                    texto_conclusao,
                    estilos["conclusao"]
                )

            ],
            LARGURA_UTIL,
            fundo=VERDE_MUITO_CLARO,
            borda=VERDE_CLARO,
            padding=14
        )
    )

    elementos.append(
        Spacer(
            1,
            9 * mm
        )
    )

    # -----------------------------------------------------
    # RESUMO FINAL
    # -----------------------------------------------------

    resumo_final = Table(
        [[

            Paragraph(
                "SCORE FINAL",
                estilos["label"]
            ),

            Paragraph(
                f"{score:.1f}%",
                estilos["valor_grande"]
            ),

            Paragraph(
                "CLASSIFICAÇÃO",
                estilos["label"]
            ),

            Paragraph(
                str(classificacao),
                ParagraphStyle(
                    "ClassificacaoFinal",
                    fontName=f"{FONTE}-Bold",
                    fontSize=10,
                    textColor=cor_classificacao
                )
            )

        ]],
        colWidths=[
            35 * mm,
            45 * mm,
            38 * mm,
            40 * mm
        ]
    )

    resumo_final.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                BRANCO
            ),

            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.6,
                CINZA_CLARO
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                8
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                8
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                9
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                9
            )

        ])
    )

    elementos.append(
        resumo_final
    )

    elementos.append(
        Spacer(
            1,
            18 * mm
        )
    )

    # -----------------------------------------------------
    # AVISO TÉCNICO
    # -----------------------------------------------------

    elementos.append(
        criar_card(
            [
                Paragraph(
                    "NOTA TÉCNICA",
                    estilos["label"]
                ),

                Spacer(
                    1,
                    4
                ),

                Paragraph(
                    "Este relatório apresenta resultados produzidos "
                    "automaticamente pelo sistema VALID. A análise "
                    "computacional deve ser considerada uma ferramenta "
                    "de apoio e não substitui avaliação documental, "
                    "pericial ou contextual realizada por profissional "
                    "habilitado quando necessária.",
                    estilos["pequeno"]
                )
            ],
            LARGURA_UTIL,
            fundo=BRANCO,
            borda=CINZA_CLARO,
            padding=10
        )
    )

    elementos.append(
        Spacer(
            1,
            12 * mm
        )
    )

    elementos.append(
        Paragraph(
            "Relatório gerado automaticamente pelo sistema VALID.",
            ParagraphStyle(
                "FinalRelatorio",
                fontName=f"{FONTE}-Bold",
                fontSize=7.5,
                textColor=VERDE_ESCURO
            )
        )
    )

    elementos.append(
        Spacer(
            1,
            3
        )
    )

    elementos.append(
        Paragraph(
            agora.strftime(
                "Gerado em %d/%m/%Y às %H:%M"
            ),
            estilos["pequeno"]
        )
    )

    # =====================================================
    # GERA PDF
    # =====================================================

    doc.build(
        elementos,
        onFirstPage=desenhar_pagina,
        onLaterPages=desenhar_pagina
    )

    return caminho_pdf