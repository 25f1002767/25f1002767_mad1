from flask import Flask, render_template, request, redirect , session 
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User, StaffProfile, Trek
from models import User
from models import Booking
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

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]
        contact_number = request.form["contact_number"]
        experience_years = request.form["experience_years"]

        existing_user = User.query.filter_by(
            username=username
        ).first()

        if existing_user:
            return "Username already exists"

        existing_email = User.query.filter_by(
            email=email
        ).first()

        if existing_email:
            return "Email already exists"

        hashed_password = generate_password_hash(password)

        user = User(
            username=username,
            email=email,
            password=hashed_password,
            role=role
        )

        db.session.add(user)
        db.session.commit()

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

        return redirect("/login")

    return render_template("register.html")
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if not user:
            return "Invalid Email"

        if user.is_blacklisted:
            return "Your account has been blocked by Admin"

        if not check_password_hash(user.password, password):
            return "Invalid Password"

        session["user_id"] = user.id
        session["role"] = user.role

        if user.role == "admin":
            return redirect("/admin")

        elif user.role == "staff":

            if user.staff_profile is None:
                return "Staff profile not found"

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

    total_users = User.query.filter_by(
        role="user"
    ).count()

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
@app.route("/admin/pending-staff")
def pending_staff():

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
@app.route("/admin/staff")
def manage_staff():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    search = request.args.get("search")

    staff_members = StaffProfile.query

    if search:

        staff_members = staff_members.join(User).filter(
            User.username.contains(search)
        )

    staff_members = staff_members.all()

    return render_template(
        "manage_staff.html",
        staff_members=staff_members
    )
