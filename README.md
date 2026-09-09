# eocr-pixel-mescla

O projeto mantém a análise EOCR/Pixel original e também expõe o módulo VALID.

## Rotas existentes

- `GET /`: verifica se a API está funcionando.
- `POST /analisar`: executa a análise EOCR/Pixel original. O campo do arquivo é `imagem`.
- `GET /results/<arquivo>`: disponibiliza as imagens de resultado.

## Rotas do VALID

- `GET /valid/`: verifica o status do módulo.
- `GET /valid/interface`: abre a interface visual do sistema.
- `POST /valid/analisar`: analisa OCR, CPF, datas e metadados. O campo é `arquivo`.
- `POST /valid/comparar`: compara dois documentos. Os campos são `documento1` e `documento2`.

Formatos aceitos pelo VALID: JPG, JPEG, PNG e PDF.

Além das dependências Python, o VALID requer o Tesseract OCR instalado no sistema e o idioma português (`por.traineddata`) disponível. No Windows, o caminho padrão usado pelo projeto é `C:\\Program Files\\Tesseract-OCR`.
