from fastapi import FastAPI, HTTPException, Response
from bs4 import BeautifulSoup
import httpx
from datetime import datetime
from database import init_db, get_cached_prayer_times, save_prayer_times

app = FastAPI()

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

ISLAND_ID = 89
BASE_URL = "https://namaadhuvaguthu.com/en/prayertimes/{island_id}/{year}/{month:02d}/{day:02d}"


@app.get("/prayertimes/")
async def get_prayer_times(date_input: str, output: str = "xml"):
    try:
        month, day, year = map(int, date_input.split("/"))
        # Validate date using datetime to catch invalid dates like 02/30/YYYY
        datetime(year, month, day)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format or date is out of range. Use MM/DD/YYYY and a valid date.",
        )

    # Create standardized date key for caching (YYYY-MM-DD format)
    date_key = f"{year:04d}-{month:02d}-{day:02d}"

    # Check cache first
    cached_data = get_cached_prayer_times(date_key)
    if cached_data:
        prayer_times = cached_data
    else:
        # Cache miss - scrape the data
        url = BASE_URL.format(island_id=ISLAND_ID, year=year, day=day, month=month)
        # print(f"URL -> {url}") # Uncomment for debugging if needed

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url)
                response.raise_for_status()  # Raises HTTPStatusError for 4xx/5xx responses
                # print(f"Response Status -> {response.status_code}") # Uncomment for debugging
            except httpx.TimeoutException:
                raise HTTPException(
                    status_code=504, detail="Request to prayer times service timed out."
                )
            except httpx.RequestError as exc:
                # This catches other network errors, DNS failures, etc.
                raise HTTPException(
                    status_code=503,
                    detail=f"Error connecting to prayer times service: {exc}",
                )

        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", class_="prayertimes-single-day")

        if not table:
            raise HTTPException(
                status_code=404,
                detail="Prayer times table not found on the page. The website structure might have changed.",
            )

        prayer_times = {}

        # table.find_all should return a list of Tag objects if table is a Tag
        # The type: ignore was present in your example, suggesting potential linter issues with bs4
        rows = table.find_all("tr")  # type: ignore
        if not rows:
            raise HTTPException(
                status_code=404, detail="No rows found in the prayer times table."
            )

        for row_element in rows:
            # Ensure row_element is a Tag and has the find method
            if not hasattr(row_element, "find"):
                continue

            name_tag = row_element.find("th", class_="prayer-name")  # type: ignore
            time_tag = row_element.find("td", class_="prayer-time")  # type: ignore

            if (
                name_tag
                and time_tag
                and hasattr(name_tag, "text")
                and hasattr(time_tag, "text")
            ):
                name = name_tag.text.strip().lower()
                time = time_tag.text.strip()

                if name == "fajr":
                    prayer_times["fajr"] = time
                elif name in ["duhr", "dhuhr"]:  # site may use either spelling
                    prayer_times["dhuhr"] = time
                elif name == "asr":
                    prayer_times["asr"] = time
                elif name == "maghrib":
                    prayer_times["maghrib"] = time
                elif name == "isha":
                    prayer_times["isha"] = time
                # Other prayer names like 'sunrise' are ignored for the final XML

        required_prayers = ["fajr", "dhuhr", "asr", "maghrib", "isha"]
        missing_prayers = [p for p in required_prayers if p not in prayer_times]

        if missing_prayers:
            raise HTTPException(
                status_code=404,
                detail=f"Could not parse all required prayer times. Missing: {', '.join(missing_prayers)}",
            )

        # Save to cache
        save_prayer_times(date_key, prayer_times)

    # Build XML output
    xml_output = "<PrayerTimes>"
    # Ensure consistent order for XML
    ordered_prayers = ["fajr", "dhuhr", "asr", "maghrib", "isha"]
    for prayer_name in ordered_prayers:
        if prayer_name in prayer_times:
            capitalized_prayer_name = prayer_name.capitalize()
            xml_output += f"<{capitalized_prayer_name}>{prayer_times[prayer_name]}</{capitalized_prayer_name}>"
    xml_output += "</PrayerTimes>"

    if output == "json":
        return {
            "fajr": prayer_times["fajr"],
            "dhuhr": prayer_times["dhuhr"],
            "asr": prayer_times["asr"],
            "maghrib": prayer_times["maghrib"],
            "isha": prayer_times["isha"],
        }

    return Response(
        content=xml_output,
        media_type="application/xml",
        headers={"Content-Disposition": "attachment; filename=prayer_times.xml"},
    )


# If you want to run this locally:
# uvicorn main:app --reload
