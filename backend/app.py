
import os

from flask import Flask
from flask_cors import CORS

from routes.translation_route import translation_bp
from routes.speech import bp as speech_bp

app = Flask(__name__)
CORS(
    app,
    resources={
        r"/*": {
            "origins": "*",
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type"],
        }
    },
)

# Only expose APIs needed for the speech → translation → speech pipeline
app.register_blueprint(translation_bp, url_prefix="/api")
app.register_blueprint(speech_bp, url_prefix="/api")

if __name__ == "__main__":
    # IMPORTANT: disable the Flask reloader when working with large torch models.
    # The reloader can start multiple processes and/or reload repeatedly, which can
    # cause the model to load multiple times (huge memory spike) or crash on Windows.
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host="127.0.0.1", debug=debug, port=5000, use_reloader=False)
