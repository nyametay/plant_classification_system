from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    username = db.Column(db.String(50), primary_key=True, unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), unique=True, nullable=False)  # Store plain text password
    images = db.relationship('Plant', backref='user', lazy=True)

class Plant(db.Model):
    __tablename__ = 'plants'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    filename = db.Column(db.String(255), nullable=False)
    image_data = db.Column(db.LargeBinary, nullable=False)
    plant_info = db.Column(db.JSON, nullable=False)
    plant_uses = db.Column(db.JSON, nullable=False)
    username = db.Column(db.String(50), db.ForeignKey('users.username'), nullable=False)

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    comment = db.Column(db.Text, nullable=False)
    rate = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String(50), db.ForeignKey('users.username'), nullable=True)

# Helper functions to check existence
def email_exists(email):
    return db.session.query(db.exists().where(User.email == email)).scalar()

def username_exists(username):
    return db.session.query(db.exists().where(User.username == username)).scalar()

def password_exists(password):
    return db.session.query(db.exists().where(User.password == password)).scalar()

# Helper function to get the count of a username
def username_count(username):
    return db.session.query(User).filter_by(username=username).count()

def email_count(email):
    return db.session.query(User).filter_by(email=email).count()

def password_count(password):
    return db.session.query(User).filter_by(password=password).count()

def get_user(username):
    return db.session.query(User).filter_by(username=username).first()

def get_plants(username):
    return db.session.query(Plant).filter_by(username=username).all()

def get_reviews():
    reviews = db.session.query(Comment).all()
    comments = []
    print(reviews)
    for review in reviews:
        user = get_user(review.username)
        if user:
            name = user.name
        else:
            name = 'Deleted User'
        comments.append({
            'id': review.id,
            'username': review.username,
            'rate': review.rate,
            'comment': review.comment,
            'name': name
        })
    return comments
    
def plants_saved_count(username):
    return db.session.query(Plant).filter_by(username=username).count()