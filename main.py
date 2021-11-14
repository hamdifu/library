from flask import Flask, render_template, redirect, url_for, flash, g, abort,request
from flask_bootstrap import Bootstrap
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
import requests
from functools import wraps
from flask_gravatar import Gravatar
from smtplib import SMTP
from forms import RegisterForm,LoginForm,SearchForm
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = '123456789'
Bootstrap(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL1','sqlite:///library.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function

#DataBase
#Books
class Book(db.Model):
    __tablename__ = "book"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    author = db.Column(db.String(250),nullable=False)
    issue_dt = db.Column(db.String(250),nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    ebook = db.Column(db.String(250))
    audio_book = db.Column(db.String(250))
    video_book = db.Column(db.String(250))
    month=db.Column(db.Integer)
    # title_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'))

#User
class User(UserMixin,db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(30),nullable= False)
    email = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(100),nullable=False,unique=True)
    books = db.Column(db.Integer,db.ForeignKey('book.id'))
    books = db.relationship('Book')



db.create_all()

API_KEY = 'AIzaSyBgu-qILtDAjWJN532D2AeeHy43j8IYj-k'


@app.route('/', methods=['GET', 'POST'])
def home():
    if current_user.is_authenticated:
        form = SearchForm()
        if request.method == 'POST':
            return redirect(url_for('search',title=form.title.data))
        return render_template('index.html',form=form)
    return render_template("website.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash("Email already exists! Try logging in instead.")
            return redirect(url_for('login'))
        new_user = User(
            email=form.email.data,
            password=generate_password_hash(form.password.data, method='pbkdf2:sha256',salt_length=8),
            name=form.name.data
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('home'))

    return render_template("register.html", form=form, logged_in=current_user.is_authenticated)

@app.route('/login',methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        email = form.email.data
        print(email)
        user = User.query.filter_by(email=email).first()
        if not user:
            print('Email does not exist, try again!!')
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, form.password.data):
            print("Incorrect password! Try again!!")
            return redirect(url_for('login'))
        login_user(user)
        return redirect(url_for('home'))
    return render_template("login.html", form=form,logged_in=current_user.is_authenticated)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/search/<title>',methods=['GET', 'POST'])
def search(title):
    url = 'https://www.googleapis.com/books/v1/volumes?q='+title
    response = requests.get(url)
    data = response.json()['items'][:5]
    color_list = ['#e9c46ab3','#023e7db3','#e63946b3','#56cfe1b3','#9d0208b3','#003566b3']


    return render_template('books.html',books=data,name=title.title(),colors=color_list)

@app.route('/checkout/<data>',methods=['GET', 'POST'])
def checkout(data):
    if Book.query.filter_by(data['id']):
        pass
    else:
        new_book = Book(
            id=data['id'],
            title=data['volumeInfo']['title'],
            author=data['volumeInfo']['authors'],
            issue_dt=None,
            img_url=data['volumeInfo']['imageLinks']['thumbnail'],
            ebook=data['volumeInfo']['previewLink'],
            user=current_user,
            month=0
        )

    return render_template('checkout.html', book=new_book)



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
