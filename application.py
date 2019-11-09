import os

from flask import Flask, jsonify,session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import Flask, render_template, request, session, redirect, url_for
from models import *

import logging  
_logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
user = None
Session(app)

@app.route("/", methods=['GET'])
def index():
    user = User()
    if session.get("user") is None:
        return redirect(url_for('login'))
    elif session.get("user"):
        return redirect(url_for('home'))
    
    lights = db.execute("SELECT now()").fetchone()
    # return "Project 1: TODO, time : "+str(lights[0])
    return render_template("login.html")

@app.route("/login", methods=['GET','POST'])
def login():    
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        if session.get("user") is None:
            session["user"] = User()
        try:
            user = session.get("user")
            user.login(username=username,password=password)
            
            session["user"] = user 
        except AttributeError:
            user = User()
            
        if user.connectionState == "connected":
            user.username = username
            user.password = password

            print(f"======== user : {user} connectionState : {user.connectionState}, username : {user.username}, password : {user.password}")
            return redirect(url_for('home')) #, message={"value":f"Welcome {user.username}","type":"primary"})
        else:
            return render_template("login.html", message={"value":"Please make sure the username and/or password are correct.","type":"danger"})
        
    return render_template("login.html")

@app.route("/register", methods=['GET','POST'])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")
        admin = request.form.get("admin")
        
        if admin == "admin":
            is_admin = True
        else:
            is_admin = False
            
        user = User()
        emailExist = user.emailExist(email)
        if emailExist:
            return render_template("registration.html", message={"value":f"A user with {email} is already registered! Please use a different email.","type":"danger"})
        user.createUser(username,password,email,is_admin)
        user.username =  username
        print(f"In registration = username : {user.username}, password : {user.password}, email : {user.email}, admin : {admin}")
        
        session['user'] = user.getInfos()
        return redirect(url_for('home')) # ,user=user, message={"value":f"Welcome {user.username}","type":"success"})
    return render_template("registration.html")

@app.route("/logout", methods=['GET','POST'])
def logout():
    User().logout()
    return redirect(url_for('login'))

@app.route("/home", methods=['GET','POST'])
def home():    
    if request.method == "POST":
        query = request.form.get("query")
        print(f"\n==== query {query}")
        if request.form.get("query") != None:
            q = request.form.get("query")
            result = User().search_books(query)
            
            return render_template("home.html",active_home="active",query=query,
                                    isbn_books=result['isbn']['data'],isbn_number=result['isbn']['number'],
                                    title_books=result['title']['data'],title_number=result['title']['number'],
                                    author_books=result['author']['data'],author_number=result['author']['number'])
    if (session.get("connectionState") is None) and (session.get("connectionState") == "disconnected"):
        return redirect(url_for('login'))
            
    user = session.get("user")
    try:
        user = user.getInfos()
    except AttributeError:
        pass
    query = request.form.get("query")
    print(f" query {query} ========= In home User {user}")
    try:
        username = user["username"]
    except TypeError:
        pass
    
    if user["connectionState"]:
        if user["connectionState"] == "connected":
            q = request.form.get("q")
            return render_template("home.html",active_home="active", message={"value":f"Welcome {user['username']}","type":"primary"})
        elif user["connectionState"] == "disconnected":
            return render_template("login.html")
        
    return render_template("home.html", active_home="active",user=user, message={"value":f"Welcome {username}","type":"secondary"})

@app.route("/home/<int:book_id>", methods=['GET','POST'])
def book_details(book_id):
    user = None    
    # Make sure user has logged in.
    try:
        user = session["user"]
    except KeyError:
        return redirect(url_for('login'))
    if user:
        if request.method == "POST":
            rating = request.form.get("rating")
            text = request.form.get("text")
            book_id = request.form.get("book_id")
            try:
                user_id = user['id']
            except TypeError:
                user = user.getInfos()
                user_id = user['id']
            
            book = User().get_book_by_book_id(book_id)
            reviews = Reviews().get_reviews_by_book(book_id)
            
            check_user_already_reviewed = Reviews().check_user_already_reviewed(user_id)
            if check_user_already_reviewed:
                return render_template("book_details.html", book=book,reviews=reviews,message={"value":f"Sorry you cannot review a book twice.","type":"danger"})
            else:
                review = Reviews().createReviews(user_id,book_id,rating,text)
                reviews = Reviews().get_reviews_by_book(book_id)
                return render_template("book_details.html", book=book,reviews=reviews,message={"value":f"Added your review.","type":"success"})

        print(f"{user}")
        book = User().get_book_by_book_id(book_id)
        reviews = Reviews().get_reviews_by_book(book_id)
        avg_book_review = Reviews().avg_book_review()
        result_api = Reviews().get_review_counts(book.isbn)
        print(f"**** reviews : {reviews}, avg_book_review : {avg_book_review}, review_counts : {result_api}")
        # work_ratings_count=result['work_ratings_count'],average_rating=result['average_rating']
        return render_template("book_details.html",result_api=result_api,book=book,reviews=reviews,avg_book_review=avg_book_review)
    else:
        return redirect(url_for('login'))

@app.route("/api/<string:isbn>",methods=['GET'])
def get_book_by_isbn_api(isbn):    
    # Make sure book exists.
    book = User().search_books_by_isbn(isbn)
    if book is None or book == []:
        return jsonify({"error": "Invalid isbn"}), 422
    
    review_count = Reviews().count_reviews_by_isbn(isbn)
    average_score = Reviews().avg_book_review()
    try:
        value_review_count = review_count[0][0]
    except Exception:
        value_review_count = 0
    print(f"review_count {review_count},average_score : {average_score} ")
    return jsonify({
        "title": book[0][2],
        "author": book[0][3],
        "year": book[0][4],
        "isbn": book[0][1],
        "review_count": value_review_count,
        "average_score": float(average_score)
    })