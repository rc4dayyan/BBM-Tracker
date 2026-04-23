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
    records = db.execute(
        "SELECT * FROM consumption ORDER BY created_at DESC"
    ).fetchall()
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
        last = db.execute(
            "SELECT current_km FROM consumption ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        distance = None
        if last and last["current_km"]:
            distance = float(current_km) - float(last["current_km"])

        db.execute(
            """INSERT INTO consumption (fuel_type, price, current_km, distance, notes, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (fuel_type, price, current_km, distance, notes, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        db.commit()
        db.close()
        return redirect(url_for("index"))

    last_fuel_type = session.get("last_fuel_type", "Pertalite")
    return render_template("add.html", last_fuel_type=last_fuel_type)

@app.route("/delete/<int:record_id>", methods=["POST"])
def delete(record_id):
    db = get_db()
    db.execute("DELETE FROM consumption WHERE id = ?", (record_id,))
    db.commit()
    db.close()
    return redirect(url_for("index"))

@app.route("/mileage", methods=["GET", "POST"])
def mileage():
    db = get_db()
    if request.method == "POST":
        odometer_km = request.form.get("odometer_km")
        notes = request.form.get("notes", "")
        db.execute(
            "INSERT INTO mileage (odometer_km, notes, recorded_at) VALUES (?, ?, ?)",
            (odometer_km, notes, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        db.commit()
        db.close()
        return redirect(url_for("mileage"))

    records = db.execute("SELECT * FROM mileage ORDER BY recorded_at DESC").fetchall()
    db.close()
    return render_template("mileage.html", records=records)

@app.route("/mileage/delete/<int:record_id>", methods=["POST"])
def delete_mileage(record_id):
    db = get_db()
    db.execute("DELETE FROM mileage WHERE id = ?", (record_id,))
    db.commit()
    db.close()
    return redirect(url_for("mileage"))

@app.route("/stats")
def stats():
    db = get_db()
    records = db.execute("SELECT * FROM consumption ORDER BY created_at ASC").fetchall()
    total_spent = db.execute("SELECT SUM(price) as total FROM consumption").fetchone()["total"] or 0
    total_entries = db.execute("SELECT COUNT(*) as count FROM consumption").fetchone()["count"] or 0
    by_type = db.execute(
        "SELECT fuel_type, COUNT(*) as count, SUM(price) as total FROM consumption GROUP BY fuel_type"
    ).fetchall()

    # Mileage by date
    mileage_by_date = db.execute("""
        SELECT DATE(recorded_at) as day,
               MAX(odometer_km) - MIN(odometer_km) as distance,
               MIN(odometer_km) as start_km,
               MAX(odometer_km) as end_km,
               COUNT(*) as entries
        FROM mileage
        GROUP BY day
        ORDER BY day DESC
    """).fetchall()

    # Mileage by month
    mileage_by_month = db.execute("""
        SELECT strftime('%Y-%m', recorded_at) as month,
               MAX(odometer_km) - MIN(odometer_km) as distance,
               MIN(odometer_km) as start_km,
               MAX(odometer_km) as end_km,
               COUNT(*) as entries
        FROM mileage
        GROUP BY month
        ORDER BY month DESC
    """).fetchall()

    # Date range filter params
    range_from = request.args.get("range_from", "")
    range_to   = request.args.get("range_to", "")
    mileage_range = None
    if range_from and range_to:
        row = db.execute("""
            SELECT MAX(odometer_km) - MIN(odometer_km) as distance,
                   MIN(odometer_km) as start_km,
                   MAX(odometer_km) as end_km,
                   COUNT(*) as entries
            FROM mileage
            WHERE DATE(recorded_at) BETWEEN ? AND ?
        """, (range_from, range_to)).fetchone()
        mileage_range = row

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
