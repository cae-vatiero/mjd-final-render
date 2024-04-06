from flask import Flask

app = Flask(__name__)

@app.route("/home")
def index():
  return "Esse é um teste do site"

@app.route("/sobremim")
def sobremim():
  return "teste sobre mim lala"

@app.route ("/portfolio")
def porfolio():
  return "meu porfolio"

@app.route("/contato")
def contato():
  return "meus contatos"