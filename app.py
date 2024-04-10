from flask import Flask, render_template
from monitoramento import ultimas_atualizacoes

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

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("home.html")

@app.route("/sobremim")
def sobremim():
    return render_template("sobremim.html")

@app.route("/portfolio")
def portfolio():
    return render_template("portfolio.html")

@app.route("/contato")
def contato():
    return render_template("contato.html")

@app.route("/raspagem")
def raspagem():
    
    # Palavras-chave para a busca de notícias
    palavra_chave = "jornalista AND atacado"
    
    # Raspando as notícias, resumindo e subindo na planilha
    todas_noticias = pega_noticia(palavra_chave)
    noticias_na_planilha = coloca_na_planilha(noticias_resumidas)
    
    # Utilizando o ChatGPT para identificar se são casos que ocorreram no Brasil
    casos_brasileiros = identifica_casos_brasileiros(noticias_na_planilha)
    
    # Utilizando o ChatGPT para identificar se é um caso de violação
    com_violacao = identifica_violacao(casos_brasileiros)
    
    # Subindo as notícias selecionadas em outra aba
    nova_aba = noticias_selecionadas(com_violacao)

    # Categorizando as violações
    classifica_violacao()
    
    return """
    <html>
    <head>
        <title>Página de Raspagem</title>
    </head>
    <body>
        <h1>Essa é uma página de raspagem</h1>
        <h1>A raspagem foi realizada.</h1>
    </body>
    </html>
    """

@app.route("/monitoramento")
def monitoramento():
    # Inicia a construção do corpo da página HTML
    html = """
    <!DOCTYPE html>
    <html>
      <nav>
        <ul> 
          <li><a href="/sobremim">Sobre Mim</a></li>
          <li><a href="/portfolio">Portfólio</a></li>
          <li><a href="/contato">Contato</a></li>    
        </ul>
      </nav>
      <head>
        <title>Atualizações do Monitoramento de PPD</title>
      </head>
      <body>
        <h1>Monitoramento violações contra comunicadores - ARTIGO19</h1>
        <p>
          As notícias coletadas nos últimos 7 dias foram:
          <ul>
    """

    # Adiciona cada notícia à página HTML
    ultimas_noticias = ultimas_atualizacoes()
    html += """
            <!DOCTYPE html>
            <html>
            <head>
              <title>Últimas Atualizações</title>
            </head>
            <body>
              <h1>Últimas Atualizações</h1>
              <ul>
    """

    for noticia in ultimas_noticias:
        titulo = noticia[0]
        descricao = noticia[1]
        url = noticia[2]
        veiculo = noticia[3]
        categoria = noticia[4]

        html += f"""
        <li>
          <strong>Título:</strong> {titulo}<br>
          <strong>Descrição:</strong> {descricao}<br>
          <strong>URL:</strong> <a href="{url}">{url}</a><br>
          <strong>Veículo:</strong> {veiculo}<br>
          <strong>Categoria:</strong> {categoria}
        </li><br>
        """

    html += """
              </ul>
            </body>
            </html>
            """

    print(html)

    return html
