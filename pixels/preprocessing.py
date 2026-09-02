# ==========================================================
# preprocessing.py
# Responsável por preparar a imagem antes da análise
# ==========================================================

from .utils import (
    load_image,
    resize_image,
    remove_border,
    convert_gray,
    equalize_image,
    denoise_image,
    threshold_image
)


def preprocess_image(image_path):

    image = load_image(image_path)

    image = resize_image(image)

    image = remove_border(image)

    gray = convert_gray(image)

    gray = equalize_image(gray)

    gray = denoise_image(gray)

    return image, gray


def preprocess_binary(image_path):
    """
    Executa o pré-processamento e retorna
    a imagem binarizada (preto e branco).
    Útil para OCR e detecção de texto.
    """

    gray = preprocess_image(image_path)

    binary = threshold_image(gray)

    return binary