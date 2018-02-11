from flask import Flask

app = Flask(__name__)
app.config["SECRET_KEY"] = "super-secret"

from mafia.views import start, play, done
