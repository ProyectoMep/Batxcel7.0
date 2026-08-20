"""Entry point. Registra los controllers (Blueprints)."""
from flask import Flask, render_template


def create_app() -> Flask:
    app = Flask(__name__, template_folder="views/templates",
               static_folder="views/static")

    from controllers.metrica_controller import metrica_bp
    from controllers.entidad_controller import entidad_bp
    from controllers.reporte_controller import reporte_bp
    from controllers.presentacion_controller import presentacion_bp
    from controllers.acta_controller import acta_bp
    from controllers.prospera_controller import prospera_bp
    app.register_blueprint(metrica_bp)
    app.register_blueprint(entidad_bp)
    app.register_blueprint(reporte_bp)
    app.register_blueprint(presentacion_bp)
    app.register_blueprint(acta_bp)
    app.register_blueprint(prospera_bp)

    @app.route("/")
    def index():
        return render_template("index.html")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=8081, debug=True, use_reloader=False)