import os
import sys
import importlib.util
from pathlib import Path

# Legg til prosjektroten i Python's søkesti
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))

# Funksjon for å opprette en "fake" modul fra en fil
def create_module_from_file(module_name, file_path):
    if os.path.exists(file_path):
        # Lag en spec for modulen
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        
        # Registrer modulen i sys.modules slik at import fungerer
        sys.modules[module_name] = module
        
        # Utfør modulen for å laste inn dens innhold
        spec.loader.exec_module(module)
        
        print(f"Opprettet {module_name}-modul for testing")
        return True
    return False

# Opprett basedata-modulen
basedata_path = os.path.join(project_root, "src", "analysis", "basedata.py")
create_module_from_file("basedata", basedata_path)

# Opprett outlierdetector-modulen - prøv å finne den i src/analysis først
outlierdetector_path = os.path.join(project_root, "src", "analysis", "outlierdetector.py")
if not create_module_from_file("outlierdetector", outlierdetector_path):
    # Hvis ikke funnet i src/analysis, prøv i src
    outlierdetector_path = os.path.join(project_root, "src", "outlierdetector.py")
    create_module_from_file("outlierdetector", outlierdetector_path)