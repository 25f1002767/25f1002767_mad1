from flask import Flask, render_template, request, redirect , session 
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User, StaffProfile
app = Flask(__name__)
app.secret_key = "trekking_secret_key"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///trekking.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

    admin = User.query.filter_by(email="admin@trek.com").first()

    if not admin:

        admin = User(
            username="admin",
            email="admin@trek.com",
            password=generate_password_hash("admin123"),
            role="admin"
        )

        db.session.add(admin)
        db.session.commit()

        print("Admin account created.")


# -------------------------------
# Home Route
# -------------------------------
# If someone visits:
# http://127.0.0.1:5000/
# they will automatically go to
# http://127.0.0.1:5000/register
@app.route("/")
def home():
    return redirect("/register")


# -------------------------------
# Registration Route
# -------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        # Receive form data
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]
        contact_number = request.form["contact_number"]
        experience_years = request.form["experience_years"]

        # Check duplicate email
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            return "Email already exists."

        # Hash password
        hashed_password = generate_password_hash(password)

        # Create user
        user = User(
            username=username,
            email=email,
            password=hashed_password,
            role=role
        )

        # Save user
        db.session.add(user)
        db.session.commit()

        # Create staff profile if role is staff
        if role == "staff":

            staff = StaffProfile(
                user_id=user.id,
                contact_number=contact_number,
                experience_years=int(experience_years)
                if experience_years else None,
                approval_status="pending"
            )

            db.session.add(staff)
            db.session.commit()

            return "Registration successful. Waiting for admin approval."

        return "Registration successful."

    # GET request
    return render_template("register.html")
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if not user:
            return "Invalid Email"

        if not check_password_hash(user.password, password):
            return "Invalid Password"
        session["user_id"] = user.id
        session["role"] = user.role

        if user.role == "admin":
            return redirect("/admin")

        elif user.role == "staff":

            if user.staff_profile.approval_status != "approved":
                return "Your account is waiting for admin approval."

            return redirect("/staff")

        else:
            return redirect("/user")

    return render_template("login.html")
@app.route("/admin")
def admin_dashboard():
    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"
    pending_staff = StaffProfile.query.filter_by(
        approval_status="pending"
    ).all()

    return render_template(
        "pending_staff.html",
        pending_staff=pending_staff
    )
    return "Welcome Admin Dashboard"


@app.route("/staff")
def staff_dashboard():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "staff":
        return "Access Denied"

    return "Welcome Staff Dashboard"
@app.route("/approve/<int:staff_id>")
def approve_staff(staff_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    staff = db.session.get(StaffProfile, staff_id)

    if not staff:
        return "Staff not found"

    staff.approval_status = "approved"

    db.session.commit()

    return redirect("/admin/pending-staff")



@app.route("/user")
def user_dashboard():
    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "user":
        return "Access Denied"

    return "Welcome User Dashboard"
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")



if __name__ == "__main__":
    app.run(debug=True)