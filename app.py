from flask import Flask, request, json, render_template
from flask_bootstrap import Bootstrap
from PIL import Image
import spongebobify

def create_app():
  app = Flask(__name__)
  Bootstrap(app)

  return app

app = create_app()

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/spongebobify/", methods=["POST"])
@app.route("/spongebobify/<textToSponge>", methods = ["GET", "POST"])
def spongebobify_there(textToSponge = None):
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        data = json.loads(request.data)
        textToSponge = data['textToSponge']
        encoded_image = spongebobify.create_image(textToSponge, "static/fonts/impact.ttf", "static/images/spongebob.jpg")
        return encoded_image.decode('utf-8')
    else:
        return 'Content-Type not supported!'