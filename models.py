import os

from flask import Flask, session, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import requests, json

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DEV_SQLALCHEMY_DATABASE_URI"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
# conString = "postgres://gregory:Goufan2017@localhost:5432/postgres"
Session(app)


import logging  
_logger = logging.getLogger(__name__)

# Set up database
engine = create_engine('postgresql://openpg:openpgpwd@localhost:5432/project1_db')
db = scoped_session(sessionmaker(bind=engine))
class Reviews:
    def __init__(self):
        super(Reviews, self).__init__()
        self.id = None
        self.user_id = None
        self.book_id = None
        self.rating = None
        self.text = None
        """CREATE TYPE rating;
            
            CREATE DOMAIN rating AS integer ;
            CHECK ( VALUE IN (1,2, 3, 4,5) );

            CREATE TABLE reviews (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users not null, 
                book_id INTEGER REFERENCES books not null,
                rating rating default 1,
                text varchar);""" 
    
    def createReviews(self,user_id,book_id,rating,text):
        _logger.info(f"In createReviews = user_id : {user_id}, book_id : {book_id}, rating : {rating}, text :{text}")
        result = db.execute("INSERT INTO reviews (user_id,book_id,rating,text) VALUES (:user_id, :book_id, :rating, :text ) RETURNING *",
            {"user_id":user_id,"book_id":book_id,"rating":rating,"text":text})
        review = result.fetchone()
        print(f"Added reviews with review.id : {review} {review.id}, book_id : {book_id}, rating : {rating}, text: {text}.")
        
        try:
            db.commit()        
            self.id = review.id
            self.review_id = review.review_id
            self.book_id = review.book_id
            self.rating = review.rating
            self.text = review.text
        
            if len(review) == 1:
                self.id = review.id
                self.review_id = review.review_id
                self.book_id = review.book_id
                self.rating = review.rating
                self.text = review.text
            return True
            
        except Exception:
            return False 
    
    def check_user_already_reviewed(self,user_id):
        query = db.execute("SELECT count(*) as user_reviews_number FROM reviews where user_id = :user_id;",
                        {"user_id":user_id}).fetchone()
        result = True
        if query.user_reviews_number == 0:
            result = False
        else:
            result = True
        return result
    
    def get_reviews_by_book(self,book_id):
        result = db.execute("SELECT id, user_id, book_id, rating, text FROM reviews WHERE book_id = :book_id;",
                        {"book_id":book_id}).fetchall()
        return result 
    
    # def get_reviews_by_isbn(self,isbn):
    #     result = db.execute("SELECT id, user_id, book_id, rating, text FROM reviews WHERE isbn = :isbn;",
    #                     {"isbn":isbn}).fetchall()
    #     return result 
           
    def count_reviews_by_isbn(self,isbn):
        result = db.execute("COMMIT; SELECT COUNT(*) FROM reviews as r JOIN books as b ON b.id = r.book_id  WHERE b.isbn = :isbn;",
                        {"isbn":isbn}).fetchall()
        return result 
    def avg_book_review(self):
        query = db.execute("BEGIN; SELECT ROUND(AVG(rating) ,1) AS \"avg_rating\" FROM reviews COMMIT;").fetchone()
        return query.avg_rating
    
    def get_review_counts(self,isbn):
        params = {}
        print(f"isbn {isbn}")
        params = {'format': 'json','isbn': str(isbn),'key': 'pVlnCL2f468Dv7WrqNZw'}
        try:
            response = requests.get('https://www.goodreads.com/book/review_counts.json?isbns=034541005X&key=pVlnCL2f468Dv7WrqNZw')
            json_data = json.loads(response.text)
            print(f"json_data : {json_data}")
            return json_data['books'][0]
    
        except Exception as e:
            print(f"An error happened {e}")
class Book:
    def get_book_by_isbn(isbn):
        print(f"isbn {isbn}")
        
        result = db.execute("SELECT id, user_id, book_id, rating, text FROM reviews WHERE book_id = :book_id;",
                        {"book_id":book_id}).fetchall()
        return result 
        
