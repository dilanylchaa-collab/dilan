import os


def _db_url():
    url = os.environ.get('DATABASE_URL')
    if not url:
        return 'postgresql+pg8000://postgres:123456@localhost:5432/delivery_db'
    url = url.replace('postgres://', 'postgresql://', 1)
    return url.replace('postgresql://', 'postgresql+pg8000://', 1)


class Config:
    SQLALCHEMY_DATABASE_URI = _db_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-local-key')

    MAIL_SERVER         = 'smtp.gmail.com'
    MAIL_PORT           = 587
    MAIL_USE_TLS        = True
    MAIL_USERNAME       = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD       = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME')

    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE   = False
    SQLALCHEMY_ENGINE_OPTIONS = {}
