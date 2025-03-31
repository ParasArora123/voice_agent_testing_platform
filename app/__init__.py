from flask import Flask
from flask_sock import Sock

sock = Sock()

def create_app():
    app = Flask(__name__)

    # Initialize Sock with the Flask app for the websocket
    sock.init_app(app)

    # We need to wait to import routes until after initializing the app
    from app.routes import main as main_blueprint

    # Register blueprints or import routes
    app.register_blueprint(main_blueprint)

    return app
