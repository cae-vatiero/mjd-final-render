from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/home")
def index():
  return render_template("home.html")

@app.route("/sobremim")
def sobremim():
  return "sobremim.html"

@app.route ("/portfolio")
def porfolio():
  return "porfolio.html"

@app.route("/contato")
def contato():
  return "contato.html"