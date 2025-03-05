import json
import requests

# Konstant for User-Agent
USER_AGENT = "Miljødataanalyseapplikasjon"

def hent_vaerdata(lat: float, lon: float):
    """Henter værdata fra MET API basert på gitt bredde- og lengdegrad."""
    url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={lat}&lon={lon}"
    
    try:
        response = requests.get(url, timeout=10)  # 10 sek timeout
        response.raise_for_status()  # Sjekker HTTP-status
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Feil ved henting av data: {e}")
        return None

# Henter data for Trondheim og lagrer det til fil
data = hent_vaerdata(63.4305, 10.3951)
if data:
    with open("data/raw/vaerdata.json", "w") as f:
        json.dump(data, f, indent=4)
    print("Data lagret til data/raw/vaerdata.json")
else:
    print("Ingen data mottatt.")
