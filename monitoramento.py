# -*- coding: utf-8 -*-
from gnews import GNews
google_news = GNews()
import gspread
import os 
import time
from oauth2client.service_account import ServiceAccountCredentials
from newspaper import Article
import nltk
nltk.download('punkt')


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

"""##Definindo os parametros de consulta"""

google_news.country = 'Brasil'
google_news.language = 'portuguese brasil'
google_news.period = '7d'
google_news.max_results = 1

"""##Raspando as notícias, resumindo e subindo na planilha"""

#entendendo a estrutura da resposta

#{'title': 'Jornalista condenado a 7 anos de prisão na Rússia por criticar ataque à Ucrânia - UOL Confere',
 #'description': 'Jornalista condenado a 7 anos de prisão na Rússia por criticar ataque à Ucrânia  UOL Confere',
 #'published date': 'Wed, 06 Mar 2024 12:25:11 GMT',
 #'url': 'https://news.google.com/rss/articles/CBMijwFodHRwczovL25vdGljaWFzLnVvbC5jb20uYnIvdWx0aW1hcy1ub3RpY2lhcy9hZnAvMjAyNC8wMy8wNi9qb3JuYWxpc3RhLWNvbmRlbmFkby1hLTctYW5vcy1kZS1wcmlzYW8tbmEtcnVzc2lhLXBvci1jcml0aWNhci1hdGFxdWUtYS11Y3JhbmlhLmh0bdIBAA?oc=5&hl=en-US&gl=US&ceid=US:en',
 #'publisher': {'href': 'https://noticias.uol.com.br', 'title': 'UOL Confere'}}

def pega_noticia(tema):

  lista_noticias = google_news.get_news(tema)
  coluna4 = sheet.col_values(4)
  noticias_raspadas = []

  for noticia in lista_noticias:
    url = noticia["url"]
    noticia["description"] = "" #ele apenas repetia o título e não gerava um resumo

    if url in coluna4:  # Verifica se a URL já está na lista de valores da coluna D
      print("Pulando notícia já processada")
      continue  # Pula para próxima notícia

    noticias_raspadas.append(noticia)


  print("As notícias foram raspadas.")
  return noticias_raspadas

def adiciona_resumo(todas_noticias):

    for noticia in todas_noticias:

        try:
            article = Article(noticia['url'])
            article.download()
            article.parse()
            article.nlp()
            novo_resumo = article.summary
            noticia['description'] = novo_resumo

        except Exception as e:
            print(f"Erro ao processar a notícia: {e}")
            continue  # Pula para a próxima notícia em caso de erro

    print("Os resumos foram adicionados.")
    return todas_noticias

def coloca_na_planilha(noticias_raspadas):

  for noticia in noticias_raspadas:

    titulo = noticia["title"]
    descricao = noticia["description"]
    data = noticia["published date"]
    url = noticia["url"]
    veiculo = noticia["publisher"]["title"]

    time.sleep(1)

    sheet.append_row([titulo, descricao, data, url, veiculo])

  print("As notícias foram adicionadas na planilha.")
  return noticias_raspadas

"""##Filtrando notícias que aconteceram no brasil e se houve violação"""

openai_api_key = os.getenv("openai_api_key")
# Coloque aqui a api key que você colou de lá.
openai_api_key = os.environ["openai_api_key"]

# Depois importamos a biblioteca
from openai import OpenAI

# E criamos um "cliente", que vai acessar a API
client = OpenAI(api_key = openai_api_key)

