from flask import Flask, jsonify
from flask_cors import CORS, cross_origin
import mysql.connector

app = Flask(__name__)
app.config.from_envvar('APP_SETTINGS')


def dbconn():
    return mysql.connector.connect(host=app.config['DATABASE_HOST'],
                                   user=app.config['DATABASE_USER'],
                                   password=app.config['DATABASE_PASSWORD'],
                                   database=app.config['DATABASE_NAME'])


@app.route("/hello", methods=["GET"])
def say_hello():
    conn = dbconn()
    cursor = conn.cursor()
    cursor.execute('select count(*) from genes')
    num_genes = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return jsonify({"msg": "Hello from Flask, # genes: %d" % num_genes})


if __name__ == "__main__":
    # Please do not set debug=True in production
    app.run(host="0.0.0.0", port=5000, debug=True)
