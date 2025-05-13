from fastapi import FastAPI, HTTPException, Response
import sqlite3
from datetime import datetime
from pathlib import Path

app = FastAPI()

DB_PATH = Path("salat.db")
CATEGORY_ID = 45


def minutes_to_hhmm(minutes: int) -> str:
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"


@app.get("/prayertimes/")
def get_prayer_times(
    date_str: str, output: str = "xml", category_id: int = CATEGORY_ID
):
    try:
        # Parse MM/DD/YYYY
        month, day, year = map(int, date_str.split("/"))
        date = datetime(year, month, day)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use MM/DD/YYYY"
        )

    # Convert to day-of-year (0-based index)
    day_of_year = (date - datetime(year, 1, 1)).days

    # Connect to DB and query
    if not DB_PATH.exists():
        raise HTTPException(status_code=500, detail="Database file not found.")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = """
    SELECT Fajuru, Dhuhr, Asr, Maghrib, Isha
    FROM PrayerTimes
    WHERE CategoryId = ? AND Date = ?
    """
    cursor.execute(query, (category_id, day_of_year))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(
            status_code=404, detail="Prayer times not found for this date"
        )

    # Map to prayer names and convert
    columns = ["fajr", "dhuhr", "asr", "maghrib", "isha"]
    prayer_times = dict(zip(columns, [minutes_to_hhmm(x) for x in row]))

    # Build XML
    xml_output = "<PrayerTimes>"
    for prayer_name in columns:
        capitalized = prayer_name.capitalize()
        xml_output += f"<{capitalized}>{prayer_times[prayer_name]}</{capitalized}>"
    xml_output += "</PrayerTimes>"

    if output == "json":
        return prayer_times
    return Response(
        content=xml_output,
        media_type="application/xml",
        headers={"Content-Disposition": "attachment; filename=prayer_times.xml"},
    )
