from flask import Flask, render_template, request, redirect, url_for, flash, session
from sqlmodel import SQLModel, Field, Relationship, Session, create_engine, select,func
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import date
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = "Aryan@0606"

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(
    DATABASE_URL,
    echo=True,
    connect_args={
        "ssl_disabled": False
    }
)



class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    username: str
    email: str
    password: str
    gender: str

class Feedback(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    message: str

class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    expenses: List["Expense"] = Relationship(back_populates="category")

class Expense(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    amount: float
    description: Optional[str]
    username: str
    category_id: int = Field(foreign_key="category.id")
    category: Optional[Category] = Relationship(back_populates="expenses")
    expense_date: date = Field(default_factory=date.today)

@app.route('/')
def home():
    return render_template("homepage.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        with Session(engine) as db_session:
            user = db_session.exec(select(User).where(User.email == email)).first()
            if user and user.password == password:
                session["username"] = user.username
                flash("Login successful! ✅", "success")
                return redirect('/ethome')
            else:
                flash("Invalid credentials.", "danger")
    return render_template("login.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            name = request.form["name"]
            username = request.form["username"]
            email = request.form['email']
            password = request.form['password']
            confirm = request.form['confirm']
            gender = request.form["gender"]

            if password != confirm:
                flash("Passwords do not match ❌.", "warning")
            else:
                with Session(engine) as db_session:
                    user = User(
                        name=name,
                        username=username,
                        email=email,
                        password=password,
                        gender=gender
                    )
                    db_session.add(user)
                    db_session.commit()
                    flash("Registration successful! ✅", "success")
                    return redirect('/login')
        except Exception as e:
            flash(f"An error occurred: {e}", "danger")
    return render_template("reg.html")

@app.route('/feedback', methods=['POST'])
def feedback():
    with Session(engine) as db_session:
        message = request.form['feedback']
        fb = Feedback(message=message)
        try:
            db_session.add(fb)
            db_session.commit()
            flash("Thanks for your feedback!", "success")
        except Exception as e:
            db_session.rollback()
            flash(f"Error saving feedback: {e}", "danger")
    return redirect('/')          
            
@app.route('/ethome', methods=['GET', 'POST'])
def ethome():
    username = session.get("username")
    if not username:
        flash("Please log in to view your expenses.", "warning")
        return redirect('/login')
    if request.method == "POST":
        expid = request.form.get("expid")
        if expid:
            with Session(engine) as db:
                delquery = db.exec(
                select(Expense).where(Expense.id == int(expid),Expense.username == username)).first()
                if delquery:
                    db.delete(delquery)
                    db.commit()
                    flash("Expense deleted successfully ✅", "success")
                else:
                    flash("Expense not found or unauthorized ❌", "danger")
                
    with Session(engine) as db:
        expenses = db.exec(
            select(Expense).where(Expense.username == username).options(selectinload(Expense.category))
        ).all()
             
        total = sum(exp.amount for exp in expenses)
            
    return render_template("ethome.html", expenses=expenses, total=total)

def searchexp(filters):
    username = session.get("username")
    with Session(engine) as db:
        query = select(Expense).where(Expense.username == username).options(selectinload(Expense.category))

        if filters.get("category_id"):
            query = query.where(Expense.category_id == filters["category_id"])

        if filters.get("start_date"):
            query = query.where(Expense.expense_date >= filters["start_date"])

        if filters.get("end_date"):
            query = query.where(Expense.expense_date <= filters["end_date"])

        if filters.get("minamt"):
            query = query.where(Expense.amount >= filters["minamt"])

        if filters.get("maxamt"):
            query = query.where(Expense.amount <= filters["maxamt"])

        return db.exec(query).all()
    

@app.route('/search', methods=['GET', 'POST'])
def search():
    results=[]
    if request.method == "POST":
        filter1=request.form.get("filter")
        filters={}
        
        if filter1 == "category_id":
            category_id = request.form.get("category_id")
            if category_id:
                filters["category_id"] = int(category_id)

        elif filter1 == "amount":
            minamt = request.form.get("minamt")
            maxamt = request.form.get("maxamt")
            if minamt:
                filters["minamt"] = float(minamt)
            if maxamt:
                filters["maxamt"] = float(maxamt)

        elif filter1 == "date":
            start_date = request.form.get("start_date")
            end_date = request.form.get("end_date")
            if start_date:
                filters["start_date"] = start_date
            if end_date:
                filters["end_date"] = end_date
        
        
        
        if filters:
            results = searchexp(filters)
        else:
            results = []
        
    return render_template("search.html", expenses=results)
        

@app.route('/addexpense', methods=['GET', 'POST'])
def addexpense():
    if request.method == "POST":
        try:
            username = session.get("username")
            if not username:
                flash("You must be logged in to add an expense.", "warning")
                return redirect('/login')
            
            amount = float(request.form["amount"])
            category_id = int(request.form["category_id"])
            description = request.form["description"]
            date_str = request.form["date"]
            expense_date = date.fromisoformat(request.form["date"])

            with Session(engine) as db_session:
                new_expense = Expense(
                    amount=amount,
                    category_id=category_id,
                    description=description,
                    username=username,
                    expense_date=expense_date
                )
                db_session.add(new_expense)
                db_session.commit()
                flash("Expense added successfully!", "success")
                return redirect('/addexpense')
        except Exception as e:
            flash(f"An error occurred: {e}", "danger")
    return render_template("addexpense.html")

def create_tables():
    SQLModel.metadata.create_all(engine)

def seed_categories():
    categories = ["Food", "Travel", "Subscription", "Shopping", "Other"]
    with Session(engine) as session:
        existing = session.exec(select(Category)).all()
        if not existing:
            for name in categories:
                session.add(Category(name=name))
            session.commit()

create_tables()
seed_categories()

if __name__ == '__main__':
    app.run(debug=True)