def identifica_casos_brasileiros(noticias_brasileiras):

  dicionario_de_noticias = sheet.get_all_records()

  pergunta1 = """Chat, eu vou te passar um resumo de uma notícia e quero que você APENAS me responda com 'Sim' ou 'Não'

      RESUMO DA NOTÍCIA:

      """
  pergunta2 = """PERGUNTA:

      O caso se refere a algo que aconteceu no Brasil? Preste atenção. Pode ser que a notícia esteja falando de um caso que não aconteceu no território brasileiro."""

  for index, noticia in enumerate(dicionario_de_noticias, start=2):

        do_brasil = noticia["caso brasileiro"]
        if "Sim" in do_brasil or "Não" in do_brasil or "Sim." in do_brasil or "Não." in do_brasil:  # Verifica se já foi preenchida
          continue  # Pula para próxima notícia
          print("Pulei as notícias que já foram avaliadas.")

        titulo = noticia["título"]
        resumo = noticia["descrição"]

        pergunta_completa = pergunta1 + titulo + """

        """ + resumo + """

        """ + pergunta2

        chat = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": pergunta_completa,
                    }
                ],
                model="gpt-3.5-turbo",
            )

        resposta = chat.choices[0].message.content
        time.sleep(1)
        sheet.update_cell(index, 6, resposta)
  print("Identificação de casos que aconteceram no Brasil concluído.")
  return noticias_brasileiras

def identifica_violacao(violacao):

  dicionario_de_noticias = sheet.get_all_records()

  pergunta1 = """Chat, eu vou te passar um resumo de uma notícia e quero que você APENAS me responda com 'Sim' ou 'Não'

        RESUMO DA NOTÍCIA:

        """
  pergunta2 = """PERGUNTA:

        A notícia se refere a algum jornalista, comunicador, radialista ou blogueiro atacado, agredido, assassinado, ou algum tipo de censura, ataque ou violação à imprensa?

        Preste atenção. Se um profissional morreu, foi assaltado ou roubado, mas não há no resumo indicando que isso aconteceu em decorrência de seu trabalho você deve dizer ‘Não’. Porque não configura como um ataque profissional."""


  for index, noticia in enumerate(dicionario_de_noticias, start=2):

    houve_violacao = noticia["relação com atuação profissional"]
    do_brasil = do_brasil = noticia["caso brasileiro"]
    if "Não" in do_brasil or "Não." in do_brasil:
      continue
    elif "Sim" in  houve_violacao or "Não" in  houve_violacao or "Sim." in houve_violacao or "Não." in  houve_violacao:  # Verifica se já foi preenchida
      continue  # Pula para próxima notícia

    else:
      titulo = noticia["título"]
      resumo = noticia["descrição"]

      pergunta_completa = pergunta1 + titulo + """

            """ + resumo + """

            """ + pergunta2

      chat = client.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": pergunta_completa,
                        }
                    ],
                    model="gpt-3.5-turbo",
                )

      resposta = chat.choices[0].message.content
      time.sleep(1)
      sheet.update_cell(index, 7, resposta)
      print("Atualização na linha", index, "com resposta:", resposta)

  print("Identificação de violação concluída.")
  return violacao

"""##Subindo a primeira limpeza de noticias em outra aba"""

def noticias_selecionadas(limpas):

  noticias_limpas = planilha.worksheet('noticias_limpas')
  todas_noticias = sheet.get_all_records()

  for linha in todas_noticias:

      resposta_brasil = linha["caso brasileiro"]
      resposta_violacao = linha["relação com atuação profissional"]
      url = linha["url"]
      coluna4 = noticias_limpas.col_values(4)

      if url in coluna4:
        print("Pulando notícia já processada")
        continue

      elif "Não" in resposta_brasil or "Não." in resposta_brasil:
        continue

      elif " " in resposta_violacao or "Não" in resposta_violacao or "Não." in resposta_violacao:
        continue

      else:
        dados_para_copiar = [linha["título"], linha["descrição"], linha["data de publicação"], linha["url"], linha["veículo"], linha["caso brasileiro"], linha["relação com atuação profissional"]]
        time.sleep(1)
        noticias_limpas.append_row(dados_para_copiar)

  print("Noticias limpas selecionadas e adicionadas na segunda aba da planilha")
  return limpas

"""##Retira notícias de diferentes portais que falem do mesmo tema"""

