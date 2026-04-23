from flask import Flask, render_template, request, redirect, url_for, session
from database import init_db, get_db
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = "bbm-tracker-secret-key"

@app.before_request
def setup():
    init_db()

@app.route("/")
def index():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM consumption ORDER BY created_at DESC")
    records = cur.fetchall()
    cur.close()
    db.close()
    return render_template("index.html", records=records)

@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        fuel_type = request.form.get("fuel_type")
        price = request.form.get("price")
        current_km = request.form.get("current_km")
        notes = request.form.get("notes", "")

        # Remember last selected type in session
        session["last_fuel_type"] = fuel_type

        db = get_db()

        # Calculate distance from last entry
        cur = db.cursor()
        cur.execute(
            "SELECT current_km FROM consumption ORDER BY created_at DESC LIMIT 1"
        )
        last = cur.fetchone()
        distance = None
        if last and last["current_km"]:
            distance = float(current_km) - float(last["current_km"])

        cur.execute(
            """INSERT INTO consumption (fuel_type, price, current_km, distance, notes, created_at)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (fuel_type, price, current_km, distance, notes, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        cur.close()
        db.commit()
        db.close()
        return redirect(url_for("index"))

    last_fuel_type = session.get("last_fuel_type", "Pertalite")
    return render_template("add.html", last_fuel_type=last_fuel_type)

@app.route("/delete/<int:record_id>", methods=["POST"])
def delete(record_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM consumption WHERE id = %s", (record_id,))
    cur.close()
    db.commit()
    db.close()
    return redirect(url_for("index"))

@app.route("/mileage", methods=["GET", "POST"])
def mileage():
    db = get_db()
    cur = db.cursor()
    if request.method == "POST":
        odometer_km = request.form.get("odometer_km")
        notes = request.form.get("notes", "")
        cur.execute(
            "INSERT INTO mileage (odometer_km, notes, recorded_at) VALUES (%s, %s, %s)",
            (odometer_km, notes, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        cur.close()
        db.commit()
        db.close()
        return redirect(url_for("mileage"))

    cur.execute("SELECT * FROM mileage ORDER BY recorded_at DESC")
    records = cur.fetchall()
    cur.close()
    db.close()
    return render_template("mileage.html", records=records)

@app.route("/mileage/delete/<int:record_id>", methods=["POST"])
def delete_mileage(record_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM mileage WHERE id = %s", (record_id,))
    cur.close()
    db.commit()
    db.close()
    return redirect(url_for("mileage"))

@app.route("/stats")
def stats():
    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM consumption ORDER BY created_at ASC")
    records = cur.fetchall()

    cur.execute("SELECT SUM(price) as total FROM consumption")
    total_spent = cur.fetchone()["total"] or 0

    cur.execute("SELECT COUNT(*) as count FROM consumption")
    total_entries = cur.fetchone()["count"] or 0

    cur.execute(
        "SELECT fuel_type, COUNT(*) as count, SUM(price) as total FROM consumption GROUP BY fuel_type"
    )
    by_type = cur.fetchall()

    # Mileage by date
    cur.execute("""
        SELECT DATE(recorded_at::timestamp) as day,
               MAX(odometer_km) - MIN(odometer_km) as distance,
               MIN(odometer_km) as start_km,
               MAX(odometer_km) as end_km,
               COUNT(*) as entries
        FROM mileage
        GROUP BY day
        ORDER BY day DESC
    """)
    mileage_by_date = cur.fetchall()

    # Mileage by month
    cur.execute("""
        SELECT TO_CHAR(recorded_at::timestamp, 'YYYY-MM') as month,
               MAX(odometer_km) - MIN(odometer_km) as distance,
               MIN(odometer_km) as start_km,
               MAX(odometer_km) as end_km,
               COUNT(*) as entries
        FROM mileage
        GROUP BY month
        ORDER BY month DESC
    """)
    mileage_by_month = cur.fetchall()

    # Date range filter params
    range_from = request.args.get("range_from", "")
    range_to   = request.args.get("range_to", "")
    mileage_range = None
    if range_from and range_to:
        cur.execute("""
            SELECT MAX(odometer_km) - MIN(odometer_km) as distance,
                   MIN(odometer_km) as start_km,
                   MAX(odometer_km) as end_km,
                   COUNT(*) as entries
            FROM mileage
            WHERE DATE(recorded_at::timestamp) BETWEEN %s AND %s
        """, (range_from, range_to))
        mileage_range = cur.fetchone()

    cur.close()
    db.close()
    return render_template(
        "stats.html",
        records=records,
        total_spent=total_spent,
        total_entries=total_entries,
        by_type=by_type,
        mileage_by_date=mileage_by_date,
        mileage_by_month=mileage_by_month,
        mileage_range=mileage_range,
        range_from=range_from,
        range_to=range_to,
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
