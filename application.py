import psycopg2
import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp
from helpers import *

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# custom filter
app.jinja_env.filters["usd"] = usd

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL(os.environ.get("DATABASE_URL") or "sqlite:///finance.db")
@app.route("/")
@login_required
def index():
    row =db.execute("SELECT * from users WHERE id=:id" ,id=session['user_id'] )
    user= row[0]['username']
    CASH= row[0]['cash']
    rows=db.execute("SELECT * from portfolio WHERE username=:username" , username=user)
    if rows:
        SYMBOL= []
        USERNAME=[]
        SHARES=[]
        PRICE_Amount=[]
        TOTAL_Amount=[]
        t=0
        for row in rows:
            SYMBOL.append(row['symbol'])
            SHARES.append(row['shares'])
            LOOK=lookup(row['symbol'])
            USERNAME.append(lookup(row['symbol'])['name'])
            price = lookup(row['symbol'])['price']
            PRICE_Amount.append(usd(price))
            TOTAL_Amount.append(usd(price * row['shares']))
            t = t + (price * row['shares'])
        Total = t + CASH
        Length = len(SYMBOL)
        return render_template("index.html",CASH=CASH, SYMBOL=SYMBOL, USERNAME=USERNAME, SHARES=SHARES, PRICE_Amount=PRICE_Amount, TOTAL_Amount=TOTAL_Amount, Total=Total, Length=Length)
    return render_template("index.html" , CASH=CASH, Total=CASH, SYMBOL=[], USERNAME=[], PRICE_Amount=[], TOTAL_Amount=[], Length=0)     
        

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "POST":
        if not request.form.get('shares'):
            return apology("no shares")
        input = int(request.form.get("shares"))
        if input < 1:
            return apology("requires a positive number of shares")
        if not request.form.get("symbol"):
                return apology("You left the page blank")
        symbol = request.form.get("symbol")     
        quote=lookup(symbol)
        row = db.execute("select cash from users WHERE id = 1")
        cash = row[0]['cash']
        price = quote['price']
        id = session['user_id']
        shares = int(request.form.get("shares"))
        if cash < (shares * price):
            return apology("not enough money")
        cash1 = cash - (shares * price)
        db.execute("UPDATE users SET cash=:cash WHERE id=:id", cash=cash1, id=session['user_id'])
        username = (db.execute("select * from users WHERE id=:id", id=id))[0]['username']
        result= db.execute("select * from portfolio WHERE symbol=:symbol AND username=:username",symbol=symbol, username=username)
        if not result:
            db.execute("insert into portfolio (username,symbol,shares) values (:username,:symbol,:shares)", username=username, symbol=symbol, shares=shares)
        else:
            old_shares = result[0]['shares']
            new_shares = old_shares + shares
            db.execute ("update portfolio set shares=:share WHERE symbol=:symbol and username=:username" , share=new_shares, username=username, symbol=symbol)
        return redirect(url_for("index"))
    else:
        return render_template("buy.html")

@app.route("/history")
@login_required
def history():
    """Show history of transactions."""
    return apology("TODO")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            return apology("invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))

@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method == "POST":
        print("foo")
        quote = lookup("GOOG")
        return render_template("quoted.html", quote=quote)
    else:
        return render_template("quote.html")
    """Get stock quote."""

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":



        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")
    
        
        elif  request.form.get("password") != request.form.get("re-enter password"):
            return apology("password don't match")
        password = request.form.get("password")
        db.execute("INSERT INTO \"users\" (username, hash, cash) VALUES (:username, :hash, 10000)", username=request.form.get("username") , hash=pwd_context.hash(password)) 
        
        
        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            return apology("invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect(url_for("index"))


    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

    """Register user."""
    return apology("TODO")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    if request.method == "POST":
        if not request.form.get('shares'):
            return apology("no shares")
        input = int(request.form.get("shares"))
        if input < 1:
            return apology("requires a positive number of shares")
        if not request.form.get("symbol"):
                return apology("You left the page blank")
        symbol = request.form.get("symbol")     
        quote=lookup(symbol)
        row = db.execute("select cash from users WHERE id = 1")
        cash = row[0]['cash']
        price = quote['price']
        id = session['user_id']
        shares = int(request.form.get("shares"))
        username = (db.execute("select * from users WHERE id=:id", id=id))[0]['username']
        result= db.execute("select * from portfolio WHERE symbol=:symbol AND username=:username",symbol=symbol, username=username)
        if not result:
            db.execute("insert into portfolio (username,symbol,shares) values (:username,:symbol,:shares)", username=username, symbol=symbol, shares=shares)
        else:
            old_shares = result[0]['shares']
            new_shares = old_shares + shares
            db.execute ("update portfolio set shares=:share WHERE symbol=:symbol and username=:username" , share=new_shares, username=username, symbol=symbol)
            return redirect(url_for("index"))
    else:
        return render_template("sell.html")
    """Sell shares of stock."""
   
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)