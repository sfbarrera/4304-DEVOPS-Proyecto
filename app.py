from flask import Flask
from flask_jwt_extended import JWTManager
from extensions import db, ma
from routes.blacklist_routes import blacklist_bp, VERSION
import os

def create_app():
    app = Flask(__name__)

    # ── Database configuration ──────────────────────────────────────────────
    DATABASE_URL = os.environ.get(
        "DATABASE_URL",
        "sqlite:///blacklist.db"          # SQLite fallback for local dev
    )
    # AWS RDS URLs sometimes use postgres:// — SQLAlchemy requires postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    # RDS: fail fast if unreachable (avoids Gunicorn worker timeout during import).
    if DATABASE_URL.startswith("postgresql"):
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_pre_ping": True,
            "connect_args": {"connect_timeout": 10},
        }

    # ── JWT configuration ───────────────────────────────────────────────────
    # Static token for simplicity (as allowed by the spec).
    # Override with JWT_SECRET_KEY env-var in production.
    app.config["JWT_SECRET_KEY"] = os.environ.get(
        "JWT_SECRET_KEY", "super-secret-static-key-change-in-prod"
    )

    # ── Init extensions ─────────────────────────────────────────────────────
    db.init_app(app)
    ma.init_app(app)
    JWTManager(app)

    # ── Register blueprints ──────────────────────────────────────────────────
    app.register_blueprint(blacklist_bp)

    # ── Health-check endpoint (required by Beanstalk) ────────────────────────
    @app.route("/health", methods=["GET"])
    def health():
        return {"status": "healthy", "version": VERSION}, 200

    # ── Create tables ────────────────────────────────────────────────────────
    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
