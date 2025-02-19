import requests

def hent_vaerdata(lat: float, lon: float):
    url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={lat}&lon={lon}"
    headers = {
        "User-Agent": "Miljødataanalyseapplikasjon/1.0"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Feil ved henting av data: {response.status_code}")
        return None

# Tester for Trondheim
data = hent_vaerdata(63.4305, 10.3951)
print(data)
