import re
import unicodedata


class DocumentComparator:
    """Compara campos extraídos sem confundir compatibilidade com autenticidade."""

    LIMIAR_NOME_PARCIAL = 0.5
    CONECTIVOS_NOME = {"DA", "DE", "DO", "DAS", "DOS", "E"}
    PESOS = {"nome": 40, "cpf": 50, "data": 10}

    def compare(self, documento1, documento2):
        campos1 = documento1.data.get("fields", {})
        campos2 = documento2.data.get("fields", {})

        nome_status, nome_similaridade = self._comparar_nomes(
            campos1.get("nome"),
            campos2.get("nome"),
        )
        cpf_status = self._comparar_cpfs(campos1, campos2)
        data_status = self._comparar_datas(
            campos1.get("datas", []),
            campos2.get("datas", []),
        )

        resultados = {
            "nome": nome_status,
            "cpf": cpf_status,
            "data": data_status,
        }
        compatibilidade = self._calcular_compatibilidade(resultados)
        quantidade_comparavel = sum(
            status != "NAO_IDENTIFICADO"
            for status in resultados.values()
        )

        if quantidade_comparavel < 2:
            status = "SEM DADOS SUFICIENTES"
        elif cpf_status in {"INVALIDO", "AMBIGUO"}:
            status = "REQUER_REVISAO"
        elif compatibilidade is not None and compatibilidade >= 70:
            status = "COMPATIVEL"
        else:
            status = "INCONSISTENTE"

        return {
            "status": status,
            "campos": resultados,
            "compatibilidade": compatibilidade,
            "detalhes": {
                "nome_similaridade": nome_similaridade,
                "campos_comparaveis": quantidade_comparavel,
            },
        }

    def _normalizar_nome(self, nome):
        if not nome:
            return None

        nome = unicodedata.normalize("NFD", nome)
        nome = "".join(
            caractere
            for caractere in nome
            if unicodedata.category(caractere) != "Mn"
        )
        return " ".join(nome.upper().split())

    def _tokens_nome(self, nome):
        normalizado = self._normalizar_nome(nome)
        if not normalizado:
            return set()
        return {
            palavra
            for palavra in normalizado.split()
            if palavra not in self.CONECTIVOS_NOME
        }

    def _comparar_nomes(self, nome1, nome2):
        tokens1 = self._tokens_nome(nome1)
        tokens2 = self._tokens_nome(nome2)

        if not tokens1 or not tokens2:
            return "NAO_IDENTIFICADO", None

        similaridade = len(tokens1 & tokens2) / len(tokens1 | tokens2)
        similaridade = round(similaridade, 2)

        if similaridade == 1:
            return "COMPATIVEL", similaridade
        if similaridade >= self.LIMIAR_NOME_PARCIAL:
            return "PARCIALMENTE_COMPATIVEL", similaridade
        return "DIVERGENTE", similaridade

    @staticmethod
    def _normalizar_cpf(cpf):
        if not cpf:
            return None
        normalizado = re.sub(r"\D", "", cpf)
        return normalizado or None

    def _comparar_cpfs(self, campos1, campos2):
        status1 = campos1.get("cpf_status")
        status2 = campos2.get("cpf_status")

        if status1 == "ambiguous" or status2 == "ambiguous":
            return "AMBIGUO"
        if status1 == "invalid" or status2 == "invalid":
            return "INVALIDO"

        cpf1 = self._normalizar_cpf(campos1.get("cpf"))
        cpf2 = self._normalizar_cpf(campos2.get("cpf"))

        if not cpf1 or not cpf2:
            return "NAO_IDENTIFICADO"
        return "COMPATIVEL" if cpf1 == cpf2 else "DIVERGENTE"

    @staticmethod
    def _normalizar_data(data):
        if not data:
            return ""
        return data.replace("-", "/").replace(" ", "")

    def _comparar_datas(self, datas1, datas2):
        if not datas1 or not datas2:
            return "NAO_IDENTIFICADO"

        normalizadas1 = {self._normalizar_data(data) for data in datas1}
        normalizadas2 = {self._normalizar_data(data) for data in datas2}
        return "COMPATIVEL" if normalizadas1 & normalizadas2 else "DIVERGENTE"

    def _calcular_compatibilidade(self, resultados):
        pontos = 0
        peso_utilizado = 0

        for campo, resultado in resultados.items():
            if resultado == "NAO_IDENTIFICADO":
                continue

            peso = self.PESOS[campo]
            peso_utilizado += peso

            if resultado == "COMPATIVEL":
                pontos += peso
            elif resultado == "PARCIALMENTE_COMPATIVEL":
                pontos += peso * 0.5

        if peso_utilizado == 0:
            return None
        return round((pontos / peso_utilizado) * 100, 2)

