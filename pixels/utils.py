# ==========================================================
# utils.py
# Funções responsáveis por preparar a imagem para análise
# ==========================================================

import cv2


# ==========================================================
# Abre a imagem
# ==========================================================
def load_image(path):

    # Lê a imagem do disco e transforma em uma matriz de pixels
    image = cv2.imread(path)

    # Verifica se a imagem foi encontrada
    if image is None:
        raise Exception("Imagem não encontrada")

    return image


# ==========================================================
# Redimensiona a imagem mantendo a proporção
# ==========================================================
def resize_image(image, width=1500):

    # Obtém altura e largura atuais
    height, current_width = image.shape[:2]

    # Calcula a proporção
    ratio = width / current_width

    # Calcula a nova altura mantendo a proporção
    new_height = int(height * ratio)

    # Redimensiona a imagem
    resized = cv2.resize(
        image,
        (width, new_height),
        interpolation=cv2.INTER_AREA
    )

    return resized


# ==========================================================
# Remove pequenas bordas da imagem
# ==========================================================
def remove_border(image, border=20):

    # Descobre altura e largura
    height, width = image.shape[:2]

    # Recorta alguns pixels das bordas
    cropped = image[
        border:height-border,
        border:width-border
    ]

    return cropped


# ==========================================================
# Converte para escala de cinza
# ==========================================================
def convert_gray(image):

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    return gray


# ==========================================================
# Melhora o contraste da imagem
# ==========================================================
def equalize_image(gray):

    equalized = cv2.equalizeHist(
        gray
    )

    return equalized


# ==========================================================
# Remove pequenos ruídos
# ==========================================================
def denoise_image(gray):

    denoised = cv2.GaussianBlur(
        gray,
        (5,5),
        0
    )

    return denoised


# ==========================================================
# Converte para preto e branco
# ==========================================================
def threshold_image(gray):

    _, thresh = cv2.threshold(

        gray,

        0,

        255,

        cv2.THRESH_BINARY +
        cv2.THRESH_OTSU

    )

    return thresh