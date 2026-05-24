from flask import Flask, jsonify, render_template, request
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
import psycopg2.extras
import os

app = Flask(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL', '').replace('postgres://', 'postgresql://')

def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS produits (
        id SERIAL PRIMARY KEY,
        nom TEXT NOT NULL,
        prix INTEGER NOT NULL,
        stock INTEGER NOT NULL
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'admin'
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS commandes (
        id SERIAL PRIMARY KEY,
        nom_client TEXT NOT NULL,
        telephone TEXT NOT NULL,
        adresse TEXT NOT NULL,
        total INTEGER NOT NULL,
        statut TEXT NOT NULL DEFAULT 'en attente',
        date_commande TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS commande_items (
        id SERIAL PRIMARY KEY,
        commande_id INTEGER REFERENCES commandes(id),
        produit_nom TEXT NOT NULL,
        quantite INTEGER NOT NULL,
        prix INTEGER NOT NULL
    )''')
    cur.execute('SELECT COUNT(*) FROM produits')
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO produits (nom, prix, stock) VALUES ('Telephone', 150000, 10)")
        cur.execute("INSERT INTO produits (nom, prix, stock) VALUES ('Ecouteurs', 25000, 5)")
        cur.execute("INSERT INTO produits (nom, prix, stock) VALUES ('Chargeur', 8000, 20)")
    cur.execute('SELECT COUNT(*) FROM users')
    if cur.fetchone()[0] == 0:
        mot_de_passe_hash = generate_password_hash('admin123')
        cur.execute("INSERT INTO users (username, password, role) VALUES ('admin', %s, 'admin')",
                    (mot_de_passe_hash,))
    conn.commit()
    cur.close()
    conn.close()

@app.route('/')
def accueil():
    return render_template('index.html')

@app.route('/produits')
def liste_produits():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute('SELECT * FROM produits')
    produits = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([dict(p) for p in produits])

@app.route('/produits/<int:id>')
def un_produit(id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute('SELECT * FROM produits WHERE id = %s', (id,))
    produit = cur.fetchone()
    cur.close()
    conn.close()
    if produit:
        return jsonify(dict(produit))
    return jsonify({"erreur": "Produit non trouve"}), 404

@app.route('/produits/ajouter', methods=['POST'])
def ajouter_produit():
    data = request.get_json()
    conn = get_db()
    cur = conn.cursor()
    cur.execute('INSERT INTO produits (nom, prix, stock) VALUES (%s, %s, %s)',
                (data['nom'], data['prix'], data['stock']))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Produit ajoute"}), 201

@app.route('/produits/supprimer/<int:id>', methods=['DELETE'])
def supprimer_produit(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM produits WHERE id = %s', (id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Produit supprime"}), 200

@app.route('/produits/modifier/<int:id>', methods=['PUT'])
def modifier_produit(id):
    data = request.get_json()
    conn = get_db()
    cur = conn.cursor()
    cur.execute('UPDATE produits SET nom=%s, prix=%s, stock=%s WHERE id=%s',
                (data['nom'], data['prix'], data['stock'], id))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Produit modifie"}), 200

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute('SELECT * FROM users WHERE username = %s', (data['username'],))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if user and check_password_hash(user['password'], data['password']):
        return jsonify({"message": "Connexion reussie", "role": user['role']}), 200
    return jsonify({"erreur": "Identifiants incorrects"}), 401

@app.route('/commandes', methods=['POST'])
def passer_commande():
    data = request.get_json()
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''INSERT INTO commandes (nom_client, telephone, adresse, total)
                   VALUES (%s, %s, %s, %s) RETURNING id''',
                (data['nom_client'], data['telephone'], data['adresse'], data['total']))
    commande_id = cur.fetchone()[0]
    for item in data['items']:
        cur.execute('''INSERT INTO commande_items (commande_id, produit_nom, quantite, prix)
                       VALUES (%s, %s, %s, %s)''',
                    (commande_id, item['nom'], item['quantite'], item['prix']))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Commande passee", "id": commande_id}), 201

@app.route('/commandes', methods=['GET'])
def liste_commandes():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute('SELECT * FROM commandes ORDER BY date_commande DESC')
    commandes = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([dict(c) for c in commandes])

@app.route('/commandes/<int:id>/statut', methods=['PUT'])
def modifier_statut(id):
    data = request.get_json()
    conn = get_db()
    cur = conn.cursor()
    cur.execute('UPDATE commandes SET statut=%s WHERE id=%s', (data['statut'], id))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Statut modifie"}), 200

init_db()

if __name__ == '__main__':
    app.run(debug=True)