class User:
    """docstring for User."""
    def __init__(self):
        super(User, self).__init__()
        self.id = None
        self.username = None
        self.password = None
        self.email = None
        self.is_admin = None
        self.connectionState =None
        
        if session.get("connectionState") is None:
            session["connectionState"] = ""
            
        # if session.get("user") is None:
        #     session["user"] = []
            
        self.connectionState = session.get("connectionState")
        
        """CREATE TABLE IF NOT EXISTS users (\
                        id SERIAL PRIMARY KEY,\
                        username VARCHAR NOT NULL,\
                        password VARCHAR NOT NULL);"""   
    def login(self,username,password):
        user = db.execute("SELECT * FROM users WHERE username = :username AND password = :password",
                        {"username":username,"password":password}).fetchone()     
        self.connectionState = "disconnected"
        session["connectionState"] = "disconnected"
        
        if user != None:
            self.id = user.id
            self.username = user.username
            self.password = user.password
            self.email = user.email
            self.is_admin = user.is_admin
            session["connectionState"] = "connected"
            self.connectionState = session.get("connectionState")
    
    def logout(self):
        self.connectionState = "disconnected"
        session["connectionState"] = "disconnected"
        session["user"] = None
        
    def getInfos(self):
        user = {
            "id" : self.id,
            "username" : self.username,
            "password" : self.password,
            "email" : self.email,
            "is_admin" : self.is_admin,
            "connectionState" : session.get("connectionState")    
        }
        return user
    
    def createUser(self,username,password,email,is_admin):
        _logger.info(f"In createUser = username : {username}, password : {password}")
        result = db.execute("INSERT INTO users (username,password,email,is_admin) VALUES (:username, :password, :email, :is_admin) RETURNING *",
            {"username":username,"password":password,"email":email,"is_admin":is_admin})
        user = result.fetchone()
        print(f"Added users with username : {user} {username}, password : {password}, email : {email}, is_admin : {is_admin}.")
        
        try:
            db.commit()        
            self.id = user.id
            self.username = user.username
            self.password = user.password
            self.email = user.email
            self.is_admin = user.is_admin
            session["connectionState"] = "connected"
            self.connectionState = session.get("connectionState")
        
            if len(user) == 1:
                self.id = user.id
                self.username = user.username
                self.password = user.password
                self.email = user.email
                self.is_admin = user.is_admin
                session["connectionState"] = "connected"
                self.connectionState = session.get("connectionState")
            return True
            
        except Exception:
            return False  

    def emailExist(self,email):
        print(f" In email: {email}")
        result = db.execute("SELECT COUNT(*) as email_number FROM ( SELECT * FROM users WHERE email=:email ) a",
                        {"email":email}).fetchone()
        print(f"=== In email result: {result.email_number} {result}")
        if result.email_number:
            if result.email_number >= 1:
                return True
        else:
            return False
    
    def search_books(self,q):
        isbn_result = self.search_books_by_isbn(q)
        title_result = self.search_books_by_title(q)
        author_result = self.search_books_by_author(q)
        
        self.isbn_result = isbn_result
        self.title_result = title_result
        self.author_result = author_result
        
        nbr_isbn = 0; nbr_title = 0; nbr_author = 0
        
        if title_result: nbr_title = len(title_result)
        if author_result: nbr_author = len(author_result)
        if isbn_result: nbr_isbn = len(isbn_result)
        result = {
            "isbn":{"data":isbn_result,"number":nbr_isbn},
            "title":{"data":title_result,"number":nbr_title},
            "author":{"data":author_result,"number":nbr_author}
        }
        return result
        
    def search_books_by_isbn(self,isbn):
        isbn = f"%{isbn}%"
        result = db.execute("SELECT id, isbn, title, author,year FROM books WHERE isbn LIKE :isbn;",
                        {"isbn":isbn}).fetchall()
        return result
    
    def search_books_by_title(self,title):
        title = f"%{title}%"
        result = db.execute("SELECT * FROM books WHERE title LIKE :title;",
                        {"title":title}).fetchall()
        return result
    
    def search_books_by_author(self,author):
        author = f"%{author}%"
        result = db.execute("SELECT * FROM books WHERE author LIKE :author;",
                        {"author":author}).fetchall()
        return result
        
    def get_book_by_book_id(self,book_id):
        result = db.execute("SELECT * FROM books WHERE id = :book_id;",
                        {"book_id":book_id}).fetchone()
        return result    
@app.route("/")
def index():
    lights = db.execute("SELECT now()").fetchone()
    return "Project 1: TODO, time : "+str(lights[0])
