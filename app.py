from flask import Flask, render_template, request, redirect , session 
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User, StaffProfile, Trek
from models import User
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

@app.route("/")
def home():
    return redirect("/register")
# -------------------------------
# Home Route
# -------------------------------
# If someone visits:
# http://127.0.0.1:5000/
# they will automatically go to
# http://127.0.0.1:5000/register
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

        # Check duplicate username
        existing_user = User.query.filter_by(
            username=username
        ).first()

        if existing_user:
            return "Username already exists"

        # Check duplicate email
        existing_email = User.query.filter_by(
            email=email
        ).first()

        if existing_email:
            return "Email already exists"

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

        return redirect("/login")

        return render_template("register.html")
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
    total_users = User.query.filter_by(role="user").count()

    total_staff = StaffProfile.query.filter_by(
        approval_status="approved"
    ).count()

    total_treks = Trek.query.count()

    total_bookings = Booking.query.count()

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        total_staff=total_staff,
        total_treks=total_treks,
        total_bookings=total_bookings
    )

    return "Welcome Admin Dashboard"
@app.route("/admin/treks")
def manage_treks():

    treks = Trek.query.all()

    return render_template(
        "manage_treks.html",
        treks=treks
    )
@app.route(
    "/assign-staff/<int:trek_id>",
    methods=["GET", "POST"]
)
def assign_staff(trek_id):

    trek = Trek.query.get_or_404(trek_id)

    approved_staff = StaffProfile.query.filter_by(
        approval_status="approved"
    ).all()

    if request.method == "POST":

        staff_id = request.form.get("staff_id")

        trek.assigned_staff_id = staff_id

        db.session.commit()

        return redirect("/admin/treks")

    return render_template(
        "assign_staff.html",
        trek=trek,
        approved_staff=approved_staff
    )

@app.route("/staff")
def staff_dashboard():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "staff":
        return "Access Denied"

    user_id = session["user_id"]

    staff = StaffProfile.query.filter_by(
        user_id=user_id
    ).first()

    assigned_treks = Trek.query.filter_by(
        assigned_staff_id=staff.id
    ).all()

    return render_template(
        "staff_dashboard.html",
        assigned_treks=assigned_treks
    )
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
@app.route(
    "/create-trek",
    methods=["GET", "POST"]
)
def create_trek():

    if request.method == "POST":

        trek_name = request.form.get("trek_name")
        location = request.form.get("location")
        difficulty = request.form.get("difficulty")
        duration_days = request.form.get("duration_days")
        available_slots = request.form.get("available_slots")
        start_date = datetime.strptime(
        request.form.get("start_date"),
        "%Y-%m-%d"
        ).date()

        end_date = datetime.strptime(
            request.form.get("end_date"),
            "%Y-%m-%d"
        ).date()
        description = request.form.get("description")

        new_trek = Trek(
            trek_name=trek_name,
            location=location,
            difficulty=difficulty,
            duration_days=duration_days,
            available_slots=available_slots,
            start_date=start_date,
            end_date=end_date,
            description=description
        )

        db.session.add(new_trek)

        db.session.commit()

        return redirect("/admin/treks")

    return render_template("create_trek.html")
@app.route("/delete-trek/<int:trek_id>")
def delete_trek(trek_id):

    trek = Trek.query.get_or_404(trek_id)

    db.session.delete(trek)

    db.session.commit()

    return redirect("/admin/treks")
@app.route(
    "/edit-trek/<int:trek_id>",
    methods=["GET", "POST"]
)
def edit_trek(trek_id):

    trek = Trek.query.get_or_404(trek_id)

    if request.method == "POST":

        trek.trek_name = request.form.get("trek_name")

        trek.location = request.form.get("location")

        trek.difficulty = request.form.get("difficulty")

        trek.duration_days = int(
            request.form.get("duration_days")
        )

        trek.available_slots = int(
            request.form.get("available_slots")
        )

        db.session.commit()

        return redirect("/admin/treks")

    return render_template(
        "edit_trek.html",
        trek=trek
    )@app.route("/admin/users")
def manage_users():

    users = User.query.filter_by(
        role="user"
    ).all()

    return render_template(
        "manage_users.html",
        users=users
    )
@app.route("/admin/users")
def manage_users():

    users = User.query.filter_by(
        role="user"
    ).all()

    return render_template(
        "manage_users.html",
        users=users
    )
@app.route("/deactivate-user/<int:user_id>")
def deactivate_user(user_id):

    user = User.query.get_or_404(user_id)

    user.is_active = False

    db.session.commit()

    return redirect("/admin/users")
@app.route(
    "/assign-staff/<int:trek_id>",
    methods=["GET", "POST"]
)
def assign_staff(trek_id):

    trek = Trek.query.get_or_404(trek_id)

    approved_staff = StaffProfile.query.filter_by(
        approval_status="approved"
    ).all()

    if request.method == "POST":

        staff_id = request.form.get("staff_id")

        trek.assigned_staff_id = staff_id

        db.session.commit()

        return redirect("/admin/treks")

    return render_template(
        "assign_staff.html",
        trek=trek,
        approved_staff=approved_staff
    )

if __name__ == "__main__":
    app.run(debug=True)