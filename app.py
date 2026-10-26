from flask import Flask
from sqlalchemy import text
from config import Config
from models import db
from extensions import mail, login_manager

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    from models import Usuario

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    from routes import main
    app.register_blueprint(main)

    return app

app = create_app()

with app.app_context():
    try:
        from models import db
        db.create_all()
        db.session.execute(text("ALTER TABLE repartidores ADD COLUMN IF NOT EXISTS aprobado BOOLEAN DEFAULT TRUE"))
        db.session.execute(text("ALTER TABLE repartidores ALTER COLUMN aprobado SET DEFAULT FALSE"))
        db.session.commit()
        print("✅ Tablas creadas correctamente")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)