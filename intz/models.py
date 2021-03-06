from intz import db, app
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired
from flask_login import current_user
import uuid


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column('id', db.Text(length=36), default=lambda: str(uuid.uuid4()), primary_key=True)
    username = db.Column(db.String(32), index = True, unique=True)
    email = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(128))
    integers = db.relationship('Integer', backref='user', lazy='dynamic')
    authenticated = db.Column(db.Boolean, default=False)
    api_key = db.Column(db.String(310))

    def __init__(self, username=None, email=None, password=None, integers=[]):
        self.username = username
        self.email = email
        self.set_password(password)
        self.integers = integers

    def is_authenticated(self):
        return self.authenticated

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def set_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password_or_token):
        return pwd_context.verify(password_or_token, self.password_hash)

    # TODO: Enable ability for user to get fresh token without having to change password
    # TODO: Allow user to set an expiration
    def get_auth_token(self, expiration = 600):
        s = Serializer(app.config['SECRET_KEY']) #, expiration=expiration)
        return s.dumps({
            'id': str(self.id),
            'password_hash': self.password_hash
        })

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])

        try:
            data = s.loads(token)
        except SignatureExpired:
            return None  # Valid token, but expired
        except BadSignature:
            return None  # Invalid token

        return User.query.get(data['user_id'])

    def json(self):
        return {
            'id': self.id,
            'username': self.username,
            'integers': self.integers
        }


class Integer(db.Model):
    __tablename__ = 'integer'
    id = db.Column('id', db.Text(length=36), default=lambda: str(uuid.uuid4()), primary_key=True)
    label = db.Column(db.String, unique=False)
    value = db.Column(db.Integer, unique=False)
    user_id = db.Column(db.Text(length=36), db.ForeignKey('user.id'), default=lambda: str(uuid.uuid4()))

    def __init__(self, value=None, label=None, user_id=None):
        self.label = label
        self.value = value
        if user_id is None:
            self.user_id = current_user.id
        else:
            self.user_id = user_id

    def __repr__(self):
        return 'value: %d' % self.value

    def json(self):
        return {
            'id': self.id,
            'label': self.label,
            'value': self.value
        }
