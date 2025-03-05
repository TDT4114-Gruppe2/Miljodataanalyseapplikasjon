import requests
import json

# Henter data fra met.no sin API
def hent_vaerdata(lat: float, lon: float):
    url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={lat}&lon={lon}"
    headers = {
        "User-Agent": "Miljødataanalyseapplikasjon"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)  # 10 sek timeout
        response.raise_for_status()  # Viser feil hvis statuskode er 4xx/5xx
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Feil ved henting av data: {e}")
        return None

# Henter data for Trondheim, og skriver data til fil hvis det finnes
data = hent_vaerdata(63.4305, 10.3951)
if data:
    with open("data/raw/vaerdata.json", "w") as f:
        json.dump(data, f, indent=4)
    print("Data lagret til data/raw/vaerdata.json")
else:
    print("Ingen data mottatt.")
