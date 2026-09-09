"""
core/cpf_validator.py

Extração, validação e correção robusta de CPF a partir de texto OCR (Tesseract).

Problema que este módulo resolve:
    O Tesseract às vezes "come" um dígito do CPF (ex: funde dois dígitos iguais,
    confunde letra/dígito, ou perde um caractere em fontes ruins). O resultado é
    uma string de 9, 10 ou 12 "dígitos" onde deveria haver 11.

Estratégia (em ordem de confiabilidade):
    1. Normalizar confusões de caractere comuns do OCR (O->0, I/l->1, S->5, B->8...)
       ANTES de descartar pontuação — isso evita perder informação estrutural.
    2. Usar a posição dos separadores (. e -) do padrão XXX.XXX.XXX-XX como pista
       de ONDE está o dígito faltando/sobrando, em vez de testar 11 posições às cegas.
    3. Validar sempre pelo dígito verificador (checksum) oficial da Receita Federal.
    4. Só "corrigir automaticamente" quando existir candidato ÚNICO válido.
       Se houver ambiguidade, retornar todos os candidatos com uma flag de
       incerteza — para revisão humana ou cruzamento com um segundo documento
       (próxima etapa do seu pipeline).

Uso rápido:
    >>> from cpf_utils import find_cpf
    >>> resultado = find_cpf("Nome: Joao\\nCPF 4707640869\\nData: ...")
    >>> resultado.status
    'ambiguous'
    >>> resultado.candidates
    ['44707640869', '47076404869', '47076408694']
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional


# ---------------------------------------------------------------------------
# 1. Normalização de confusões comuns do OCR (letra <-> dígito)
# ---------------------------------------------------------------------------

# Mapa aplicado SÓ dentro de trechos que já parecem numéricos (perto do rótulo
# "CPF"), para não corromper texto normal do documento.
_OCR_DIGIT_LOOKALIKES = {
    "O": "0", "o": "0", "D": "0", "Q": "0",
    "I": "1", "l": "1", "|": "1",
    "Z": "2",
    "S": "5", "s": "5",
    "G": "6", "b": "6",
    "T": "7",
    "B": "8",
    "g": "9", "q": "9",
}


def normalize_ocr_chars(raw: str) -> str:
    """Substitui letras visualmente parecidas com dígitos por dígitos."""
    return "".join(_OCR_DIGIT_LOOKALIKES.get(ch, ch) for ch in raw)


# ---------------------------------------------------------------------------
# 2. Extração do trecho candidato a CPF no texto OCR
# ---------------------------------------------------------------------------

# Captura algo como "CPF 470.764.086-9", "CPF: 4707640869" ou o formato
# bilíngue de RGs mais novos, onde o rótulo e o valor ficam separados por
# outros campos/quebras de linha:
#   "Registro Geral - CPF / Personal Number     Sexo/Sex
#    F
#
#    088.794.450-7"
# A tolerância de distância é generosa (até 80 caracteres, incluindo
# quebras de linha) porque documentos reais variam bastante em como
# organizam rótulo e valor — o valor em si ainda precisa ter cara de CPF
# (dígitos/pontuação), então um "achado" errado tende a ser descartado
# depois pela validação de checksum, não silenciosamente aceito.
_CPF_LABEL_RE = re.compile(
    r"C\s*P\s*F.{0,80}?"
    r"([0-9OIloqQgGbBsSzZtT][0-9OIloqQgGbBsSzZtT.\-\s]{7,17}[0-9OIloqQgGbBsSzZtT])",
    re.IGNORECASE | re.DOTALL,
)


def extract_raw_candidate(text: str) -> Optional[str]:
    """Retorna o trecho bruto (com pontuação) logo após o rótulo 'CPF' no texto."""
    match = _CPF_LABEL_RE.search(text)
    if not match:
        return None
    return match.group(1)


# ---------------------------------------------------------------------------
# 3. Validação oficial do dígito verificador do CPF
# ---------------------------------------------------------------------------

def is_valid_cpf(cpf: str) -> bool:
    """Valida um CPF de 11 dígitos pelo algoritmo oficial (módulo 11)."""
    if not re.fullmatch(r"\d{11}", cpf):
        return False
    if len(set(cpf)) == 1:  # sequências tipo 00000000000 são inválidas
        return False

    digits = [int(c) for c in cpf]

    soma = sum(digits[i] * (10 - i) for i in range(9))
    d1 = (soma * 10) % 11
    d1 = 0 if d1 == 10 else d1
    if d1 != digits[9]:
        return False

    soma = sum(digits[i] * (11 - i) for i in range(10))
    d2 = (soma * 10) % 11
    d2 = 0 if d2 == 10 else d2
    if d2 != digits[10]:
        return False

    return True


# ---------------------------------------------------------------------------
# 4. Correção guiada por estrutura (separadores) + fallback por checksum
# ---------------------------------------------------------------------------

@dataclass
class CpfResult:
    status: str  # "valid" | "corrected" | "ambiguous" | "not_found" | "invalid"
    value: Optional[str] = None          # CPF final (só quando valid/corrected)
    raw_ocr_text: Optional[str] = None   # o que o OCR realmente leu
    candidates: List[str] = field(default_factory=list)  # quando ambiguous


def _digits_only(s: str) -> str:
    return re.sub(r"\D", "", s)


def _try_structural_correction(raw: str) -> List[str]:
    """
    Usa a posição dos separadores (. e -) do formato XXX.XXX.XXX-XX para
    descobrir qual GRUPO ficou com dígito a menos/a mais, em vez de testar
    todas as posições da string inteira. Reduz muito a ambiguidade.
    """
    groups = re.split(r"[.\-\s]+", raw.strip())
    groups = [g for g in groups if g]
    expected_lens = [3, 3, 3, 2]

    # só vale a pena se o número de grupos bate com o esperado (4 grupos)
    if len(groups) != 4:
        return []

    candidates = []
    for i, (g, exp) in enumerate(zip(groups, expected_lens)):
        diff = len(g) - exp
        if diff == -1:  # falta 1 dígito nesse grupo específico
            for pos in range(len(g) + 1):
                for d in "0123456789":
                    new_g = g[:pos] + d + g[pos:]
                    new_groups = groups.copy()
                    new_groups[i] = new_g
                    candidate = "".join(new_groups)
                    if is_valid_cpf(candidate):
                        candidates.append(candidate)
        elif diff == 1:  # sobrou 1 dígito nesse grupo
            for pos in range(len(g)):
                new_g = g[:pos] + g[pos + 1:]
                new_groups = groups.copy()
                new_groups[i] = new_g
                candidate = "".join(new_groups)
                if is_valid_cpf(candidate):
                    candidates.append(candidate)

    return sorted(set(candidates))


def _try_blind_correction(digits: str) -> List[str]:
    """
    Fallback quando não há separadores confiáveis: testa inserção (se faltam
    dígitos) ou remoção (se sobram) em CADA posição, mantendo só os que
    resultam em CPF válido. Costuma gerar mais de um candidato — por isso
    é usado só como fallback, e o resultado deve ser tratado como incerto
    a menos que haja um único candidato.
    """
    candidates = set()
    n = len(digits)

    if n == 10:
        for pos in range(n + 1):
            for d in "0123456789":
                cand = digits[:pos] + d + digits[pos:]
                if is_valid_cpf(cand):
                    candidates.add(cand)
    elif n == 12:
        for pos in range(n):
            cand = digits[:pos] + digits[pos + 1:]
            if is_valid_cpf(cand):
                candidates.add(cand)

    return sorted(candidates)


def find_cpf(text: str) -> CpfResult:
    """
    Ponto de entrada principal: recebe o texto OCR completo do documento e
    devolve um CpfResult com status claro sobre o que foi encontrado.
    """
    raw = extract_raw_candidate(text)
    if raw is None:
        return CpfResult(status="not_found")

    normalized = normalize_ocr_chars(raw)
    digits = _digits_only(normalized)

    # Caso ideal: já veio com 11 dígitos e é válido
    if len(digits) == 11 and is_valid_cpf(digits):
        return CpfResult(status="valid", value=digits, raw_ocr_text=raw)

    # Tenta correção estrutural primeiro (mais confiável, usa os separadores)
    structural = _try_structural_correction(normalized)
    if len(structural) == 1:
        return CpfResult(status="corrected", value=structural[0], raw_ocr_text=raw)
    if len(structural) > 1:
        return CpfResult(status="ambiguous", raw_ocr_text=raw, candidates=structural)

    # Fallback: correção "cega" só quando há 10 ou 12 dígitos
    blind = _try_blind_correction(digits)
    if len(blind) == 1:
        return CpfResult(status="corrected", value=blind[0], raw_ocr_text=raw)
    if len(blind) > 1:
        return CpfResult(status="ambiguous", raw_ocr_text=raw, candidates=blind)

    # Achou dígitos mas não bateu 11 nem foi possível corrigir com confiança
    if len(digits) == 11:
        return CpfResult(status="invalid", raw_ocr_text=raw, candidates=[digits])

    return CpfResult(status="not_found", raw_ocr_text=raw)


# ---------------------------------------------------------------------------
# Demonstração com o caso real que você reportou
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    exemplos = [
        "Nome: Joao da Silva\nCPF 4707640869\nData: 01/01/2024",
        "CPF: 470.764.086-9",   # com separadores -> corrige sem ambiguidade
        "CPF 111.444.777-35",   # CPF válido já correto
    ]
    for texto in exemplos:
        r = find_cpf(texto)
        print(f"texto={texto!r}")
        print(f"  -> status={r.status} value={r.value} candidates={r.candidates}\n")
