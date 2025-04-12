from flask import Flask, render_template, request, redirect, url_for, flash, session
from sqlmodel import SQLModel, Field, Relationship, Session, create_engine, select
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import date

app = Flask(__name__)
app.secret_key = "Aryan@0606"

DATABASE_URL = "mysql+mysqlconnector://aryan:Aryan%400606@localhost/expensetracker"
engine = create_engine(DATABASE_URL, echo=True)

# Models
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

# Routes
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

@app.route('/ethome')
def ethome():
    with Session(engine) as db:
        expenses = db.exec(select(Expense).options(selectinload(Expense.category))).all()
    return render_template("ethome.html", expenses=expenses)

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

            with Session(engine) as db_session:
                new_expense = Expense(
                    amount=amount,
                    category_id=category_id,
                    description=description,
                    username=username
                )
                db_session.add(new_expense)
                db_session.commit()
                flash("Expense added successfully!", "success")
                return redirect('/addexpense')
        except Exception as e:
            flash(f"An error occurred: {e}", "danger")
    return render_template("addexpense.html")

# Database setup
def create_tables():
    SQLModel.metadata.create_all(engine)

def seed_categories():
    categories = ["Food", "Transport", "Subscription", "Shopping", "Other"]
    with Session(engine) as session:
        existing = session.exec(select(Category)).all()
        if not existing:
            for name in categories:
                session.add(Category(name=name))
            session.commit()

if __name__ == '__main__':
    create_tables()
    seed_categories()
    app.run(debug=True)
