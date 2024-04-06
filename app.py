from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/")
def index():
  return render_template("home.html")

@app.route("/sobremim")
def sobremim():
  return render_template("sobremim.html")

@app.route ("/portfolio")
def porfolio():
  return render_template("porfolio.html")

@app.route("/contato")
def contato():
  return render_template("contato.html")