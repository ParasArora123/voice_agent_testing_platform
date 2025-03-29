from flask import Flask
from flask_sock import Sock

from app.routes import main as main_blueprint

sock = Sock()

def create_app():
    app = Flask(__name__)

    # Initialize Sock with the Flask app for the websocket
    sock.init_app(app)

    # Register blueprints or import routes
    app.register_blueprint(main_blueprint)

    return app
