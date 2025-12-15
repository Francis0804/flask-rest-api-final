from flask import Flask, request, jsonify, make_response
from flask_mysqldb import MySQL
import MySQLdb.cursors
from dicttoxml import dicttoxml
import jwt
import datetime

app = Flask(__name__)

# MySQL Config (CHANGE DB NAME IF NEEDED)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'aying'   # <-- your database
app.config['SECRET_KEY'] = 'secret123'

mysql = MySQL(app)

# -----------------------------------------------
# Helper for XML output
# -----------------------------------------------
def output_format(data, format_type):
    if format_type == "xml":
        xml = dicttoxml(data, custom_root='response', attr_type=False)
        response = make_response(xml)
        response.headers['Content-Type'] = 'application/xml'
        return response
    return jsonify(data)

# -----------------------------------------------
# JWT Login
# -----------------------------------------------
@app.route('/login', methods=['POST'])
def login():
    auth = request.json
    if not auth or not auth.get('username'):
        return jsonify({"message": "Missing credentials"}), 400

    token = jwt.encode({
        "user": auth["username"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
    }, app.config['SECRET_KEY'], algorithm="HS256")

    return jsonify({"token": token})

# -----------------------------------------------
# Middleware: Require JWT
# -----------------------------------------------
def require_token(f):
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"message": "Token missing"}), 401

        try:
            jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        except:
            return jsonify({"message": "Invalid token"}), 401

        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# -----------------------------------------------
# CRUD ROUTES
# -----------------------------------------------
@app.route('/products', methods=['GET'])
@require_token
def get_products():
    format_type = request.args.get("format", "json")

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM products")
    data = cursor.fetchall()

    return output_format(data, format_type)

@app.route('/products', methods=['POST'])
@require_token
def add_product():
    data = request.json

    if not data.get("name"):
        return jsonify({"message": "Name required"}), 400

    cursor = mysql.connection.cursor()
    cursor.execute(
        "INSERT INTO products(name, price, quantity) VALUES (%s,%s,%s)",
        (data["name"], data["price"], data["quantity"])
    )
    mysql.connection.commit()

    return jsonify({"message": "Product created"}), 201

# -----------------------------------------------
# START APP
# -----------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
