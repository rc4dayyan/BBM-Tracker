from flask import Flask, render_template, request, redirect, url_for, session, g, flash
from database import init_db, get_db
from datetime import datetime, date, timezone, timedelta

app = Flask(__name__)
app.secret_key = "bbm-tracker-secret-key"

WIB = timezone(timedelta(hours=7))

def now_wib():
    return datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S")

@app.before_request
def setup():
    init_db()

@app.context_processor
def inject_vehicles():
    db = get_db()
    vehicles = db.table("vehicles").select("*").order("created_at").execute().data
    active_vehicle_id = session.get("active_vehicle_id")
    active_vehicle = None
    if vehicles:
        if active_vehicle_id:
            active_vehicle = next((v for v in vehicles if v["id"] == active_vehicle_id), None)
        if not active_vehicle:
            active_vehicle = vehicles[0]
            session["active_vehicle_id"] = active_vehicle["id"]
    return dict(vehicles=vehicles, active_vehicle=active_vehicle)

def get_active_vehicle_id():
    db = get_db()
    vid = session.get("active_vehicle_id")
    if vid:
        return vid
    # auto-select first vehicle
    rows = db.table("vehicles").select("id").order("created_at").limit(1).execute().data
    if rows:
        session["active_vehicle_id"] = rows[0]["id"]
        return rows[0]["id"]
    return None

# ── Vehicle management ─────────────────────────────────────────────────────────

@app.route("/vehicles")
def vehicles():
    db = get_db()
    all_vehicles = db.table("vehicles").select("*").order("created_at").execute().data
    return render_template("vehicles.html", all_vehicles=all_vehicles)

@app.route("/vehicles/add", methods=["POST"])
def add_vehicle():
    name = request.form.get("name", "").strip()
    plate = request.form.get("plate", "").strip()
    notes = request.form.get("notes", "").strip()
    if name:
        db = get_db()
        result = db.table("vehicles").insert({
            "name": name,
            "plate": plate or None,
            "notes": notes or None,
            "created_at": now_wib()
        }).execute()
        new_id = result.data[0]["id"]
        session["active_vehicle_id"] = new_id
        flash(f'Vehicle "{name}" added and selected.')
    return redirect(url_for("vehicles"))

@app.route("/vehicles/select/<int:vehicle_id>", methods=["POST"])
def select_vehicle(vehicle_id):
    session["active_vehicle_id"] = vehicle_id
    return redirect(request.referrer or url_for("index"))

@app.route("/vehicles/delete/<int:vehicle_id>", methods=["POST"])
def delete_vehicle(vehicle_id):
    db = get_db()
    db.table("vehicles").delete().eq("id", vehicle_id).execute()
    if session.get("active_vehicle_id") == vehicle_id:
        session.pop("active_vehicle_id", None)
    return redirect(url_for("vehicles"))

# ── Fuel consumption ───────────────────────────────────────────────────────────

@app.route("/")
def index():
    vid = get_active_vehicle_id()
    db = get_db()
    if vid:
        records = db.table("consumption").select("*").eq("vehicle_id", vid).order("created_at", desc=True).execute().data
    else:
        records = []
    return render_template("index.html", records=records)

@app.route("/add", methods=["GET", "POST"])
def add():
    vid = get_active_vehicle_id()
    if not vid:
        flash("Please add a vehicle first.")
        return redirect(url_for("vehicles"))

    if request.method == "POST":
        fuel_type = request.form.get("fuel_type")
        price = request.form.get("price")
        current_km = request.form.get("current_km")
        notes = request.form.get("notes", "")

        session["last_fuel_type"] = fuel_type

        db = get_db()
        last_rows = db.table("consumption").select("current_km").eq("vehicle_id", vid).order("created_at", desc=True).limit(1).execute().data
        distance = None
        if last_rows and last_rows[0]["current_km"]:
            distance = float(current_km) - float(last_rows[0]["current_km"])

        db.table("consumption").insert({
            "vehicle_id": vid,
            "fuel_type": fuel_type,
            "price": float(price),
            "current_km": float(current_km),
            "distance": distance,
            "notes": notes,
            "created_at": now_wib()
        }).execute()
        return redirect(url_for("index"))

    last_fuel_type = session.get("last_fuel_type", "Pertalite")
    return render_template("add.html", last_fuel_type=last_fuel_type)