def verifica_tema_duplicado(duplicado):

  noticias_limpas = planilha.worksheet('noticias_limpas')
  dicionario_de_noticias = noticias_limpas.get_all_records()

  pergunta = """Chat, eu vou te dar o título de uma notícia e uma lista com outras notícias. Eu quero que você veja se por acaso a informação que tem no título que eu te passei já consta nessa lista.

      Os títulos não vão estar iguais, mas podem estar falando do mesmo assunto. Nesse caso, você deve responder APENAS com "Sim" ou "Não".

      Título:

      """
  lista = """Lista:

      """


  for index, noticia in enumerate(dicionario_de_noticias, start=2):

              titulo = noticia["título"]
              duplicado = noticia["tema duplicado"]

              if "sem duplicata" in duplicado:
                print("Não há duplicata de temas")
                continue

              # Código para pegar os títulos das outras notícias que não são iguais ao título atual

              outros_titulos = [outra_noticia["título"] for outra_noticia in dicionario_de_noticias if outra_noticia["título"] != titulo]
              outros_titulos_str = "\n".join(outros_titulos)


              pergunta_completa = pergunta + titulo + """

              """ + lista + """

              """ + outros_titulos_str

              chat = client.chat.completions.create(
                      messages=[
                          {
                              "role": "user",
                              "content": pergunta_completa,
                          }
                      ],
                      model="gpt-3.5-turbo",
                  )

              resposta = chat.choices[0].message.content


              if resposta == "Sim":
                noticias_limpas.delete_rows(index)
                print(f"Linha {index} apagada. Título: {titulo}")

  num_linhas = len(noticias_limpas.col_values(1))  # Obter o número total de linhas
  for i in range(2, num_linhas + 1):
          time.sleep(1)
          noticias_limpas.update_cell(i, 8, "sem duplicata")

  print("Mensagem 'está ok' adicionada em todas as linhas restantes na coluna 8.")
  return "Processo de limpeza concluído com sucesso."

"""##Categorizando as notícias limpas"""

def classifica_violacao(casos):

  noticias_limpas = planilha.worksheet('noticias_limpas')
  todas_noticias = noticias_limpas.get_all_records()

  pergunta = """ Chat, eu vou te passar o resumo de uma notícia e quero que você faça duas coisas: classifique se a notícia e escreva uma justificativa em uma frase da sua escolha.

  Categorias:

  Ameaça física
  Ameaça digital
  Ameaça legal/Jurídica
  Outros

  Atenção: você deve me responder somente com o nome da classificação e a sua breve justificativa, nada além disso.

  Atenção: você deve usar a opção 'Ameaças legais/Jurídicas' apenas em casos em que profissionais da comunicação foram PROCESSADOS, PRESOS ou tiveram os seus equipamentos APREENDIDOS; Já a categoria 'Outros' você deve classificar em casos que não mencionam as categorias anteriores.

  Resumo da notícia:

  """


  for index, noticia in enumerate(todas_noticias, start=2):

    classificacao = noticia["categoria e justificativa"]
    coluna9 = noticias_limpas.col_values(9)

    if "Ameaça física" in classificacao or "Ameaça digital" in classificacao or "Ameaça legal/Jurídica" in classificacao or "Outros" in classificacao:
      print("Notícia já avaliada")
      continue

    else:
        titulo = noticia["título"]
        resumo = noticia["descrição"]

        pergunta_completa = pergunta + titulo + """

             """ + resumo

        chat = client.chat.completions.create(
                      messages=[
                          {
                              "role": "user",
                              "content": pergunta_completa,
                          }
                      ],
                      model="gpt-3.5-turbo",
                  )

        resposta = chat.choices[0].message.content
        time.sleep(1)
        noticias_limpas.update_cell(index, 9, resposta)
        print("Atualização na linha", index, "com resposta:", resposta)


  print("Noticias limpas devidamente classificadas")
  return casos

"""##Pegando as últimas atualizações"""

def ultimas_atualizacoes():
  noticias_limpas = planilha.worksheet('noticias_limpas')

  todas_noticias = noticias_limpas.get_all_records()
  resposta = []

  for index, noticia in enumerate(todas_noticias, start=2):

        titulo = noticia["título"]
        descricao = noticia["descrição"]
        url = noticia["url"]
        veiculo = noticia["veículo"]
        categoria = noticia["categoria e justificativa"]
        email= noticia["e-mail enviado"]

        #if "Enviado" in email:
          #print("Notícia já enviada por e-mail na última semana")
          #continue

        #else:

        resposta.append([titulo, descricao, url, veiculo, categoria])
          #noticias_limpas.update_cell(index, 10, "Enviado")

  return resposta
