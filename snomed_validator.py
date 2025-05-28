#!/usr/bin/env python3
"""
Validateur SNOMED CT utilisant la distribution officielle française
Distribution: terminologie-snomed-ct-fr-Juin 2024 v1.0 (1)
"""

import csv
import os
from typing import Dict, Set, Optional, Tuple
from pathlib import Path

class SNOMEDValidator:
    """Validateur de codes SNOMED CT basé sur la distribution officielle française"""
    
    def __init__(self, snomed_base_path: Optional[str] = None):
        """
        Initialiser le validateur
        
        Args:
            snomed_base_path: Chemin vers le dossier SNOMED CT. 
                             Si None, utilise le chemin par défaut dans Downloads
        """
        if snomed_base_path is None:
            # Chemin par défaut vers le dossier SNOMED CT
            home = Path.home()
            snomed_base_path = home / "Downloads" / "terminologie-snomed-ct-fr-Juin 2024 v1.0 (1)"
        
        self.snomed_path = Path(snomed_base_path)
        self.snapshot_path = self._find_snapshot_path()
        
        # Dictionnaires pour stocker les données chargées
        self.valid_concepts: Set[str] = set()  # SCTID valides
        self.french_terms: Dict[str, str] = {}  # SCTID -> terme français préféré
        self.term_to_code: Dict[str, str] = {}  # terme_lower -> SCTID
        
        # Flag pour savoir si les données sont chargées
        self._loaded = False
    
    def _find_snapshot_path(self) -> Optional[Path]:
        """Trouver le chemin vers les fichiers Snapshot"""
        try:
            # Chercher le dossier avec la structure attendue
            src_path = self.snomed_path / "src"
            if not src_path.exists():
                print(f"❌ Dossier src non trouvé dans {self.snomed_path}")
                return None
            
            # Trouver le dossier de production (nom peut varier)
            production_dirs = list(src_path.glob("SnomedCT_*"))
            if not production_dirs:
                print(f"❌ Aucun dossier de production trouvé dans {src_path}")
                return None
            
            # Filtrer pour prendre seulement les dossiers (pas les fichiers .zip)
            production_dirs = [p for p in production_dirs if p.is_dir()]
            if not production_dirs:
                print(f"❌ Aucun dossier de production valide trouvé dans {src_path}")
                return None
            
            production_path = production_dirs[0]
            snapshot_path = production_path / "Snapshot" / "Terminology"
            
            if snapshot_path.exists():
                return snapshot_path
            else:
                print(f"❌ Dossier Snapshot/Terminology non trouvé dans {production_path}")
                return None
                
        except Exception as e:
            print(f"❌ Erreur lors de la recherche du chemin Snapshot : {e}")
            return None
    
    def load_snomed_data(self) -> bool:
        """Charger les données SNOMED CT depuis les fichiers officiels"""
        if self._loaded:
            return True
        
        if not self.snapshot_path:
            print("❌ Chemin Snapshot non trouvé")
            return False
        
        print(f"🔍 Chargement des données SNOMED CT depuis {self.snapshot_path}...")
        
        # Charger les concepts valides
        concepts_loaded = self._load_concepts()
        if not concepts_loaded:
            return False
        
        # Charger les descriptions françaises
        descriptions_loaded = self._load_french_descriptions()
        if not descriptions_loaded:
            return False
        
        self._loaded = True
        print(f"✅ Données SNOMED CT chargées : {len(self.valid_concepts)} concepts, {len(self.french_terms)} termes français")
        return True
    
    def _load_concepts(self) -> bool:
        """Charger la liste des concepts valides (actifs)"""
        try:
            # Trouver le fichier de concepts
            concept_files = list(self.snapshot_path.glob("sct2_Concept_Snapshot_*.txt"))
            if not concept_files:
                print("❌ Fichier de concepts non trouvé")
                return False
            
            concept_file = concept_files[0]
            print(f"📄 Chargement des concepts depuis {concept_file.name}")
            
            with open(concept_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='\t')
                for row in reader:
                    if row['active'] == '1':  # Concepts actifs uniquement
                        self.valid_concepts.add(row['id'])
            
            print(f"✅ {len(self.valid_concepts)} concepts actifs chargés")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors du chargement des concepts : {e}")
            return False
    
    def _load_french_descriptions(self) -> bool:
        """Charger les descriptions françaises"""
        try:
            # Trouver le fichier de descriptions françaises
            desc_files = list(self.snapshot_path.glob("sct2_Description_Snapshot-fr_*.txt"))
            if not desc_files:
                print("❌ Fichier de descriptions françaises non trouvé")
                return False
            
            desc_file = desc_files[0]
            print(f"📄 Chargement des descriptions françaises depuis {desc_file.name}")
            
            with open(desc_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='\t')
                for row in reader:
                    if row['active'] == '1' and row['languageCode'] == 'fr':
                        concept_id = row['conceptId']
                        term = row['term']
                        
                        # Stocker le premier terme trouvé pour chaque concept
                        # (une version plus sophistiquée utiliserait le Language Refset pour le terme préféré)
                        if concept_id not in self.french_terms:
                            self.french_terms[concept_id] = term
                            self.term_to_code[term.lower().strip()] = concept_id
            
            print(f"✅ {len(self.french_terms)} termes français chargés")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors du chargement des descriptions françaises : {e}")
            return False
    
    def validate_code(self, sctid: str) -> bool:
        """
        Valider qu'un code SCTID existe et est actif
        
        Args:
            sctid: Le code SNOMED CT à valider
            
        Returns:
            True si le code est valide et actif
        """
        if not self._loaded:
            if not self.load_snomed_data():
                return False
        
        return sctid in self.valid_concepts
    
    def get_french_term(self, sctid: str) -> Optional[str]:
        """
        Obtenir le terme français officiel pour un code SCTID
        
        Args:
            sctid: Le code SNOMED CT
            
        Returns:
            Le terme français officiel ou None si non trouvé
        """
        if not self._loaded:
            if not self.load_snomed_data():
                return None
        
        return self.french_terms.get(sctid)
    
    def find_code_by_term(self, term: str) -> Optional[str]:
        """
        Trouver un code SCTID à partir d'un terme français
        
        Args:
            term: Le terme français à rechercher
            
        Returns:
            Le code SCTID correspondant ou None si non trouvé
        """
        if not self._loaded:
            if not self.load_snomed_data():
                return None
        
        return self.term_to_code.get(term.lower().strip())
    
    def validate_extraction_result(self, extraction_result) -> Dict:
        """
        Valider tous les codes d'un résultat d'extraction SNOMED CT
        
        Args:
            extraction_result: Objet SNOMEDExtraction
            
        Returns:
            Dictionnaire avec les statistiques de validation
        """
        if not self._loaded:
            if not self.load_snomed_data():
                return {"error": "Impossible de charger les données SNOMED CT"}
        
        stats = {
            "total_codes": 0,
            "valid_codes": 0,
            "invalid_codes": 0,
            "unknown_codes": 0,
            "validation_details": []
        }
        
        # Valider toutes les catégories
        all_items = (
            extraction_result.clinical_findings + 
            extraction_result.procedures + 
            extraction_result.body_structures
        )
        
        for item in all_items:
            if hasattr(item, 'snomed_code') and item.snomed_code:
                stats["total_codes"] += 1
                
                if item.snomed_code == "UNKNOWN":
                    stats["unknown_codes"] += 1
                    status = "UNKNOWN"
                elif self.validate_code(item.snomed_code):
                    stats["valid_codes"] += 1
                    status = "VALID"
                    official_term = self.get_french_term(item.snomed_code)
                else:
                    stats["invalid_codes"] += 1
                    status = "INVALID"
                    official_term = None
                
                stats["validation_details"].append({
                    "term": item.term,
                    "gemini_code": item.snomed_code,
                    "status": status,
                    "official_term": official_term if status == "VALID" else None
                })
        
        return stats

def test_validator():
    """Fonction de test du validateur"""
    print("🧪 Test du validateur SNOMED CT...")
    
    validator = SNOMEDValidator()
    
    # Test de chargement
    if not validator.load_snomed_data():
        print("❌ Échec du chargement des données")
        return
    
    # Test avec quelques codes connus
    test_codes = [
        "38907003",  # Varicelle (si ce code existe)
        "271807003", # Éruption cutanée (si ce code existe)
        "999999999", # Code inexistant
        "UNKNOWN"    # Code inconnu
    ]
    
    print("\n🔍 Test de validation de codes :")
    for code in test_codes:
        is_valid = validator.validate_code(code)
        french_term = validator.get_french_term(code) if is_valid else None
        print(f"   {code}: {'✅ VALIDE' if is_valid else '❌ INVALIDE'}")
        if french_term:
            print(f"      → Terme officiel: {french_term}")

if __name__ == "__main__":
    test_validator() 