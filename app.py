import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'votre_cle_secrete_ici' # Changez ceci en production
app.config['SQLALCHEMY_DATABASE_DATA_URI'] = 'sqlite:///radar.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- MODÈLES DE DONNÉES ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    results = db.relationship('RadarResult', backref='user', lazy=True)

class RadarResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    data_json = db.Column(db.Text, nullable=False) # Stocke toutes les réponses
    score_total = db.Column(db.Float)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- INITIALISATION DE L'ADMIN ---

def create_admin():
    with app.app_context():
        db.create_all()
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            # Création du compte demandé : admin / delivrance2026
            hashed_pw = generate_password_hash('delivrance2026', method='pbkdf2:sha256')
            new_admin = User(username='admin', password=hashed_pw, is_admin=True)
            db.session.add(new_admin)
            db.session.commit()
            print("Compte Admin créé avec succès.")

# --- ROUTES ---

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('index'))
        flash('Identifiants incorrects')
    return render_template('login.html')

@app.route('/save_radar', methods=['POST'])
@login_required
def save_radar():
    # On récupère les données du formulaire
    form_data = request.form.to_dict()
    
    # Enregistrement dans l'historique
    new_result = RadarResult(
        data_json=json.dumps(form_data),
        user_id=current_user.id
    )
    db.session.add(new_result)
    db.session.commit()
    
    flash('Résultats enregistrés avec succès dans votre historique.')
    return redirect(url_for('history'))

@app.route('/history')
@login_required
def history():
    # Récupère l'historique de l'utilisateur connecté
    user_results = RadarResult.query.filter_by(user_id=current_user.id).order_by(RadarResult.date_creation.desc()).all()
    return render_template('history.html', results=user_results)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    create_admin()
    app.run(debug=True)
