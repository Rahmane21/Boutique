from flask import Flask, jsonify, render_template, request
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), 'boutique.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS produits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        prix INTEGER NOT NULL,
        stock INTEGER NOT NULL
    )''')
    if conn.execute('SELECT COUNT(*) FROM produits').fetchone()[0] == 0:
        conn.execute("INSERT INTO produits (nom, prix, stock) VALUES ('Telephone', 150000, 10)")
        conn.execute("INSERT INTO produits (nom, prix, stock) VALUES ('Ecouteurs', 25000, 5)")
        conn.execute("INSERT INTO produits (nom, prix, stock) VALUES ('Chargeur', 8000, 20)")
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'admin'
    )''')
    if conn.execute('SELECT COUNT(*) FROM users').fetchone()[0] == 0:
        mot_de_passe_hash = generate_password_hash('admin123')
        conn.execute("INSERT INTO users (username, password, role) VALUES ('admin', ?, 'admin')",
                     (mot_de_passe_hash,))
    conn.commit()
    conn.close()

@app.route('/')
def accueil():
    return render_template('index.html')

@app.route('/produits')
def liste_produits():
    conn = get_db()
    produits = conn.execute('SELECT * FROM produits').fetchall()
    conn.close()
    return jsonify([dict(p) for p in produits])

@app.route('/produits/<int:id>')
def un_produit(id):
    conn = get_db()
    produit = conn.execute('SELECT * FROM produits WHERE id = ?', (id,)).fetchone()
    conn.close()
    if produit:
        return jsonify(dict(produit))
    return jsonify({"erreur": "Produit non trouve"}), 404

@app.route('/produits/ajouter', methods=['POST'])
def ajouter_produit():
    data = request.get_json()
    conn = get_db()
    conn.execute('INSERT INTO produits (nom, prix, stock) VALUES (?, ?, ?)',
                 (data['nom'], data['prix'], data['stock']))
    conn.commit()
    conn.close()
    return jsonify({"message": "Produit ajoute"}), 201

@app.route('/produits/supprimer/<int:id>', methods=['DELETE'])
def supprimer_produit(id):
    conn = get_db()
    conn.execute('DELETE FROM produits WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Produit supprime"}), 200

@app.route('/produits/modifier/<int:id>', methods=['PUT'])
def modifier_produit(id):
    data = request.get_json()
    conn = get_db()
    conn.execute('UPDATE produits SET nom=?, prix=?, stock=? WHERE id=?',
                 (data['nom'], data['prix'], data['stock'], id))
    conn.commit()
    conn.close()
    return jsonify({"message": "Produit modifie"}), 200

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE username=?',
                        (data['username'],)).fetchone()
    conn.close()
    if user and check_password_hash(user['password'], data['password']):
        return jsonify({"message": "Connexion reussie", "role": user['role']}), 200
    return jsonify({"erreur": "Identifiants incorrects"}), 401

init_db()

if __name__ == '__main__':
    app.run(debug=True)
