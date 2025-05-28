#!/usr/bin/env python3
"""
Script pour forcer le redémarrage de l'app Streamlit Cloud
"""

import time
from datetime import datetime

# Créer un fichier timestamp pour forcer le redémarrage
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

with open('.streamlit/timestamp.txt', 'w') as f:
    f.write(f"Dernière modification: {timestamp}\n")
    f.write("Ce fichier force le redémarrage de Streamlit Cloud\n")

print(f"✅ Timestamp créé: {timestamp}")
print("🔄 Streamlit Cloud va redémarrer automatiquement") 