#fazendo as importações
from monitoramento import (
    pega_noticia, coloca_na_planilha,
    identifica_casos_brasileiros, identifica_violacao,
    noticias_selecionadas,
    classifica_violacao
)
from gnews import GNews
google_news = GNews()
import gspread
import os 
from oauth2client.service_account import ServiceAccountCredentials

from dotenv import load_dotenv

load_dotenv()
conteudo_credenciais = os.getenv("GSPREAD_CREDENTIALS")

arquivo_credenciais = "monitoramento-artigo19-5c4984346bfd.json"
conteudo_credenciais = os.environ["GSPREAD_CREDENTIALS"]
with open(arquivo_credenciais, mode="w") as arquivo:
    arquivo.write(conteudo_credenciais)

conta = ServiceAccountCredentials.from_json_keyfile_name(arquivo_credenciais)
api = gspread.authorize(conta)
planilha = api.open_by_key("1oim884TTeWfYwGTlWIm7pLPLT8SdlDZcNG9nW9jlcBY")
sheet = planilha.worksheet("raspagem_bruta")

#definindo os parametros
google_news.country = 'Brasil'
google_news.language = 'portuguese brasil'
google_news.period = '7d'
google_news.max_results = 3

# Palavras-chave para a busca de notícias
palavra_chave = "jornalista AND atacado"

# Raspando as notícias, resumindo e subindo na planilha
todas_noticias = pega_noticia(palavra_chave)
noticias_na_planilha = coloca_na_planilha(noticias_na_planilha)

# Utilizando o ChatGPT para identificar se são casos que ocorreram no Brasil
casos_brasileiros = identifica_casos_brasileiros(noticias_na_planilha)

# Utilizando o ChatGPT para identificar se é um caso de violação
com_violacao = identifica_violacao(casos_brasileiros)

# Subindo as notícias selecionadas em outra aba
nova_aba = noticias_selecionadas(com_violacao)

# Categorizando as violações
classifica_violacao()

