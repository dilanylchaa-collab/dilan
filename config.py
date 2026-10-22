class Config:
    SQLALCHEMY_DATABASE_URI = 'postgresql+pg8000://postgres:123456@localhost:5432/delivery_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'delivery2025'

    MAIL_SERVER         = 'smtp.gmail.com'
    MAIL_PORT           = 587
    MAIL_USE_TLS        = True
    MAIL_USERNAME       = 'yeferson1ylchanalema@gmail.com'
    MAIL_PASSWORD       = 'ssgtexyv lvkxislk'
    MAIL_DEFAULT_SENDER = 'yeferson1ylchanalema@gmail.com'
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE   = False
    SQLALCHEMY_ENGINE_OPTIONS = {}