@app.route("/blacklist-staff/<int:staff_id>")
def blacklist_staff(staff_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    staff = StaffProfile.query.get_or_404(staff_id)

    staff.user.is_blacklisted = True
    staff.user.is_active = False

    db.session.commit()

    return redirect("/admin/staff")
@app.route("/activate-staff/<int:staff_id>")
def activate_staff(staff_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    staff = StaffProfile.query.get_or_404(staff_id)

    staff.user.is_blacklisted = False
    staff.user.is_active = True

    db.session.commit()

    return redirect("/admin/staff")
@app.route("/delete-staff/<int:staff_id>")
def delete_staff(staff_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    staff = StaffProfile.query.get_or_404(staff_id)

    user = staff.user

    db.session.delete(staff)
    db.session.delete(user)

    db.session.commit()

    return redirect("/admin/staff")
@app.route("/admin/treks")
def manage_treks():

    search = request.args.get("search")

    treks = Trek.query

    if search:

        treks = treks.filter(
            Trek.trek_name.contains(search)
        )

    treks = treks.all()

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

    total_assigned_treks = len(assigned_treks)

    total_trekkers = 0

    for trek in assigned_treks:
        total_trekkers += Booking.query.filter_by(
            trek_id=trek.id
        ).count()

    return render_template(
        "staff_dashboard.html",
        assigned_treks=assigned_treks,
        total_assigned_treks=total_assigned_treks,
        total_trekkers=total_trekkers
    )
@app.route("/staff/profile", methods=["GET", "POST"])
def staff_profile():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "staff":
        return "Access Denied"

    staff = StaffProfile.query.filter_by(
        user_id=session["user_id"]
    ).first()

    if request.method == "POST":

        staff.contact_number = request.form.get(
            "contact_number"
        )

        staff.experience_years = int(
            request.form.get("experience_years")
        )

        db.session.commit()

        return redirect("/staff")

    return render_template(
        "staff_profile.html",
        staff=staff
    )
@app.route("/staff/trek-users/<int:trek_id>")
def view_trek_users(trek_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "staff":
        return "Access Denied"

    staff = StaffProfile.query.filter_by(
        user_id=session["user_id"]
    ).first()

    trek = Trek.query.get_or_404(trek_id)

    if trek.assigned_staff_id != staff.id:
        return "Access Denied"

    bookings = Booking.query.filter_by(
        trek_id=trek.id
    ).all()

    return render_template(
        "view_trek_users.html",
        trek=trek,
        bookings=bookings
    )
@app.route("/staff/update-slots/<int:trek_id>", methods=["GET", "POST"])
def update_slots(trek_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "staff":
        return "Access Denied"

    staff = StaffProfile.query.filter_by(
        user_id=session["user_id"]
    ).first()

    trek = Trek.query.get_or_404(trek_id)

    if trek.assigned_staff_id != staff.id:
        return "Access Denied"

    if request.method == "POST":

        trek.available_slots = int(
            request.form.get("available_slots")
        )

        db.session.commit()

        return redirect("/staff")

    return render_template(
        "update_slots.html",
        trek=trek
    )
@app.route("/staff/update-status/<int:trek_id>", methods=["GET", "POST"])
def update_trek_status(trek_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "staff":
        return "Access Denied"

    staff = StaffProfile.query.filter_by(
        user_id=session["user_id"]
    ).first()

    trek = Trek.query.get_or_404(trek_id)

    if trek.assigned_staff_id != staff.id:
        return "Access Denied"

    if request.method == "POST":

        trek.status = request.form.get("status")

        if trek.status == "Completed":

            bookings = Booking.query.filter_by(
                trek_id=trek.id
            ).all()

            for booking in bookings:
                booking.booking_status = "Completed"

        db.session.commit()

        return redirect("/staff")

    return render_template(
        "update_trek_status.html",
        trek=trek
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

    location = request.args.get("location")
    difficulty = request.args.get("difficulty")

    treks = Trek.query.filter(
        Trek.available_slots > 0
    )

    if location:
        treks = treks.filter(
            Trek.location.contains(location)
        )

    if difficulty:
        treks = treks.filter_by(
            difficulty=difficulty
        )

    treks = treks.all()

    return render_template(
        "user_dashboard.html",
        treks=treks
    )
@app.route("/user/profile", methods=["GET", "POST"])
def user_profile():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "user":
        return "Access Denied"

    user = User.query.get(session["user_id"])

    if request.method == "POST":

        user.username = request.form.get("username")
        user.email = request.form.get("email")

        db.session.commit()

        return redirect("/user")

    return render_template(
        "user_profile.html",
        user=user
    )


@app.route("/book-trek/<int:trek_id>")
def book_trek(trek_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "user":
        return "Access Denied"

    trek = Trek.query.get_or_404(trek_id)
    
    if trek.status != "Open":
       return "This trek is not open for booking"

    if trek.available_slots <= 0:
       return "No slots available for this trek"

    existing_booking = Booking.query.filter_by(
        user_id=session["user_id"],
        trek_id=trek.id
    ).first()

    if existing_booking:
        return "You have already booked this trek"

    booking = Booking(
        user_id=session["user_id"],
        trek_id=trek.id,
        booking_status="booked",
        payment_status="pending"
    )

    db.session.add(booking)
    trek.available_slots -= 1

    db.session.commit()

    return redirect("/user")

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
    )
@app.route("/admin/users")
def manage_users():

    search = request.args.get("search")

    users = User.query.filter_by(role="user")

    if search:

        users = users.filter(
            (User.username.contains(search)) |
            (User.email.contains(search))
        )

    users = users.all()

    return render_template(
        "manage_users.html",
        users=users
    )
@app.route("/blacklist-user/<int:user_id>")
def blacklist_user(user_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    user = User.query.get_or_404(user_id)

    user.is_blacklisted = True
    user.is_active = False

    db.session.commit()

    return redirect("/admin/users")
@app.route("/activate-user/<int:user_id>")
def activate_user(user_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    user = User.query.get_or_404(user_id)

    user.is_blacklisted = False
    user.is_active = True

    db.session.commit()

    return redirect("/admin/users")

@app.route("/deactivate-user/<int:user_id>")
def deactivate_user(user_id):

    user = User.query.get_or_404(user_id)

    user.is_active = False

    db.session.commit()

    return redirect("/admin/users")
@app.route("/my-bookings")
def my_bookings():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "user":
        return "Access Denied"

    bookings = Booking.query.filter_by(
        user_id=session["user_id"]
    ).all()
    return render_template(
        "my_bookings.html",
        bookings=bookings
    )

@app.route("/cancel-booking/<int:booking_id>")
def cancel_booking(booking_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "user":
        return "Access Denied"

    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != session["user_id"]:
        return "Access Denied"
    trek = Trek.query.get(booking.trek_id)

    trek.available_slots += 1

    booking.booking_status = "Cancelled"
    db.session.commit()

    return redirect("/my-bookings")
@app.route("/admin/bookings")
def admin_bookings():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    bookings = Booking.query.all()

    return render_template(
        "admin_bookings.html",
        bookings=bookings
    )
@app.route("/trek-history")
def trek_history():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "user":
        return "Access Denied"

    history = Booking.query.join(Trek).filter(
        Booking.user_id == session["user_id"],
        Trek.status == "Completed"
    ).all()

    return render_template(
        "trek_history.html",
        history=history
    )

    


if __name__ == "__main__":
    app.run(debug=True)