from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# User model with nullable manager_id
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('managers.id'), nullable=True)
    manager = db.relationship('Manager', back_populates='users')

# Manager model with explicit table name
class Manager(db.Model):
    __tablename__ = 'managers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    users = db.relationship('User', back_populates='manager')
    documentations = db.relationship('Documentation', back_populates='manager')
    contracts = db.relationship('Contract', back_populates='manager')

# Documentation model
class Documentation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    officer = db.Column(db.String(100))
    manager_id = db.Column(db.Integer, db.ForeignKey('managers.id'))
    manager = db.relationship('Manager', back_populates='documentations')

# LegalAdvisor model with contract relationship
class LegalAdvisor(db.Model):
    __tablename__ = 'legal_advisors'  # Explicitly name the table
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    
    # Relationship with Contract
    contracts = db.relationship('Contract', back_populates='legal_advisor')

class Contract(db.Model):
    __tablename__ = 'contracts'  # Explicitly name the table
    id = db.Column(db.Integer, primary_key=True)
    advice = db.Column(db.String(100))
    
    # ForeignKey to LegalAdvisor table
    legal_advisor_id = db.Column(db.Integer, db.ForeignKey('legal_advisors.id'))  # ForeignKey reference

    legal_advisor = db.relationship('LegalAdvisor', back_populates='contracts')
    manager_id = db.Column(db.Integer, db.ForeignKey('managers.id'))  # ForeignKey to Manager table
    manager = db.relationship('Manager', back_populates='contracts')

# Association table for many-to-many relationship between Deal and ProfitHandler
deal_profit_handler = db.Table('deal_profit_handler',
    db.Column('deal_id', db.Integer, db.ForeignKey('deals.id'), primary_key=True),
    db.Column('profit_handler_id', db.Integer, db.ForeignKey('profit_handlers.id'), primary_key=True)
)

# DocumentStorage model
class DocumentStorage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    storage_type = db.Column(db.String(100))

# Renamed Accountant model (singular)
class Accountant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    profit_handler_id = db.Column(db.Integer, db.ForeignKey('profit_handlers.id'))
    profit_handler = db.relationship('ProfitHandler', back_populates='accountants')

# ProfitHandler model
class ProfitHandler(db.Model):
    __tablename__ = 'profit_handlers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    accountants = db.relationship('Accountant', back_populates='profit_handler')
    deals = db.relationship('Deal', secondary=deal_profit_handler, back_populates='profit_handlers')

class Manufacturer(db.Model):
    __tablename__ = 'manufacturers'  # Explicitly set the table name
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    deals = db.relationship('Deal', back_populates='manufacturer')

class Deal(db.Model):
    __tablename__ = 'deals'
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(100))
    manufacturer_id = db.Column(db.Integer, db.ForeignKey('manufacturers.id'))
    manufacturer = db.relationship('Manufacturer', back_populates='deals')
    profit_handlers = db.relationship('ProfitHandler', secondary=deal_profit_handler, back_populates='deals')
    retailers = db.relationship('Retailer', secondary='retailer_deal', back_populates='deals')


class Retailer(db.Model):
    __tablename__ = 'retailers'  # Explicitly name the table
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    
    # Relationship with Deal
    deals = db.relationship('Deal', back_populates='retailers', secondary='retailer_deal')

# Association table for many-to-many relationship between Retailer and Deal
retailer_deal = db.Table('retailer_deal',
    db.Column('retailer_id', db.Integer, db.ForeignKey('retailers.id'), primary_key=True),
    db.Column('deal_id', db.Integer, db.ForeignKey('deals.id'), primary_key=True)
)