@app.route("/delete/<int:record_id>", methods=["POST"])
def delete(record_id):
    db = get_db()
    db.table("consumption").delete().eq("id", record_id).execute()
    return redirect(url_for("index"))

# ── Mileage ────────────────────────────────────────────────────────────────────

@app.route("/mileage", methods=["GET", "POST"])
def mileage():
    vid = get_active_vehicle_id()
    if not vid:
        flash("Please add a vehicle first.")
        return redirect(url_for("vehicles"))

    db = get_db()
    if request.method == "POST":
        odometer_km = request.form.get("odometer_km")
        notes = request.form.get("notes", "")
        db.table("mileage").insert({
            "vehicle_id": vid,
            "odometer_km": float(odometer_km),
            "notes": notes,
            "recorded_at": now_wib()
        }).execute()
        return redirect(url_for("mileage"))

    records = db.table("mileage").select("*").eq("vehicle_id", vid).order("recorded_at", desc=True).execute().data
    return render_template("mileage.html", records=records)

@app.route("/mileage/delete/<int:record_id>", methods=["POST"])
def delete_mileage(record_id):
    db = get_db()
    db.table("mileage").delete().eq("id", record_id).execute()
    return redirect(url_for("mileage"))

# ── Stats ──────────────────────────────────────────────────────────────────────

@app.route("/stats")
def stats():
    vid = get_active_vehicle_id()
    db = get_db()

    if vid:
        records = db.table("consumption").select("*").eq("vehicle_id", vid).order("created_at").execute().data
        all_mileage = db.table("mileage").select("*").eq("vehicle_id", vid).order("recorded_at").execute().data
    else:
        records = []
        all_mileage = []

    total_spent = sum(r["price"] for r in records) if records else 0
    total_entries = len(records)

    by_type_map = {}
    for r in records:
        ft = r["fuel_type"]
        if ft not in by_type_map:
            by_type_map[ft] = {"fuel_type": ft, "count": 0, "total": 0}
        by_type_map[ft]["count"] += 1
        by_type_map[ft]["total"] += r["price"]
    by_type = list(by_type_map.values())

    date_map = {}
    for r in all_mileage:
        day = r["recorded_at"][:10]
        if day not in date_map:
            date_map[day] = []
        date_map[day].append(float(r["odometer_km"]))
    mileage_by_date = sorted([
        {"day": d, "start_km": min(v), "end_km": max(v),
         "distance": max(v) - min(v), "entries": len(v)}
        for d, v in date_map.items()
    ], key=lambda x: x["day"], reverse=True)

    month_map = {}
    for r in all_mileage:
        month = r["recorded_at"][:7]
        if month not in month_map:
            month_map[month] = []
        month_map[month].append(float(r["odometer_km"]))
    mileage_by_month = sorted([
        {"month": m, "start_km": min(v), "end_km": max(v),
         "distance": max(v) - min(v), "entries": len(v)}
        for m, v in month_map.items()
    ], key=lambda x: x["month"], reverse=True)

    range_from = request.args.get("range_from", "")
    range_to   = request.args.get("range_to", "")
    mileage_range = None
    if range_from and range_to:
        filtered = [float(r["odometer_km"]) for r in all_mileage
                    if range_from <= r["recorded_at"][:10] <= range_to]
        if filtered:
            mileage_range = {
                "start_km": min(filtered), "end_km": max(filtered),
                "distance": max(filtered) - min(filtered), "entries": len(filtered)
            }
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
