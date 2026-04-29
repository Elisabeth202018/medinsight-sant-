"""
backend.py — MedInsight Health Data Platform
============================================
Couche métier : gestion des données, calculs cliniques,
algorithmes de risque, alertes automatiques.

Aucune dépendance Streamlit ici — ce fichier est 100% réutilisable.
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ══════════════════════════════════════════════════════════════════════════════

DATA_FILE = "medinsight_data.csv"

COLUMNS = [
    "id", "date_collecte", "nom_patient", "age", "sexe", "region",
    "poids_kg", "taille_cm", "imc", "categorie_imc",
    "tension_sys", "tension_dia", "categorie_ta",
    "glycemie", "categorie_glycemie",
    "temperature", "frequence_cardiaque", "spo2",
    "fumeur", "alcool", "activite",
    "antecedents", "diagnostic", "traitement", "notes",
    "score_risque", "niveau_risque",
]

REGIONS = [
    "Centre (Yaoundé)", "Littoral (Douala)", "Ouest", "Nord-Ouest",
    "Sud-Ouest", "Adamaoua", "Nord", "Extrême-Nord", "Est", "Sud", "Autre",
]

NIVEAUX_RISQUE_ORDRE = ["Faible", "Modéré", "Élevé", "Très élevé"]

CATEGORIES_TA_ORDRE = [
    "Optimale", "Normale", "Normale haute",
    "HTA grade 1", "HTA grade 2", "HTA grade 3",
]


# ══════════════════════════════════════════════════════════════════════════════
# CLASSE PRINCIPALE — DataManager
# ══════════════════════════════════════════════════════════════════════════════

class DataManager:
    """Gère la persistance et l'accès aux données patients."""

    def __init__(self, filepath: str = DATA_FILE):
        self.filepath = filepath

    def load(self) -> pd.DataFrame:
        """
        Charge les données depuis le fichier JSON (persistant sur disque).
        Fallback sur CSV si présent. Retourne un DataFrame vide sinon.
        """
        json_path = self.filepath.replace(".csv", ".json")

        # Priorité : JSON (survit aux redémarrages Streamlit Cloud)
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    records = json.load(f)
                df = pd.DataFrame(records)
            except (json.JSONDecodeError, Exception):
                df = pd.DataFrame(columns=COLUMNS)

        # Fallback : CSV legacy
        elif os.path.exists(self.filepath):
            df = pd.read_csv(self.filepath)

        else:
            return pd.DataFrame(columns=COLUMNS)

        # Garantit que toutes les colonnes existent
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = np.nan
        return df

    def save(self, df: pd.DataFrame) -> None:
        """Sauvegarde en JSON ET en CSV (double persistance)."""
        # JSON — format principal (plus fiable sur cloud)
        json_path = self.filepath.replace(".csv", ".json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(df.to_dict(orient="records"), f, ensure_ascii=False, indent=2)
        # CSV — backup lisible
        df.to_csv(self.filepath, index=False)

    def add_patient(self, patient_dict: dict) -> pd.DataFrame:
        """Ajoute un patient et retourne le DataFrame mis à jour."""
        df = self.load()
        new_id = f"MED-{len(df) + 1:04d}"
        patient_dict["id"] = new_id
        patient_dict["date_collecte"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        df = pd.concat([df, pd.DataFrame([patient_dict])], ignore_index=True)
        self.save(df)
        return df

    def get_patient(self, patient_id: str) -> dict:
        """Retourne les données d'un patient par son ID."""
        df = self.load()
        row = df[df["id"] == patient_id]
        if len(row) == 0:
            raise ValueError(f"Patient {patient_id} introuvable.")
        return row.iloc[0].to_dict()

    def clear(self) -> None:
        """Vide entièrement la base de données."""
        self.save(pd.DataFrame(columns=COLUMNS))

    def count(self) -> int:
        """Retourne le nombre de patients enregistrés."""
        return len(self.load())

    def high_risk_count(self) -> int:
        """Retourne le nombre de profils à risque élevé ou très élevé."""
        df = self.load()
        if len(df) == 0 or "niveau_risque" not in df.columns:
            return 0
        return int(df["niveau_risque"].isin(["Élevé", "Très élevé"]).sum())

    def filter(
        self,
        df: pd.DataFrame,
        sexe_list: list = None,
        risk_list: list = None,
        age_range: tuple = None,
    ) -> pd.DataFrame:
        """Applique des filtres sur le DataFrame."""
        mask = pd.Series([True] * len(df), index=df.index)
        if sexe_list and "sexe" in df.columns:
            mask &= df["sexe"].isin(sexe_list)
        if risk_list and "niveau_risque" in df.columns:
            mask &= df["niveau_risque"].isin(risk_list)
        if age_range and "age" in df.columns and df["age"].notna().sum() > 0:
            mask &= (df["age"] >= age_range[0]) & (df["age"] <= age_range[1])
        return df[mask]

    def export_csv(self, df: pd.DataFrame) -> bytes:
        """Exporte un DataFrame en bytes CSV."""
        return df.to_csv(index=False).encode("utf-8")

    def export_json(self, df: pd.DataFrame) -> bytes:
        """Exporte un DataFrame en bytes JSON."""
        return df.to_json(orient="records", force_ascii=False, indent=2).encode("utf-8")

    def get_numeric_columns(self, df: pd.DataFrame) -> list:
        """Retourne les colonnes numériques disponibles pour les analyses."""
        candidates = [
            "age", "poids_kg", "taille_cm", "imc",
            "tension_sys", "tension_dia", "glycemie",
            "temperature", "frequence_cardiaque", "spo2", "score_risque",
        ]
        return [c for c in candidates if c in df.columns and df[c].notna().sum() > 0]

    def get_categorical_columns(self, df: pd.DataFrame) -> list:
        """Retourne les colonnes catégorielles disponibles."""
        candidates = [
            "sexe", "region", "categorie_imc", "categorie_ta",
            "categorie_glycemie", "fumeur", "alcool", "activite", "niveau_risque",
        ]
        return [c for c in candidates if c in df.columns and df[c].notna().sum() > 0]

    def summary_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule les statistiques descriptives résumées."""
        num_cols = self.get_numeric_columns(df)
        stats = df[num_cols].describe().T.round(2)
        stats.columns = ["n", "Moyenne", "Écart-type", "Min", "Q25%", "Médiane", "Q75%", "Max"]
        return stats

    def region_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule les statistiques agrégées par région."""
        if "region" not in df.columns:
            return pd.DataFrame()
        return (
            df.groupby("region")
            .agg(
                Patients=("nom_patient", "count"),
                IMC_moyen=("imc", "mean"),
                Tension_moy=("tension_sys", "mean"),
                Score_risque=("score_risque", "mean"),
            )
            .round(1)
            .sort_values("Patients", ascending=False)
        )

    def risk_means_by_level(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule les moyennes des facteurs de risque par niveau."""
        if "niveau_risque" not in df.columns or len(df) < 2:
            return pd.DataFrame()
        return df.groupby("niveau_risque")[
            ["age", "imc", "tension_sys", "glycemie"]
        ].mean().round(1)


# ══════════════════════════════════════════════════════════════════════════════
# CLASSE — ClinicalEngine (calculs médicaux)
# ══════════════════════════════════════════════════════════════════════════════

class ClinicalEngine:
    """Moteur de calcul clinique : IMC, tension, risque CV, alertes."""

    # ── Validation des saisies ────────────────────────────────────────────────

    # Bornes cliniques réalistes (min, max) pour chaque paramètre vital
    CLINICAL_BOUNDS = {
        "poids_kg":           (3,    300,  "Poids"),
        "taille_cm":          (50,   250,  "Taille"),
        "tension_sys":        (60,   260,  "Tension systolique"),
        "tension_dia":        (30,   160,  "Tension diastolique"),
        "glycemie":           (2.0,  35.0, "Glycémie"),
        "temperature":        (34.0, 42.5, "Température"),
        "frequence_cardiaque":(25,   220,  "Fréquence cardiaque"),
        "spo2":               (70,   100,  "SpO₂"),
        "age":                (0,    120,  "Âge"),
    }

    @classmethod
    def validate(cls, **kwargs) -> list[str]:
        """
        Valide les paramètres vitaux selon les bornes cliniques réalistes.
        Retourne une liste d'erreurs (vide = tout est valide).
        """
        errors = []
        for field, value in kwargs.items():
            if field in cls.CLINICAL_BOUNDS:
                vmin, vmax, label = cls.CLINICAL_BOUNDS[field]
                if not (vmin <= float(value) <= vmax):
                    errors.append(f"**{label}** : valeur `{value}` hors plage clinique [{vmin} – {vmax}]")
        # Cohérence tension sys > dia
        if "tension_sys" in kwargs and "tension_dia" in kwargs:
            if float(kwargs["tension_sys"]) <= float(kwargs["tension_dia"]):
                errors.append("**Tension** : la systolique doit être supérieure à la diastolique")
        return errors

    # ── IMC ──────────────────────────────────────────────────────────────────

    @staticmethod
    def compute_imc(poids_kg: float, taille_cm: float) -> float:
        """Calcule l'Indice de Masse Corporelle."""
        if taille_cm <= 0:
            return 0.0
        return round(poids_kg / (taille_cm / 100) ** 2, 1)

    @staticmethod
    def imc_category(imc: float) -> str:
        """Retourne la catégorie OMS pour un IMC donné."""
        if imc < 16:    return "Maigreur sévère"
        if imc < 18.5:  return "Insuffisance pondérale"
        if imc < 25:    return "Poids normal"
        if imc < 30:    return "Surpoids"
        if imc < 35:    return "Obésité modérée"
        return "Obésité sévère"

    # ── Tension artérielle ────────────────────────────────────────────────────

    @staticmethod
    def ta_category(systolique: int, diastolique: int) -> str:
        """Classifie la tension artérielle selon les recommandations ESC."""
        if systolique < 120 and diastolique < 80:   return "Optimale"
        if systolique < 130 and diastolique < 80:   return "Normale"
        if systolique < 140 or diastolique < 90:    return "Normale haute"
        if systolique < 160 or diastolique < 100:   return "HTA grade 1"
        if systolique < 180 or diastolique < 110:   return "HTA grade 2"
        return "HTA grade 3"

    # ── Glycémie ──────────────────────────────────────────────────────────────

    @staticmethod
    def glycemia_category(glycemie_mmol: float) -> str:
        """Classifie la glycémie à jeun (mmol/L)."""
        if glycemie_mmol < 3.9:   return "Hypoglycémie"
        if glycemie_mmol <= 6.1:  return "Normale"
        if glycemie_mmol <= 7.0:  return "Pré-diabète"
        return "Hyperglycémie"

    # ── Score de risque cardiovasculaire ─────────────────────────────────────

    @staticmethod
    def cardiovascular_risk_score(
        age: int,
        sexe: str,
        imc: float,
        tension_sys: int,
        glycemie: float,
        fumeur: str,
        activite: str,
        antecedents: str = "",
    ) -> int:
        """
        Calcule un score de risque cardiovasculaire simplifié (0–100)
        inspiré du modèle de Framingham.

        Facteurs pris en compte :
        - Âge, Sexe, IMC, Tension systolique
        - Glycémie, Tabagisme, Activité physique, Antécédents
        """
        score = 0

        # Âge
        if age >= 65:    score += 25
        elif age >= 55:  score += 18
        elif age >= 45:  score += 12
        elif age >= 35:  score += 6

        # Sexe masculin légèrement plus à risque
        if sexe == "Masculin":
            score += 5

        # IMC
        if imc >= 35:    score += 18
        elif imc >= 30:  score += 12
        elif imc >= 25:  score += 6

        # Tension systolique
        if tension_sys >= 180:    score += 22
        elif tension_sys >= 160:  score += 16
        elif tension_sys >= 140:  score += 10
        elif tension_sys >= 130:  score += 5

        # Glycémie
        if glycemie > 7.0:    score += 14
        elif glycemie > 6.1:  score += 7

        # Tabagisme
        if fumeur == "Fumeur actif":  score += 15
        elif fumeur == "Ex-fumeur":   score += 5

        # Sédentarité
        if activite == "Sédentaire":  score += 8
        elif activite == "Légère":    score += 4

        # Antécédents cardiovasculaires / métaboliques
        if antecedents:
            keywords = ["diabète", "diabete", "hypertension", "infarctus", "avc", "coronaire"]
            if any(kw in antecedents.lower() for kw in keywords):
                score += 10

        return min(score, 100)

    @staticmethod
    def risk_level(score: int) -> str:
        """Traduit un score numérique en niveau de risque qualitatif."""
        if score < 25:  return "Faible"
        if score < 50:  return "Modéré"
        if score < 70:  return "Élevé"
        return "Très élevé"

    @staticmethod
    def risk_css_class(level: str) -> str:
        """Retourne la classe CSS correspondant au niveau de risque."""
        mapping = {
            "Faible":     "risk-low",
            "Modéré":     "risk-medium",
            "Élevé":      "risk-high",
            "Très élevé": "risk-high",
        }
        return mapping.get(level, "risk-low")

    # ── Alertes cliniques ─────────────────────────────────────────────────────

    @staticmethod
    def clinical_alerts(row: dict) -> list[tuple[str, str]]:
        """
        Génère la liste des alertes cliniques pour un patient.

        Retourne une liste de tuples (niveau, message) :
        - niveau : "danger" | "warn" | "ok"
        - message : texte de l'alerte avec emoji
        """
        alerts = []

        # Tension artérielle
        sys = float(row.get("tension_sys", 0))
        dia = float(row.get("tension_dia", 0))
        if sys >= 140:
            alerts.append(("danger", f"⚠️ Hypertension artérielle ({sys:.0f}/{dia:.0f} mmHg)"))
        elif sys >= 130:
            alerts.append(("warn", f"⚡ Tension normale haute ({sys:.0f}/{dia:.0f} mmHg)"))

        # Glycémie
        glyc = float(row.get("glycemie", 5))
        if glyc > 7.0:
            alerts.append(("danger", f"🩸 Hyperglycémie ({glyc} mmol/L)"))
        elif glyc > 6.1:
            alerts.append(("warn", f"🩸 Pré-diabète ({glyc} mmol/L)"))
        elif glyc < 3.9:
            alerts.append(("danger", f"🩸 Hypoglycémie ({glyc} mmol/L)"))

        # IMC
        imc = float(row.get("imc", 22))
        if imc >= 35:
            alerts.append(("danger", f"⚖️ Obésité sévère (IMC {imc})"))
        elif imc >= 30:
            alerts.append(("warn", f"⚖️ Obésité (IMC {imc})"))
        elif imc < 18.5:
            alerts.append(("warn", f"⚖️ Insuffisance pondérale (IMC {imc})"))

        # Température
        temp = float(row.get("temperature", 37))
        if temp >= 38.5:
            alerts.append(("danger", f"🌡️ Fièvre élevée ({temp}°C)"))
        elif temp >= 37.5:
            alerts.append(("warn", f"🌡️ Fièvre légère ({temp}°C)"))

        # SpO₂
        spo2 = float(row.get("spo2", 98))
        if spo2 < 92:
            alerts.append(("danger", f"💨 Hypoxémie critique (SpO₂ {spo2:.0f}%)"))
        elif spo2 < 95:
            alerts.append(("warn", f"💨 Saturation basse (SpO₂ {spo2:.0f}%)"))

        # Fréquence cardiaque
        fc = float(row.get("frequence_cardiaque", 72))
        if fc > 100:
            alerts.append(("warn", f"💓 Tachycardie ({fc:.0f} bpm)"))
        elif fc < 60:
            alerts.append(("warn", f"💓 Bradycardie ({fc:.0f} bpm)"))

        # Aucune alerte → bilan positif
        if not alerts:
            alerts.append(("ok", "✅ Tous les paramètres sont dans les limites normales"))

        return alerts

    # ── Construction d'un enregistrement complet ──────────────────────────────

    @classmethod
    def build_patient_record(
        cls,
        nom: str,
        age: int,
        sexe: str,
        region: str,
        poids: float,
        taille: float,
        t_sys: int,
        t_dia: int,
        glyc: float,
        temp: float,
        spo2: int,
        fc: int,
        fumeur: str,
        alcool: str,
        activite: str,
        antecedents: str,
        diagnostic: str,
        traitement: str,
        notes: str,
        existing_count: int,
    ) -> dict:
        """
        Assemble un dictionnaire patient complet avec tous les champs
        calculés (IMC, catégories, score de risque, etc.).
        """
        imc_val   = cls.compute_imc(poids, taille)
        score     = cls.cardiovascular_risk_score(age, sexe, imc_val, t_sys, glyc, fumeur, activite, antecedents)
        niveau    = cls.risk_level(score)

        return {
            "id":               f"MED-{existing_count + 1:04d}",
            "date_collecte":    datetime.now().strftime("%Y-%m-%d %H:%M"),
            "nom_patient":      nom.strip(),
            "age":              age,
            "sexe":             sexe,
            "region":           region,
            "poids_kg":         poids,
            "taille_cm":        taille,
            "imc":              imc_val,
            "categorie_imc":    cls.imc_category(imc_val),
            "tension_sys":      t_sys,
            "tension_dia":      t_dia,
            "categorie_ta":     cls.ta_category(t_sys, t_dia),
            "glycemie":         glyc,
            "categorie_glycemie": cls.glycemia_category(glyc),
            "temperature":      temp,
            "frequence_cardiaque": fc,
            "spo2":             spo2,
            "fumeur":           fumeur,
            "alcool":           alcool,
            "activite":         activite,
            "antecedents":      antecedents,
            "diagnostic":       diagnostic,
            "traitement":       traitement,
            "notes":            notes,
            "score_risque":     score,
            "niveau_risque":    niveau,
        }


# ══════════════════════════════════════════════════════════════════════════════
# INSTANCES PRÊTES À L'EMPLOI (importables directement dans app.py)
# ══════════════════════════════════════════════════════════════════════════════

db     = DataManager()
engine = ClinicalEngine()