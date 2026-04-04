"""
DREAM-KG Location Enrichment Script
=====================================
What this does:
  1. Queries the DREAM-KG SPARQL endpoint for all services that have
     lat/lon coordinates but are missing city or postal code data.
  2. Uses the free OpenStreetMap Nominatim API (no key needed) to
     reverse geocode each coordinate pair into a city and postal code.
  3. Prints a report of what was found and saves results to a CSV file
     so you can share it with the research team.

"""

import requests
import csv
import time

# ── SPARQL endpoint ────────────────────────────────────────────────────────────
SPARQL_ENDPOINT = "https://frink.apps.renci.org/federation/sparql"

SPARQL_QUERY = """
PREFIX sdo: <http://schema.org/>
PREFIX dreamkg: <http://www.semanticweb.org/dreamkg/ijcai/>

SELECT ?service ?name ?lat ?lon WHERE {
  ?service sdo:latitude  ?lat ;
           sdo:longitude ?lon .
  OPTIONAL { ?service sdo:name ?name }
}
"""

# ── Nominatim reverse geocoding (free, no API key) ────────────────────────────
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
HEADERS = {"User-Agent": "DREAM-KG-enrichment-script/1.0 (research project)"}


def fetch_services():
    """Fetch all services with lat/lon from DREAM-KG."""
    print("Querying DREAM-KG for services with coordinates...")
    response = requests.get(
        SPARQL_ENDPOINT,
        params={"query": SPARQL_QUERY, "format": "json"},
        headers=HEADERS,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    results = data["results"]["bindings"]
    print(f"  Found {len(results)} services with coordinates.\n")
    return results


def reverse_geocode(lat, lon):
    """
    Given lat/lon, return (city, postal_code, full_address).
    Uses OpenStreetMap Nominatim — free, no API key required.
    Includes a 1-second delay to respect Nominatim's usage policy.
    """
    try:
        response = requests.get(
            NOMINATIM_URL,
            params={
                "lat": lat,
                "lon": lon,
                "format": "json",
                "addressdetails": 1,
            },
            headers=HEADERS,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        address = data.get("address", {})

        # City can be stored under different keys depending on location
        city = (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("county")
            or "Unknown"
        )
        postal_code = address.get("postcode", "Unknown")
        full_address = data.get("display_name", "Unknown")

        return city, postal_code, full_address

    except Exception as e:
        return "Error", "Error", str(e)


def clean_value(binding, key):
    """Safely extract a value from a SPARQL result binding."""
    return binding.get(key, {}).get("value", "").strip()


def main():
    # Step 1: Get all services with coordinates from DREAM-KG
    services = fetch_services()

    if not services:
        print("No services found. Check your SPARQL endpoint or query.")
        return

    results = []

    print(f"Reverse geocoding {len(services)} services using OpenStreetMap...")
    print("(This takes ~1 second per service to respect API rate limits)\n")

    for i, svc in enumerate(services, start=1):
        service_url = clean_value(svc, "service")
        name        = clean_value(svc, "name") or "(no name)"
        lat         = clean_value(svc, "lat")
        lon         = clean_value(svc, "lon")

        # Skip if coordinates are missing
        if not lat or not lon:
            continue

        city, postal_code, full_address = reverse_geocode(lat, lon)

        print(f"[{i}/{len(services)}] {name}")
        print(f"  Coords : {lat}, {lon}")
        print(f"  City   : {city}")
        print(f"  Zipcode: {postal_code}")
        print()

        results.append({
            "service_url":    service_url,
            "name":           name,
            "latitude":       lat,
            "longitude":      lon,
            "city":           city,
            "postal_code":    postal_code,
            "full_address":   full_address,
        })

        # Nominatim requires max 1 request/second
        time.sleep(1)

    # Step 2: Save results to CSV
    output_file = "dreamkg_location_enrichment.csv"
    fieldnames = ["service_url", "name", "latitude", "longitude",
                  "city", "postal_code", "full_address"]

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    # Step 3: Print summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    cities = {}
    for r in results:
        city = r["city"]
        cities[city] = cities.get(city, 0) + 1

    print(f"Total services processed : {len(results)}")
    print(f"Unique cities found      : {len(cities)}")
    print()
    print("Services per city:")
    for city, count in sorted(cities.items(), key=lambda x: -x[1]):
        print(f"  {city}: {count} service(s)")

    print()
    print(f"Full results saved to: {output_file}")
    print()
    


if __name__ == "__main__":
    main()
