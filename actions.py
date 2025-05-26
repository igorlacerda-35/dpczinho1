import pandas as pd
import os
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

def carregar_dados():
    arquivos = [
        "Tabela - Filial Feira.xlsx",
        "Tabelas - Filial Caruaru.xlsx",
        "Tabelas - Filial Goiás.xlsx",
        "Tabelas - Matriz.xlsx"
    ]
    planilhas = []
    for arquivo in arquivos:
        caminho = os.path.join(os.path.dirname(__file__), arquivo)
        df = pd.read_excel(caminho)
        df["seqproduto"] = pd.to_numeric(df["seqproduto"], errors="coerce").astype("Int64")

        for coluna in df.columns:
            if coluna.lower() in ["mg", "ba", "pe", "go"]:
                df[coluna] = (
                    df[coluna]
                    .astype(str)
                    .str.strip()
                    .str.replace(r"[R$\s]", "", regex=True)
                    .str.replace(",", ".", regex=False)
                )
                df[coluna] = pd.to_numeric(df[coluna], errors="coerce")
        df.columns = [col.strip().lower() for col in df.columns]

        planilhas.append(df)

    return pd.concat(planilhas, ignore_index=True)


df_preco = carregar_dados()

class ActionSetarRegiao(Action):
    def name(self):
        return "action_setar_regiao"

    def run(self, dispatcher, tracker, domain):
        mensagem = tracker.latest_message.get("text", "").lower()
        regiao = None
        if "mg" in mensagem:
            regiao = "mg"
        elif "ba" in mensagem:
            regiao = "ba"
        elif "pe" in mensagem:
            regiao = "pe"
        elif "go" in mensagem:
            regiao = "go"

        if regiao:
            dispatcher.utter_message(text=f"Região registrada: {regiao.upper()}")
            return [SlotSet("regiao", regiao)]
        else:
            dispatcher.utter_message(text="Não consegui identificar a região. Por favor, informe MG, BA, PE ou GO.")
            return []

class ActionBuscarPreco(Action):
    def name(self):
        return "action_buscar_preco"

    def run(self, dispatcher, tracker, domain):
        regiao = tracker.get_slot("regiao")
        mensagem = tracker.latest_message.get("text", "").lower()

        print("REGIÃO (slot):", regiao)
        print("MENSAGEM:", mensagem)

        codigo = None
        for palavra in mensagem.split():
            if palavra.isdigit():
                codigo = int(palavra)
                break

        if not regiao:
            dispatcher.utter_message(text="Por favor, informe a região primeiro (MG, BA, PE ou GO).")
            return []

        if not codigo:
            dispatcher.utter_message(text="Por favor, informe um código de produto válido.")
            return []

        resultado = df_preco[df_preco["seqproduto"] == codigo]

        print("RESULTADO FILTRADO:")
        print(resultado)
        print("COLUNAS DISPONÍVEIS:", resultado.columns.tolist())

        if not resultado.empty:
            colunas_normalizadas = [col.lower() for col in resultado.columns]
            if regiao in colunas_normalizadas:
                nome_coluna = [col for col in resultado.columns if col.lower() == regiao][0]
                # Busca a primeira linha com preço válido
                resultado_valido = resultado[resultado[nome_coluna].notna()]
                if not resultado_valido.empty:
                    preco = resultado_valido.iloc[0][nome_coluna]
                    dispatcher.utter_message(text=f"Preço do produto {codigo} para a região {regiao.upper()}: R$ {preco:.2f}")
                else:
                    dispatcher.utter_message(text=f"O produto {codigo} não possui preço definido para a região {regiao.upper()}.")
            else:
                dispatcher.utter_message(text=f"Não há preço disponível para a região {regiao.upper()}.")
        else:
            dispatcher.utter_message(text=f"Produto {codigo} não encontrado na base de dados.")

        return []