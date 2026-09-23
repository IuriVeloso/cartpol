import json
import numpy as np

def pertinencia(valor, tipo, parametros):
    if tipo == "trapezoidal":
        a, b, c, d = parametros
        if valor <= a or valor >= d:
            return 0.0
        if b <= valor <= c:
            return 1.0
        if a < valor < b:
            return (valor - a) / (b - a)
        return (d - valor) / (d - c)

    if tipo == "trapezoidal_esq":
        b, c = parametros
        if valor <= b:
            return 1.0
        if b < valor < c:
            return (c - valor) / (c - b)
        return 0.0

    if tipo == "trapezoidal_dir":
        a, b = parametros
        if valor >= b:
            return 1.0
        if a < valor < b:
            return (valor - a) / (b - a)
        return 0.0

    if tipo == "triangular":
        a, b, c = parametros
        if valor <= a or valor >= c:
            return 0.0
        if valor == b:
            return 1.0
        if a < valor < b:
            return (valor - a) / (b - a)
        return (c - valor) / (c - b)

    if tipo == "triangular_esq":
        b, c = parametros
        if valor <= b:
            return 1.0
        if b < valor < c:
            return (c - valor) / (c - b)
        return 0.0

    if tipo == "triangular_dir":
        a, b = parametros
        if valor >= b:
            return 1.0
        if a < valor < b:
            return (valor - a) / (b - a)
        return 0.0

    raise ValueError(tipo)


class SistemaFuzzyMamdani:
    def __init__(self, arq_variaveis, arq_regras, tnorma=min, tconorma=max, defuzz="centroide"):
        self.variaveis = {}
        self.entradas = []
        self.saida = None
        self.tnorma = tnorma
        self.tconorma = tconorma
        self.defuzz = defuzz

        # carregamento das variaveis fuzzy
        for variavel in json.load(open(arq_variaveis))["variaveis"]:
            self.variaveis[variavel["nome"]] = variavel
            if variavel["tipo"] == "entrada":
                self.entradas.append(variavel["nome"])
            else:
                self.saida = variavel["nome"]

        # carregamento das regras fuzzy
        self.regras = json.load(open(arq_regras))["regras"]

    # retorna um dict de pertinências do valor na variável
    def fuzzificar(self, variavel, valor):
        resposta = {}
        for conjunto in self.variaveis[variavel]["conjuntos"]:
            resposta[conjunto["nome"]] = pertinencia(valor, conjunto["tipo"], conjunto["parametros"])
        return resposta

    def inferir(self, entradas):

        # prepara o conjunto fuzzy final
        var_saida = self.variaveis[self.saida]
        dominio = np.linspace(*var_saida["dominio"], 400)
        agregado = np.zeros_like(dominio)

        # retorna um dict de pertinências de todo o registro
        fuzz = {variavel: self.fuzzificar(variavel, entradas[variavel]) for variavel in entradas}

        # aplica o registro fuzzificado às regras
        for regra in self.regras:
            # obtém as pertinências das condições
            graus = [
                fuzz[antecedente["variavel"]][antecedente["conjunto"]]
                for antecedente in regra["antecedente"]
            ]

            # obtém o grau de realização da regra
            alfa = self.tnorma(graus) * regra["certeza"]

            # identifica o conjunto resposta da regra
            conj = next(
                conjunto for conjunto in var_saida["conjuntos"]
                if conjunto["nome"] == regra["consequente"]["conjunto"]
            )

            # aplica o grau de realização à regra, produzindo o conjunto-resposta da regra
            mu = np.array([
                min(alfa, pertinencia(valor, conj["tipo"], conj["parametros"]))
                for valor in dominio
            ])

            # agrega (união, máximo) o conjunto-resposta de agora aos demais
            agregado = np.maximum(agregado, mu)

        # defuzzifica o conjunto-resposta final (agregado)
        if self.defuzz == "centroide":
            return np.sum(dominio * agregado) / np.sum(agregado) if np.sum(agregado) else 0.0
        if self.defuzz == "media_dos_maximos":
            indices = np.where(agregado == np.max(agregado))[0]
            return np.mean(dominio[indices])
        if self.defuzz == "maior_dos_maximos":
            return dominio[np.where(agregado == np.max(agregado))[0][-1]]
        if self.defuzz == "menor_dos_maximos":
            return dominio[np.where(agregado == np.max(agregado))[0][0]]

        raise ValueError(self.defuzz)


# Código de teste - executado apenas quando o arquivo é chamado diretamente
if __name__ == "__main__":
    sf = SistemaFuzzyMamdani(
        arq_variaveis="cartpol_app/scripts/fuzzy_logic/variaveis-fuzzy.json",
        arq_regras="cartpol_app/scripts/fuzzy_logic/regras-fuzzy.json",
        defuzz="centroide"
    )
    entradas = {
        "ruesp_can": 6.5,
        "tam_conglomerado": 3,
        "qtd_bairros": 15
    }
    resultado = sf.inferir(entradas)
    print(resultado)