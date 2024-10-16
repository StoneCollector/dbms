from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt  # Import Flask-Bcrypt
from models import db, User, Manager, LegalAdvisor, Accountant, Manufacturer, Deal, ProfitHandler, retailer_deal, Contract
from sqlalchemy.exc import IntegrityError
from datetime import timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///example.db'
app.config['SECRET_KEY'] = 'mysecret'
app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

db.init_app(app)

# Initialize Bcrypt
bcrypt = Bcrypt(app)

# Set up login manager
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_default_admin():
    """Creates a default admin user with username 'backwardbus' and password '12345' if not exists."""
    with app.app_context():
        # Check if the user exists
        admin = User.query.filter_by(username='backwardbus').first()

        if not admin:
            hashed_password = bcrypt.generate_password_hash('12345').decode('utf-8')  # Use bcrypt for hashing
            # Create the admin user
            admin = User(username='backwardbus', password=hashed_password, role='admin')
            db.session.add(admin)
            db.session.commit()
            print("Default admin user 'backwardbus' created.")

@app.before_request
def initialize():
    """Ensure the database is initialized and create the default admin if necessary."""
    db.create_all()
    create_default_admin()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if user exists
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):  # Check hashed password
            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                if user.role == 'manager':
                    return redirect(url_for('manager_dashboard'))
                elif user.role == 'manufacturer':
                    return redirect(url_for('manufacturer_dashboard'))
                elif user.role == 'financer':
                    return redirect(url_for('financer_dashboard'))
                elif user.role == 'retailer':
                    return redirect(url_for('retailer_dashboard'))
                flash('Login unsuccessful. Please check your username and password.', 'danger')
                return render_template('login.html')
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')

    return render_template('login.html')

@app.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if current_user.role != 'admin':
        flash('You do not have permission to access this page!', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        # Hash the password with bcrypt
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Create a new user
        new_user = User(username=username, password=hashed_password, role=role)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('User added successfully!', 'success')
            return redirect(url_for('add_user'))
        except IntegrityError:
            db.session.rollback()
            flash('Username already exists. Please choose a different username.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')

    return render_template('add_user.html')


@app.route('/')
def home():
    return render_template('home.html')  # Add a home.html file in your templates folder

# Admin dashboard route
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return "Unauthorized", 403
    return render_template('admin_dashboard.html')

@app.route('/view_users')
@login_required
def view_users():
    if current_user.role != 'admin':
        return "Unauthorized", 403
    
    users = User.query.all()  # Fetch all users from the database
    return render_template('view_users.html', users=users)

# Manager dashboard route
@app.route('/manager/dashboard')
@login_required
def manager_dashboard():
    if current_user.role != 'manager':
        return "Unauthorized", 403
    return render_template('form.html')  # Add a corresponding HTML file

@app.route('/add_data', methods=['POST'])
def add_data():
    manager_name = request.form['manager_name']
    contract_advice = request.form['contract_advice']
    legal_advisor_name = request.form['legal_advisor_name']
    deal_status = request.form['deal_status']
    manufacturer_name = request.form['manufacturer_name']

    # Create or get a legal advisor
    legal_advisor = LegalAdvisor.query.filter_by(name=legal_advisor_name).first()
    if not legal_advisor:
        legal_advisor = LegalAdvisor(name=legal_advisor_name)
        db.session.add(legal_advisor)

    # Create or get a manufacturer
    manufacturer = Manufacturer.query.filter_by(name=manufacturer_name).first()
    if not manufacturer:
        manufacturer = Manufacturer(name=manufacturer_name)
        db.session.add(manufacturer)

    # Create the manager
    manager = Manager(name=manager_name)
    db.session.add(manager)

    # Create the contract
    contract = Contract(advice=contract_advice, manager=manager, legal_advisor=legal_advisor)
    db.session.add(contract)

    # Create the deal
    deal = Deal(status=deal_status, manufacturer=manufacturer)
    db.session.add(deal)

    # Commit all changes
    db.session.commit()

    return redirect(url_for('manager_dashboard'))

# Route to display all data
@app.route('/display_data')
def display_data():
    managers = Manager.query.all()
    contracts = Contract.query.all()
    deals = Deal.query.all()
    return render_template('display.html', managers=managers, contracts=contracts, deals=deals)

# Manufacturer dashboard route
@app.route('/manufacturer/dashboard')
@login_required
def manufacturer_dashboard():
    if current_user.role != 'manufacturer':
        return "Unauthorized", 403
    
    # Fetch deals associated with the manufacturer
    deals = Deal.query.filter_by(manufacturer_id=current_user.id).all()
    
    return render_template('manufacturer_dashboard.html', deals=deals)


@app.route('/financer/dashboard', methods=['GET', 'POST'])
@login_required
def financer_dashboard():
    if current_user.role != 'financer':
        return "Unauthorized", 403
    
    if request.method == 'POST':
        form_type = request.form.get('form_type')

        if form_type == 'accountant':  # Handling the Accountant form
            accountant_name = request.form['accountant_name']
            profit_handler_id = request.form['profit_handler_id']
            try:
                accountant = Accountant(name=accountant_name, profit_handler_id=profit_handler_id)
                db.session.add(accountant)
                db.session.commit()
                flash('Accountant added successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error adding accountant: {str(e)}', 'danger')

        elif form_type == 'profit_handler':  # Handling the Profit Handler form
            profit_handler_name = request.form['profit_handler_name']
            try:
                profit_handler = ProfitHandler(name=profit_handler_name)
                db.session.add(profit_handler)
                db.session.commit()
                flash('Profit Handler added successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error adding profit handler: {str(e)}', 'danger')

        elif form_type == 'deal':  # Handling the Deal form
            deal_status = request.form['deal_status']
            manufacturer_id = request.form['manufacturer_id']
            profit_handler_ids = request.form['profit_handler_ids'].split(',')

            try:
                deal = Deal(status=deal_status, manufacturer_id=manufacturer_id)

                # Associate deal with profit handlers
                for handler_id in profit_handler_ids:
                    handler = ProfitHandler.query.get(handler_id)
                    if handler:
                        deal.profit_handlers.append(handler)

                db.session.add(deal)
                db.session.commit()
                flash('Deal added successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error adding deal: {str(e)}', 'danger')

    return render_template('financer_dashboard.html')
 

@app.route('/retailer/dashboard')
@login_required
def retailer_dashboard():
    if current_user.role != 'retailer':
        return "Unauthorized", 403
    
    # Fetch deals associated with the current retailer
    deals = Deal.query.join(retailer_deal).filter(retailer_deal.c.retailer_id == current_user.id).all()
    
    return render_template('retailer_dashboard.html', deals=deals)
 

# Handle logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)