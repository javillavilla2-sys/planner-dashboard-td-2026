"""
Dashboard Ejecutivo - Gestión de Requerimientos Microsoft Planner
Arquitecto: Senior Python & Streamlit Developer
Versión: 2.0.0
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, date
import re
import io
import json
import os
import csv
import warnings
from pathlib import Path

# PDF generation
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors as rl_colors
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak,
)
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN GLOBAL
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard TD 2026 · Planner Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Paleta corporativa
COLORS = {
    "primary":   "#1d6af5",
    "green":     "#0da063",
    "red":       "#e03030",
    "yellow":    "#d97706",
    "purple":    "#6d28d9",
    "cyan":      "#0891b2",
    "orange":    "#ea580c",
    "gray":      "#64748b",
    "bg":        "#f4f6fb",
    "card":      "#ffffff",
}

CATEGORY_COLORS = {
    "Excelencia ERP":         "#1d6af5",
    "Eficiencia Operativa":   "#0da063",
    "Seguridad de la Información": "#e03030",
    "Datos Confiables":       "#6d28d9",
    "Integración":            "#0891b2",
    "Sin clasificar":         "#94a3b8",
}

PROGRESS_MAP = {
    "completado":   "Completado",
    "en curso":     "En curso",
    "no iniciado":  "No iniciado",
    "completed":    "Completado",
    "in progress":  "En curso",
    "not started":  "No iniciado",
}

# ─────────────────────────────────────────────────────────────────────────────
# REQ 3 & 4: CAPA DE PERSISTENCIA — JSON + CSV histórico
# ─────────────────────────────────────────────────────────────────────────────
# Rutas de persistencia — compatibles con Streamlit Cloud y local
_DATA_DIR         = Path("data")
_KPI_FILE         = _DATA_DIR / "strategic_kpis.json"
_HISTORY_FILE     = _DATA_DIR / "strategic_history.csv"
_HISTORY_COLS     = ["fecha", "objetivo", "meta", "avance"]

# Mapeo interno _sd ↔ nombre de objetivo
_OBJ_SD_MAP = {
    "Eficiencia Operativa":        ("eo_meta",  "eo_completados"),
    "Datos Confiables":            ("dc_meta",  "dc_completados"),
    "Excelencia ERP":              ("erp_meta", "erp_completados"),
    "Integración":                 ("int_meta", "int_completadas"),
    "Seguridad de la Información": ("seg_meta", "seg_completados"),
}


def _ensure_data_dir():
    """Crea el directorio data/ si no existe. Silencia errores en entornos read-only."""
    try:
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass


def load_kpis_from_json() -> dict | None:
    """
    REQ 3: Carga metas y avances desde data/strategic_kpis.json.
    Retorna None si el archivo no existe o está corrupto.

    Estructura del JSON:
    {
      "Eficiencia Operativa": {"meta": 20, "avance": 12},
      ...
    }
    """
    try:
        if not _KPI_FILE.exists():
            return None
        with _KPI_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        # Validación básica
        if not isinstance(data, dict):
            return None
        return data
    except Exception:
        return None


def save_kpis_to_json(sd: dict):
    """
    REQ 3: Guarda las metas y avances actuales en data/strategic_kpis.json.
    Solo escribe si el directorio es escribible.
    """
    _ensure_data_dir()
    payload = {}
    for obj, (meta_k, comp_k) in _OBJ_SD_MAP.items():
        payload[obj] = {
            "meta":   int(sd.get(meta_k, 1)),
            "avance": int(sd.get(comp_k, 0)),
        }
    try:
        with _KPI_FILE.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


def append_history_row(sd: dict):
    """
    REQ 4: Añade una fila al CSV histórico por cada objetivo.
    Columnas: fecha | objetivo | meta | avance
    """
    _ensure_data_dir()
    hoy = datetime.today().strftime("%Y-%m-%d %H:%M")
    rows = []
    for obj, (meta_k, comp_k) in _OBJ_SD_MAP.items():
        rows.append({
            "fecha":    hoy,
            "objetivo": obj,
            "meta":     int(sd.get(meta_k, 1)),
            "avance":   int(sd.get(comp_k, 0)),
        })
    try:
        file_exists = _HISTORY_FILE.exists()
        with _HISTORY_FILE.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=_HISTORY_COLS)
            if not file_exists:
                writer.writeheader()
            writer.writerows(rows)
        return True
    except OSError:
        return False


def load_history_df() -> pd.DataFrame:
    """REQ 4: Carga el CSV histórico como DataFrame."""
    try:
        if not _HISTORY_FILE.exists():
            return pd.DataFrame(columns=_HISTORY_COLS)
        df = pd.read_csv(_HISTORY_FILE, parse_dates=["fecha"])
        return df
    except Exception:
        return pd.DataFrame(columns=_HISTORY_COLS)


def _apply_json_to_sd(sd: dict, json_data: dict):
    """Aplica los datos del JSON al dict _sd en memoria."""
    for obj, (meta_k, comp_k) in _OBJ_SD_MAP.items():
        if obj in json_data:
            entry = json_data[obj]
            if "meta"   in entry: sd[meta_k] = int(entry["meta"])
            if "avance" in entry: sd[comp_k] = int(entry["avance"])

# ─────────────────────────────────────────────────────────────────────────────
# ESTILOS CSS
# ─────────────────────────────────────────────────────────────────────────────
def inject_css():
    st.markdown("""
    <style>
      /* General */
      [data-testid="stAppViewContainer"] { background: #f4f6fb; }
      [data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #e2e8f0; }
      .block-container { padding: 1.5rem 2rem 2rem; max-width: 1400px; }

      /* Métricas */
      [data-testid="metric-container"] {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px 20px 14px;
        box-shadow: 0 1px 4px rgba(0,0,0,.05);
      }
      [data-testid="stMetricValue"] { font-size: 2rem !important; font-weight: 800 !important; }
      [data-testid="stMetricLabel"] { font-size: 0.75rem !important; font-weight: 600 !important;
        text-transform: uppercase; letter-spacing: 0.8px; color: #8fa0b8 !important; }

      /* Encabezados de sección */
      .section-header {
        font-size: 11px; font-weight: 700; letter-spacing: 1.2px;
        text-transform: uppercase; color: #8fa0b8;
        display: flex; align-items: center; gap: 8px;
        margin: 1.5rem 0 0.8rem;
        padding-bottom: 6px;
        border-bottom: 1px solid #e2e8f0;
      }

      /* Alert ribbon */
      .alert-ribbon {
        background: #fff8f0; border: 1px solid #fbd09d; border-radius: 8px;
        padding: 10px 16px; margin-bottom: 1rem;
        display: flex; align-items: center; gap: 8px;
        font-size: 13px; color: #d97706; font-weight: 500;
      }

      /* KPI card supplement */
      .kpi-card {
        background: white; border: 1px solid #e2e8f0; border-radius: 10px;
        padding: 16px 20px; height: 100%;
      }
      .kpi-label  { font-size: 11px; font-weight: 700; text-transform: uppercase;
                    letter-spacing: .8px; color: #8fa0b8; margin-bottom: 4px; }
      .kpi-value  { font-size: 2rem; font-weight: 800; line-height: 1.1; }
      .kpi-sub    { font-size: 11px; color: #8fa0b8; margin-top: 4px; }

      /* Tabla workload */
      .wl-header { font-size: 10px; font-weight: 700; text-transform: uppercase;
                   letter-spacing: .8px; color: #8fa0b8; }

      /* Sidebar labels */
      .sidebar-label { font-size: 11px; font-weight: 600; color: #64748b;
                       text-transform: uppercase; letter-spacing: .6px; margin-bottom: 2px; }

      /* Hide streamlit branding */
      #MainMenu, footer, header { visibility: hidden; }

      /* ── BARRA DE NAVEGACIÓN SUPERIOR FIJA ─────────────────────────────── */
      .nav-top-bar {
        background: white;
        border-bottom: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 10px 20px;
        margin-bottom: 1.2rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 1px 4px rgba(0,0,0,.05);
      }
      .nav-top-brand {
        font-size: 16px; font-weight: 900; color: #0f1c2e;
        display: flex; align-items: center; gap: 8px;
      }
      .nav-top-date {
        font-size: 11px; color: #8fa0b8; text-align: right;
      }
      /* Radio horizontal en top bar */
      div[data-testid="stRadio"] > div {
        flex-direction: row !important;
        gap: 8px;
      }
      div[data-testid="stRadio"] label {
        border: 1px solid #e2e8f0 !important;
        border-radius: 20px !important;
        padding: 6px 16px !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        cursor: pointer;
        transition: all .15s;
        white-space: nowrap;
      }
      div[data-testid="stRadio"] label:hover {
        background: #f1f5f9 !important;
      }
      /* Tarjeta de cumplimiento global */
      .global-kpi-card {
        background: linear-gradient(135deg, #1d6af5 0%, #0891b2 100%);
        border-radius: 14px;
        padding: 16px 14px;
        text-align: center;
        box-shadow: 0 4px 16px rgba(29,106,245,.25);
        height: 100%;
        min-height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
      }
      .global-kpi-card-label {
        font-size: 9px; font-weight: 700; color: rgba(255,255,255,.75);
        text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px;
      }
      .global-kpi-card-value {
        font-size: 2.8rem; font-weight: 900; color: white; line-height: 1;
      }
      .global-kpi-card-sub {
        font-size: 10px; color: rgba(255,255,255,.6); margin-top: 6px;
      }

      /* ── VISTA ESTRATÉGICA ─────────────────────────────────────────────── */

      /* Tarjeta de objetivo estratégico — altura uniforme garantizada */
      .obj-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 18px 16px 12px;
        box-shadow: 0 1px 6px rgba(0,0,0,.06);
        position: relative;
        overflow: hidden;
        min-height: 160px;
      }
      .obj-card-accent {
        position: absolute; top: 0; left: 0;
        width: 4px; height: 100%;
        border-radius: 14px 0 0 14px;
      }
      .obj-label {
        font-size: 9px; font-weight: 800; text-transform: uppercase;
        letter-spacing: 1.2px; color: #94a3b8; margin-bottom: 6px;
        padding-left: 8px; line-height: 1.3;
      }
      .obj-pct {
        font-size: 2.4rem; font-weight: 900; line-height: 1;
        margin-bottom: 8px; padding-left: 8px;
      }
      .obj-bar-track {
        background:#f1f5f9; border-radius:4px; height:5px; margin:0 0 8px;
      }
      .obj-meta-text {
        font-size: 11px; color: #94a3b8; padding-left: 8px;
        margin-top: 4px;
      }

      /* Semáforo badge */
      .badge-green  { display:inline-block; background:#dcfce7; color:#15803d;
                      font-size:10px; font-weight:700; padding:2px 8px;
                      border-radius:20px; margin-left:8px; }
      .badge-yellow { display:inline-block; background:#fef9c3; color:#a16207;
                      font-size:10px; font-weight:700; padding:2px 8px;
                      border-radius:20px; margin-left:8px; }
      .badge-red    { display:inline-block; background:#fee2e2; color:#b91c1c;
                      font-size:10px; font-weight:700; padding:2px 8px;
                      border-radius:20px; margin-left:8px; }

      /* Panel de edición inline bajo tarjeta */
      .edit-panel {
        background: #f8faff;
        border: 1px solid #e0e7ff;
        border-radius: 0 0 14px 14px;
        border-top: none;
        padding: 10px 12px 12px;
        margin-top: -6px;
      }
      .edit-label {
        font-size: 9px; font-weight: 700; text-transform: uppercase;
        letter-spacing: .8px; color: #94a3b8; margin-bottom: 4px;
      }

      /* Tarjeta de cumplimiento global */
      .global-kpi-card {
        background: linear-gradient(160deg, #1d6af5 0%, #0891b2 100%);
        border-radius: 14px;
        padding: 20px 14px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(29,106,245,.28);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        min-height: 260px;
      }
      .global-kpi-card-label {
        font-size: 9px; font-weight: 800; color: rgba(255,255,255,.75);
        text-transform: uppercase; letter-spacing: 1.2px; margin-bottom: 10px;
        line-height: 1.4;
      }
      .global-kpi-card-value {
        font-size: 3.4rem; font-weight: 900; color: white; line-height: 1;
        margin-bottom: 8px;
      }
      .global-kpi-card-badge {
        font-size: 11px; background: rgba(255,255,255,.2);
        color: white; padding: 3px 12px; border-radius: 20px;
        font-weight: 600; margin-bottom: 8px;
      }
      .global-kpi-card-sub {
        font-size: 10px; color: rgba(255,255,255,.55); margin-top: 4px;
      }

      /* Panel de configuración editable */
      .config-panel {
        background: #f8faff; border: 1px solid #dbeafe;
        border-radius: 12px; padding: 16px 20px; margin-bottom: 1rem;
      }
      .config-title {
        font-size: 11px; font-weight: 700; text-transform: uppercase;
        letter-spacing: 1px; color: #3b82f6;
      }

      /* Indicador global legacy */
      .global-kpi {
        background: linear-gradient(135deg, #1d6af5 0%, #0891b2 100%);
        border-radius: 16px; padding: 28px 32px; color: white;
        text-align: center; box-shadow: 0 4px 20px rgba(29,106,245,.25);
      }
      .global-kpi-label { font-size: 12px; font-weight: 600; opacity: .8;
                          text-transform: uppercase; letter-spacing: 1px; }
      .global-kpi-value { font-size: 4rem; font-weight: 900; line-height: 1.1; }
      .global-kpi-sub   { font-size: 12px; opacity: .7; margin-top: 4px; }

      /* Streamlit number_input compacto */
      [data-testid="stNumberInputContainer"] input {
        font-size: 13px !important;
        padding: 4px 8px !important;
        height: 32px !important;
      }
    </style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# 1. CARGA DE DATOS
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_data(file) -> pd.DataFrame:
    """Carga el Excel exportado desde Microsoft Planner."""
    try:
        df = pd.read_excel(file, sheet_name=0)
        return df
    except Exception as e:
        st.error(f"❌ Error leyendo el archivo: {e}")
        return pd.DataFrame()


# ─────────────────────────────────────────────────────────────────────────────
# 2. EXTRACCIÓN DE CATEGORÍA ESTRATÉGICA
# ─────────────────────────────────────────────────────────────────────────────
STRATEGIC_PATTERNS = {
    "Excelencia ERP":              r"excelencia\s+erp|🟨",
    "Eficiencia Operativa":        r"eficiencia\s+operativa|🟦",
    "Seguridad de la Información": r"seguridad\s+(?:de\s+la\s+)?(?:informaci[oó]n|informacion)",
    "Datos Confiables":            r"datos\s+confiables|🟩",
    "Integración":                 r"integraci[oó]n|🟥",
}

def extract_strategic_category(label: str) -> str:
    """Detecta la categoría estratégica desde el campo Etiquetas."""
    if pd.isna(label) or label == "":
        return "Sin clasificar"
    label_lower = str(label).lower()
    for category, pattern in STRATEGIC_PATTERNS.items():
        if re.search(pattern, label_lower, re.IGNORECASE):
            return category
    return "Sin clasificar"


# ─────────────────────────────────────────────────────────────────────────────
# 3. PREPROCESAMIENTO
# ─────────────────────────────────────────────────────────────────────────────
REQUIRED_COLUMNS = {
    "nombre":       ["Nombre de la tarea", "Task Name", "Nombre"],
    "bucket":       ["Nombre del depósito", "Bucket Name", "Depósito"],
    "progreso":     ["Progreso", "Progress", "Estado"],
    "prioridad":    ["Priority", "Prioridad"],
    "asignado":     ["Asignado a", "Assigned To"],
    "creacion":     ["Fecha de creación", "Created Date", "Created"],
    "inicio":       ["Fecha de inicio", "Start Date"],
    "vencimiento":  ["Fecha de vencimiento", "Due Date"],
    "finalizacion": ["Fecha de finalización", "Completion Date", "Completed Date"],
    "retraso":      ["Con retraso", "Late", "Is Late"],
    "etiquetas":    ["Etiquetas", "Labels", "Tags"],
}

def find_column(df: pd.DataFrame, candidates: list) -> str | None:
    """Encuentra el nombre real de una columna entre varios candidatos."""
    for c in candidates:
        if c in df.columns:
            return c
    # Búsqueda case-insensitive
    df_cols_lower = {col.lower().strip(): col for col in df.columns}
    for c in candidates:
        if c.lower().strip() in df_cols_lower:
            return df_cols_lower[c.lower().strip()]
    return None

def normalize_progress(val) -> str:
    """Normaliza el valor de progreso a español estándar."""
    if pd.isna(val):
        return "No iniciado"
    v = str(val).strip().lower()
    return PROGRESS_MAP.get(v, str(val).strip())

@st.cache_data(show_spinner=False)
def preprocess_data(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Limpia, normaliza y enriquece el DataFrame."""
    if df.empty:
        return df, {}

    col_map = {}
    missing = []
    for key, candidates in REQUIRED_COLUMNS.items():
        found = find_column(df, candidates)
        if found:
            col_map[key] = found
        else:
            missing.append(key)

    # Renombrar a nombres internos estándar
    rename = {v: k for k, v in col_map.items() if v != k}
    df = df.rename(columns=rename)

    # Rellenar columnas faltantes con None
    for key in REQUIRED_COLUMNS:
        if key not in df.columns:
            df[key] = None

    # ── Fechas ──────────────────────────────────────────────────────────────
    date_cols = ["creacion", "inicio", "vencimiento", "finalizacion"]
    for c in date_cols:
        df[c] = pd.to_datetime(df[c], errors="coerce", dayfirst=True)

    # ── Progreso normalizado ─────────────────────────────────────────────────
    df["progreso"] = df["progreso"].apply(normalize_progress)

    # ── Retraso (bool) ───────────────────────────────────────────────────────
    def parse_late(v):
        if pd.isna(v): return False
        if isinstance(v, bool): return v
        return str(v).strip().lower() in ["true", "sí", "si", "yes", "1"]
    df["retraso"] = df["retraso"].apply(parse_late)

    # ── Categoría estratégica ────────────────────────────────────────────────
    df["categoria"] = df["etiquetas"].apply(extract_strategic_category)

    # ── Lead Time (días) ─────────────────────────────────────────────────────
    df["lead_time_dias"] = (df["finalizacion"] - df["creacion"]).dt.days

    # ── Mes de finalización ──────────────────────────────────────────────────
    df["mes_finalizacion"] = df["finalizacion"].dt.to_period("M").astype(str)

    # ── Vencida abierta: vencimiento < hoy y no completada ──────────────────
    hoy = pd.Timestamp.today().normalize()
    df["vencida_abierta"] = (
        df["vencimiento"].notna() &
        (df["vencimiento"] < hoy) &
        (df["progreso"] != "Completado")
    )

    # ── Expandir múltiples asignados ─────────────────────────────────────────
    # (se usará en workload; aquí guardamos el raw)
    df["asignado_raw"] = df["asignado"].fillna("Sin asignar")

    return df, {"missing_cols": missing, "col_map": col_map}


# ─────────────────────────────────────────────────────────────────────────────
# 4. CÁLCULO DE KPIs
# ─────────────────────────────────────────────────────────────────────────────
def calculate_kpis(df: pd.DataFrame) -> dict:
    """Calcula todos los KPIs ejecutivos del portafolio."""
    if df.empty:
        return {}

    total = len(df)
    completados   = (df["progreso"] == "Completado").sum()
    en_curso      = (df["progreso"] == "En curso").sum()
    no_iniciado   = (df["progreso"] == "No iniciado").sum()
    con_retraso   = df["retraso"].sum()
    vencidas_abiertas = df["vencida_abierta"].sum()

    # Lead times
    lead_times = df.loc[df["progreso"] == "Completado", "lead_time_dias"].dropna()
    lead_avg   = lead_times.mean() if len(lead_times) > 0 else None
    lead_med   = lead_times.median() if len(lead_times) > 0 else None

    # Velocidad mensual
    vel = df[df["progreso"] == "Completado"].groupby("mes_finalizacion").size()

    # Tasa asignación
    asignados = (df["asignado_raw"] != "Sin asignar").sum()

    return {
        "total":              total,
        "completados":        int(completados),
        "en_curso":           int(en_curso),
        "no_iniciado":        int(no_iniciado),
        "con_retraso":        int(con_retraso),
        "vencidas_abiertas":  int(vencidas_abiertas),
        "pct_completado":     round(completados / total * 100, 1) if total else 0,
        "pct_en_curso":       round(en_curso   / total * 100, 1) if total else 0,
        "pct_no_iniciado":    round(no_iniciado / total * 100, 1) if total else 0,
        "pct_retraso":        round(con_retraso / total * 100, 1) if total else 0,
        "lead_avg":           round(lead_avg, 1) if lead_avg is not None else None,
        "lead_med":           round(lead_med, 1) if lead_med is not None else None,
        "velocidad_mensual":  vel,
        "tasa_asignacion":    round(asignados / total * 100, 1) if total else 0,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 5. TABLA DE CARGA DE TRABAJO
# ─────────────────────────────────────────────────────────────────────────────
def calculate_workload(df: pd.DataFrame) -> pd.DataFrame:
    """Genera la tabla de carga de trabajo por especialista."""
    if df.empty:
        return pd.DataFrame()

    hoy = pd.Timestamp.today().normalize()
    rows = []

    # Expandir asignados múltiples (separados por ";")
    expanded = []
    for _, row in df.iterrows():
        raw = str(row.get("asignado_raw", "Sin asignar"))
        persons = [p.strip() for p in raw.split(";") if p.strip()]
        if not persons:
            persons = ["Sin asignar"]
        for person in persons:
            r = row.copy()
            r["especialista"] = person
            expanded.append(r)

    exp_df = pd.DataFrame(expanded)

    for especialista, g in exp_df.groupby("especialista"):
        total        = len(g)
        completadas  = (g["progreso"] == "Completado").sum()
        en_curso     = (g["progreso"] == "En curso").sum()
        no_iniciado  = (g["progreso"] == "No iniciado").sum()
        con_retraso  = g["retraso"].sum()
        vencidas     = g["vencida_abierta"].sum()
        activas      = total - completadas  # todo lo que no está completado

        pct_cumplimiento = round(completadas / total * 100, 1) if total > 0 else 0.0

        # Lead time promedio solo de completadas
        lt = g.loc[g["progreso"] == "Completado", "lead_time_dias"].dropna()
        lead_avg = round(lt.mean(), 1) if len(lt) > 0 else None

        rows.append({
            "Especialista":       especialista,
            "Total":              int(total),
            "Carga Activa":       int(activas),
            "Completadas":        int(completadas),
            "En Curso":           int(en_curso),
            "No Iniciadas":       int(no_iniciado),
            "Con Retraso":        int(con_retraso),
            "Vencidas Abiertas":  int(vencidas),
            "% Cumplimiento":     pct_cumplimiento,
            "Lead Time (días)":   lead_avg,
        })

    wl = pd.DataFrame(rows)
    if not wl.empty:
        wl = wl.sort_values("Carga Activa", ascending=False).reset_index(drop=True)

    return wl


# ─────────────────────────────────────────────────────────────────────────────
# 6. ESTILIZACIÓN DE LA TABLA WORKLOAD
# ─────────────────────────────────────────────────────────────────────────────
def style_workload(wl: pd.DataFrame) -> pd.DataFrame:
    """
    Formatea la tabla de carga de trabajo con emojis y columnas limpias.
    SIN pandas Styler — compatible 100% con Streamlit Cloud.
    Devuelve un DataFrame plano formateado para usar con st.dataframe().
    """
    if wl.empty:
        return wl

    def fmt_pct(val):
        if pd.isna(val): return "—"
        icon = "🟢" if val >= 60 else ("🟡" if val >= 30 else "🔴")
        return f"{icon} {val:.1f}%"

    def fmt_lead(val):
        if pd.isna(val): return "—"
        return f"{val:.1f} d"

    def fmt_alert(row):
        """Columna de alerta visual al inicio de la fila."""
        if row.get("Vencidas Abiertas", 0) > 0:
            return "🔴"
        if row.get("Carga Activa", 0) >= 4:
            return "🟡"
        return "🟢"

    display = wl.copy()
    display.insert(0, " ", display.apply(fmt_alert, axis=1))
    display["% Cumplimiento"]   = display["% Cumplimiento"].apply(fmt_pct)
    display["Lead Time (días)"] = display["Lead Time (días)"].apply(fmt_lead)
    display = display.reset_index(drop=True)
    return display


# ─────────────────────────────────────────────────────────────────────────────
# 7. GRÁFICOS
# ─────────────────────────────────────────────────────────────────────────────
def chart_pipeline_estrategico(df: pd.DataFrame) -> go.Figure:
    cat_counts = (
        df.groupby("categoria")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=True)
    )
    if cat_counts.empty:
        fig = go.Figure()
        fig.update_layout(height=300, paper_bgcolor="white", plot_bgcolor="white")
        return fig

    max_val = cat_counts["count"].max()
    colors = [CATEGORY_COLORS.get(c, "#94a3b8") for c in cat_counts["categoria"]]

    fig = go.Figure(go.Bar(
        x=cat_counts["count"],
        y=cat_counts["categoria"],
        orientation="h",
        marker_color=colors,
        marker_line_width=0,
        text=cat_counts["count"],
        textposition="outside",
        textfont=dict(size=13, family="Inter, sans-serif"),
        cliponaxis=False,
    ))
    fig.update_layout(
        xaxis=dict(
            showgrid=True,
            gridcolor="#f1f5f9",
            gridwidth=1,
            zeroline=False,
            title=None,
            range=[0, max_val * 1.25],   # ← espacio suficiente para etiquetas
            tickfont=dict(size=11, color="#8fa0b8"),
        ),
        yaxis=dict(
            showgrid=False,
            title=None,
            tickfont=dict(size=12, color="#334155"),
            automargin=True,
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=0, r=60, t=8, b=8),   # r=60 para labels externas
        height=max(260, 42 * len(cat_counts) + 40),
        font=dict(family="Inter, sans-serif", size=12),
        bargap=0.35,
    )
    return fig


def chart_progreso_dona(kpis: dict) -> go.Figure:
    labels = ["Completado", "En curso", "No iniciado"]
    values = [kpis["completados"], kpis["en_curso"], kpis["no_iniciado"]]
    colors = [COLORS["green"], COLORS["yellow"], "#e2e8f0"]

    # Filtrar segmentos en cero para no mostrar etiquetas vacías
    data = [(l, v, c) for l, v, c in zip(labels, values, colors) if v > 0]
    if not data:
        return go.Figure()
    labels_f, values_f, colors_f = zip(*data)

    fig = go.Figure(go.Pie(
        labels=list(labels_f),
        values=list(values_f),
        hole=0.68,
        marker=dict(colors=list(colors_f), line=dict(color="white", width=3)),
        textinfo="percent",           # solo % dentro del segmento
        textposition="inside",        # ← siempre dentro, nunca cortado
        textfont=dict(size=11, family="Inter, sans-serif", color="white"),
        hovertemplate="<b>%{label}</b><br>%{value} tareas (%{percent})<extra></extra>",
        showlegend=True,
        direction="clockwise",
        sort=False,
    ))

    pct_comp = kpis["pct_completado"]
    total    = kpis["total"]

    # ── Layout minimalista 100% compatible con Streamlit Cloud ───────────────
    fig.update_layout(
        annotations=[dict(
            text=f"<b>{pct_comp}%</b><br>completado",
            x=0.5, y=0.5,
            font=dict(size=15, color="#0f1c2e"),
            showarrow=False,
            align="center",
        )],
        showlegend=True,
        legend=dict(
            orientation="h",
            x=0.5,
            xanchor="center",
            y=-0.05,
        ),
        margin=dict(t=40, b=40, l=40, r=40),
        height=320,
        paper_bgcolor="white",
    )
    return fig


def chart_velocidad_mensual(kpis: dict) -> go.Figure:
    vel = kpis.get("velocidad_mensual", pd.Series(dtype=int))
    if vel.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="Sin entregas registradas aún",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=13, color="#94a3b8"),
        )
        fig.update_layout(height=240, paper_bgcolor="white", plot_bgcolor="white",
                          xaxis=dict(visible=False), yaxis=dict(visible=False))
        return fig

    vel = vel.reset_index()
    vel.columns = ["Mes_raw", "Completadas"]

    # ── Convertir Period/string a nombre de mes legible ──────────────────────
    MES_ES = {
        "01": "Ene", "02": "Feb", "03": "Mar", "04": "Abr",
        "05": "May", "06": "Jun", "07": "Jul", "08": "Ago",
        "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dic",
    }
    def fmt_mes(v):
        s = str(v)                    # e.g. "2026-02" or "2026-01"
        if len(s) >= 7 and s[4] == "-":
            yr  = s[2:4]              # "26"
            mon = s[5:7]              # "02"
            return f"{MES_ES.get(mon, mon)} '{yr}"
        return s

    vel["Mes"] = vel["Mes_raw"].apply(fmt_mes)

    fig = go.Figure(go.Bar(
        x=vel["Mes"],
        y=vel["Completadas"],
        marker_color=COLORS["green"],
        marker_line_width=0,
        text=vel["Completadas"],
        textposition="outside",
        textfont=dict(size=13, family="Inter, sans-serif"),
        cliponaxis=False,
    ))
    max_y = vel["Completadas"].max()
    fig.update_layout(
        xaxis=dict(
            title=None,
            showgrid=False,
            tickfont=dict(size=12, color="#334155"),
            type="category",          # ← fuerza texto, nunca timestamps
        ),
        yaxis=dict(
            title=None,
            showgrid=True,
            gridcolor="#f1f5f9",
            gridwidth=1,
            zeroline=False,
            range=[0, max_y * 1.3],
            tickfont=dict(size=11, color="#8fa0b8"),
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=10, r=20, t=16, b=10),
        height=270,
        font=dict(family="Inter, sans-serif", size=12),
        bargap=0.45,
    )
    return fig


def chart_lead_time_por_especialista(df: pd.DataFrame) -> go.Figure:
    comp = df[(df["progreso"] == "Completado") & df["lead_time_dias"].notna()].copy()
    if comp.empty:
        fig = go.Figure()
        fig.add_annotation(text="Sin tareas completadas con fechas registradas",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=12, color="#94a3b8"))
        fig.update_layout(height=240, paper_bgcolor="white", plot_bgcolor="white",
                          xaxis=dict(visible=False), yaxis=dict(visible=False))
        return fig

    # Expandir asignados
    expanded = []
    for _, row in comp.iterrows():
        raw = str(row.get("asignado_raw", "Sin asignar"))
        for p in [x.strip() for x in raw.split(";") if x.strip()]:
            r = row.copy(); r["especialista"] = p
            expanded.append(r)
    if not expanded:
        return go.Figure()

    exp = pd.DataFrame(expanded)
    lt = (
        exp.groupby("especialista")["lead_time_dias"]
        .agg(["mean", "count"])
        .reset_index()
        .rename(columns={"mean": "lead_avg", "count": "n"})
        .query("n > 0")
        .sort_values("lead_avg")
    )
    lt["lead_avg"] = lt["lead_avg"].round(1)

    colors = [
        COLORS["green"]  if v <= 7  else
        COLORS["yellow"] if v <= 14 else
        COLORS["red"]
        for v in lt["lead_avg"]
    ]

    max_y = lt["lead_avg"].max()
    fig = go.Figure(go.Bar(
        x=lt["especialista"],
        y=lt["lead_avg"],
        marker_color=colors,
        marker_line_width=0,
        text=[f"{v} d" for v in lt["lead_avg"]],
        textposition="outside",
        textfont=dict(size=12, family="Inter, sans-serif"),
        cliponaxis=False,
    ))
    fig.update_layout(
        xaxis=dict(title=None, showgrid=False, tickfont=dict(size=11, color="#334155"),
                   type="category"),
        yaxis=dict(title=None, showgrid=True, gridcolor="#f1f5f9", zeroline=False,
                   range=[0, max_y * 1.3], tickfont=dict(size=11, color="#8fa0b8")),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=10, r=20, t=16, b=10),
        height=270,
        font=dict(family="Inter, sans-serif", size=12),
        bargap=0.45,
    )
    return fig


def chart_carga_por_especialista(wl: pd.DataFrame) -> go.Figure:
    if wl.empty:
        return go.Figure()

    # Solo filas con carga > 0
    top = wl[wl["Total"] > 0].head(10)
    if top.empty:
        return go.Figure()

    COLS = {"Completadas": COLORS["green"], "En Curso": COLORS["yellow"], "No Iniciadas": "#cbd5e1"}
    fig = go.Figure()
    for col, color in COLS.items():
        col_data = top.get(col, pd.Series([0]*len(top)))
        fig.add_trace(go.Bar(
            name=col,
            x=top["Especialista"],
            y=col_data,
            marker_color=color,
            marker_line_width=0,
            text=col_data.where(col_data > 0),   # label solo si > 0
            textposition="inside",
            textfont=dict(
                color="white" if col != "No Iniciadas" else "#64748b",
                size=11, family="Inter, sans-serif",
            ),
            insidetextanchor="middle",
        ))
    fig.update_layout(
        barmode="stack",
        xaxis=dict(title=None, showgrid=False, tickfont=dict(size=11, color="#334155"),
                   type="category"),
        yaxis=dict(title=None, showgrid=True, gridcolor="#f1f5f9", zeroline=False,
                   tickfont=dict(size=11, color="#8fa0b8")),
        legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=10, r=20, t=8, b=40),
        height=310,
        font=dict(family="Inter, sans-serif", size=12),
        bargap=0.35,
    )
    return fig


def chart_distribucion_areas(df: pd.DataFrame) -> go.Figure:
    """Gráfica de áreas de negocio extraídas de las etiquetas (sin la categoría estratégica)."""
    area_counts = {}
    skip_patterns = list(STRATEGIC_PATTERNS.values()) + [
        r"🟨", r"🟦", r"🟩", r"🟥", r"excelencia erp", r"eficiencia operativa",
        r"seguridad", r"datos confiables", r"integraci",
    ]

    for etiq in df["etiquetas"].fillna(""):
        for tag in str(etiq).split(";"):
            tag = tag.strip()
            if not tag:
                continue
            tag_clean = re.sub(r"^[🟨🟦🟩🟥🔴⬛]\s*", "", tag).strip()
            is_strategic = any(re.search(p, tag.lower(), re.IGNORECASE) for p in skip_patterns)
            if not is_strategic and len(tag_clean) > 1:
                area_counts[tag_clean] = area_counts.get(tag_clean, 0) + 1

    if not area_counts:
        fig = go.Figure()
        fig.add_annotation(text="Sin datos de área de negocio en las etiquetas",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=12, color="#94a3b8"))
        fig.update_layout(height=300, paper_bgcolor="white", plot_bgcolor="white",
                          xaxis=dict(visible=False), yaxis=dict(visible=False))
        return fig

    areas = (
        pd.Series(area_counts)
        .sort_values(ascending=False)
        .head(15)
        .reset_index()
    )
    areas.columns = ["Área", "Cantidad"]

    palette = ["#1d6af5","#0da063","#6d28d9","#0891b2","#d97706","#e03030",
               "#ea580c","#059669","#7c3aed","#dc2626","#db2777","#2563eb",
               "#b45309","#0e7490","#475569"]
    colors = [palette[i % len(palette)] for i in range(len(areas))]

    max_y = areas["Cantidad"].max()
    fig = go.Figure(go.Bar(
        x=areas["Área"],
        y=areas["Cantidad"],
        marker_color=colors,
        marker_line_width=0,
        text=areas["Cantidad"],
        textposition="outside",
        textfont=dict(size=11, family="Inter, sans-serif"),
        cliponaxis=False,
    ))
    fig.update_layout(
        xaxis=dict(
            title=None,
            tickangle=-38,
            showgrid=False,
            tickfont=dict(size=11, color="#334155"),
            type="category",
            automargin=True,
        ),
        yaxis=dict(
            title=None,
            showgrid=True,
            gridcolor="#f1f5f9",
            zeroline=False,
            range=[0, max_y * 1.25],
            tickfont=dict(size=11, color="#8fa0b8"),
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=10, r=20, t=16, b=10),
        height=330,
        font=dict(family="Inter, sans-serif", size=11),
        bargap=0.35,
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# 8. FILTROS (SIDEBAR)
# ─────────────────────────────────────────────────────────────────────────────
def apply_sidebar_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Renderiza el sidebar de filtros y retorna el DataFrame filtrado."""
    with st.sidebar:
        st.image(
            "https://img.icons8.com/fluency/48/000000/combo-chart.png",
            width=36,
        )
        st.markdown("### ⚡ Dashboard TD 2026")
        st.markdown("---")

        # ── Especialista ───────────────────────────────────────────────────
        st.markdown('<div class="sidebar-label">👤 Especialista</div>', unsafe_allow_html=True)
        all_persons = set()
        for raw in df["asignado_raw"].fillna("Sin asignar"):
            for p in str(raw).split(";"):
                all_persons.add(p.strip())
        all_persons = sorted(all_persons)
        sel_person = st.multiselect(
            "Especialista", options=all_persons, default=[], label_visibility="collapsed"
        )

        # ── Categoría ──────────────────────────────────────────────────────
        st.markdown('<div class="sidebar-label">🏆 Categoría estratégica</div>', unsafe_allow_html=True)
        cats = sorted(df["categoria"].unique())
        sel_cat = st.multiselect(
            "Categoría", options=cats, default=[], label_visibility="collapsed"
        )

        # ── Progreso ───────────────────────────────────────────────────────
        st.markdown('<div class="sidebar-label">📊 Estado de progreso</div>', unsafe_allow_html=True)
        estados = sorted(df["progreso"].unique())
        sel_estado = st.multiselect(
            "Progreso", options=estados, default=[], label_visibility="collapsed"
        )

        # ── Prioridad ──────────────────────────────────────────────────────
        st.markdown('<div class="sidebar-label">🎯 Prioridad</div>', unsafe_allow_html=True)
        prioridades = sorted(df["prioridad"].dropna().unique())
        sel_prio = st.multiselect(
            "Prioridad", options=prioridades, default=[], label_visibility="collapsed"
        )

        # ── Rango de fechas ────────────────────────────────────────────────
        st.markdown('<div class="sidebar-label">📅 Rango de creación</div>', unsafe_allow_html=True)
        min_date = df["creacion"].min()
        max_date = df["creacion"].max()

        if pd.notna(min_date) and pd.notna(max_date):
            fecha_rango = st.date_input(
                "Fechas", value=(min_date.date(), max_date.date()),
                min_value=min_date.date(), max_value=max_date.date(),
                label_visibility="collapsed",
            )
        else:
            fecha_rango = None

        # ── Sólo con retraso ───────────────────────────────────────────────
        st.markdown("---")
        solo_retraso = st.checkbox("⚠ Solo requerimientos con retraso", value=False)
        solo_vencidas = st.checkbox("🔴 Solo vencidas abiertas", value=False)

        st.markdown("---")
        st.caption(f"📁 Total registros: **{len(df)}**")

    # ── Aplicar filtros ────────────────────────────────────────────────────
    filtered = df.copy()

    if sel_person:
        mask = filtered["asignado_raw"].apply(
            lambda raw: any(p in [x.strip() for x in str(raw).split(";")] for p in sel_person)
        )
        filtered = filtered[mask]

    if sel_cat:
        filtered = filtered[filtered["categoria"].isin(sel_cat)]

    if sel_estado:
        filtered = filtered[filtered["progreso"].isin(sel_estado)]

    if sel_prio:
        filtered = filtered[filtered["prioridad"].isin(sel_prio)]

    if fecha_rango and len(fecha_rango) == 2:
        f_ini, f_fin = fecha_rango
        filtered = filtered[
            (filtered["creacion"].isna()) |
            (
                (filtered["creacion"].dt.date >= f_ini) &
                (filtered["creacion"].dt.date <= f_fin)
            )
        ]

    if solo_retraso:
        filtered = filtered[filtered["retraso"]]

    if solo_vencidas:
        filtered = filtered[filtered["vencida_abierta"]]

    return filtered


# ─────────────────────────────────────────────────────────────────────────────
# 9. DASHBOARD PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────
def create_dashboard(df: pd.DataFrame, metadata: dict):
    """Construye y renderiza el dashboard completo."""
    inject_css()

    # ── Topbar / Título ────────────────────────────────────────────────────
    col_title, col_meta = st.columns([3, 1])
    with col_title:
        st.markdown(
            "## ⚡ Dashboard Gestión de Requerimientos TD 2026",
            help="Datos exportados desde Microsoft Planner"
        )
        st.caption("Transformación Digital · Product Owner View")
    with col_meta:
        st.markdown(
            f"<div style='text-align:right;padding-top:12px;color:#8fa0b8;font-size:12px;'>"
            f"📅 {datetime.today().strftime('%d/%m/%Y')}<br>"
            f"🗂 {len(df)} requerimientos</div>",
            unsafe_allow_html=True
        )

    # ── Filtros ────────────────────────────────────────────────────────────
    df_f = apply_sidebar_filters(df)

    if df_f.empty:
        st.warning("⚠ No hay datos que coincidan con los filtros seleccionados.")
        return

    kpis = calculate_kpis(df_f)
    wl   = calculate_workload(df_f)

    # ── Alert ribbon ───────────────────────────────────────────────────────
    if kpis["con_retraso"] > 0:
        st.markdown(
            f'<div class="alert-ribbon">⚠️ <strong>{kpis["con_retraso"]} requerimientos con retraso</strong>'
            f' · {kpis["vencidas_abiertas"]} vencidos sin cerrar aún.</div>',
            unsafe_allow_html=True,
        )

    # ═══════════════════════════════════════════════════════════════════════
    # SECCIÓN 1: KPIs EJECUTIVOS
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-header">📊 Indicadores Clave de Desempeño</div>',
                unsafe_allow_html=True)

    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    c1.metric("Total Reqs.", kpis["total"])
    c2.metric("Completados",
              f"{kpis['completados']}",
              f"{kpis['pct_completado']}% del total",
              delta_color="normal")
    c3.metric("En Curso",
              kpis["en_curso"],
              f"{kpis['pct_en_curso']}%")
    c4.metric("No Iniciados",
              kpis["no_iniciado"],
              f"{kpis['pct_no_iniciado']}%",
              delta_color="inverse")
    c5.metric("Con Retraso",
              kpis["con_retraso"],
              f"{kpis['pct_retraso']}%",
              delta_color="inverse")
    c6.metric("Lead Time Prom.",
              f"{kpis['lead_avg']} d" if kpis["lead_avg"] is not None else "—",
              "días hasta cierre")
    c7.metric("Tasa Asignación",
              f"{kpis['tasa_asignacion']}%",
              delta_color="normal")

    st.markdown("<br>", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════
    # SECCIÓN 2: PIPELINE ESTRATÉGICO + DONA + VELOCIDAD
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-header">🔄 Pipeline Estratégico & Avance</div>',
                unsafe_allow_html=True)

    col_pipe, col_dona, col_vel = st.columns([2.2, 1.3, 1.8])

    with col_pipe:
        st.markdown(
            "<p style='font-size:13px;font-weight:600;color:#334155;margin-bottom:4px;'>"
            "Requerimientos por Categoría Estratégica</p>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(chart_pipeline_estrategico(df_f),
                        use_container_width=True, key="pipeline")

    with col_dona:
        st.markdown(
            "<p style='font-size:13px;font-weight:600;color:#334155;margin-bottom:4px;'>"
            "Estado del Portafolio</p>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(chart_progreso_dona(kpis),
                        use_container_width=True, key="dona")

    with col_vel:
        st.markdown(
            "<p style='font-size:13px;font-weight:600;color:#334155;margin-bottom:4px;'>"
            "Velocidad de Entrega Mensual</p>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(chart_velocidad_mensual(kpis),
                        use_container_width=True, key="velocidad")

    # ═══════════════════════════════════════════════════════════════════════
    # SECCIÓN 3: TABLA DE CARGA DE TRABAJO (NUEVO REQUERIMIENTO)
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-header">👥 Carga de Trabajo & Avance por Especialista</div>',
                unsafe_allow_html=True)

    # Leyenda de semáforos
    col_l1, col_l2, col_l3, col_l4 = st.columns(4)
    col_l1.markdown("🟢 **≥ 60%** cumplimiento — óptimo")
    col_l2.markdown("🟡 **30–59%** cumplimiento — en seguimiento")
    col_l3.markdown("🔴 **< 30%** cumplimiento — alerta")
    col_l4.markdown("🔴 Col. ' ' = tiene vencidas abiertas")

    if not wl.empty:
        styled_wl = style_workload(wl)
        st.dataframe(
            styled_wl,
            use_container_width=True,
            height=min(60 + 48 * len(wl), 520),
            hide_index=True,
        )

        # Mini chart de carga apilada
        st.markdown(
            "<p style='font-size:13px;font-weight:600;color:#334155;margin:8px 0 4px;'>"
            "Distribución de carga por especialista (top 10)</p>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(chart_carga_por_especialista(wl),
                        use_container_width=True, key="carga_bar")

    else:
        st.info("No hay datos de carga de equipo para el filtro seleccionado.")

    # ═══════════════════════════════════════════════════════════════════════
    # SECCIÓN 4: ANÁLISIS COMPLEMENTARIO
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-header">🔍 Análisis Complementario</div>',
                unsafe_allow_html=True)

    col_lt, col_areas = st.columns([1, 1.5])

    with col_lt:
        st.markdown(
            "<p style='font-size:13px;font-weight:600;color:#334155;margin-bottom:4px;'>"
            "Lead Time Promedio por Especialista <span style='color:#8fa0b8;font-weight:400'>(días al cierre)</span></p>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(chart_lead_time_por_especialista(df_f),
                        use_container_width=True, key="lead_time")

    with col_areas:
        st.markdown(
            "<p style='font-size:13px;font-weight:600;color:#334155;margin-bottom:4px;'>"
            "Distribución por Área de Negocio</p>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(chart_distribucion_areas(df_f),
                        use_container_width=True, key="areas")

    # ═══════════════════════════════════════════════════════════════════════
    # SECCIÓN 5: TABLA DETALLE REQUERIMIENTOS
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-header">📝 Detalle de Requerimientos</div>',
                unsafe_allow_html=True)

    # Filtro rápido dentro de la tabla
    tab_all, tab_ejec, tab_val, tab_comp, tab_ret = st.tabs([
        f"Todos ({len(df_f)})",
        f"En Ejecución ({(df_f['progreso']=='En curso').sum()})",
        f"En Validación ({df_f['bucket'].str.contains('validaci', case=False, na=False).sum()})",
        f"Completados ({kpis['completados']})",
        f"⚠ Retraso ({kpis['con_retraso']})",
    ])

    display_cols = {
        "nombre":         "Requerimiento",
        "bucket":         "Etapa",
        "progreso":       "Estado",
        "prioridad":      "Prioridad",
        "asignado_raw":   "Asignado a",
        "categoria":      "Categoría Estratégica",
        "vencimiento":    "Vencimiento",
        "finalizacion":   "Finalización",
        "lead_time_dias": "Lead Time (d)",
        "retraso":        "⚠ Retraso",
        "vencida_abierta":"Vencida Abierta",
    }

    def get_display(sub_df: pd.DataFrame) -> pd.DataFrame:
        """Prepara el DataFrame para visualización: solo cols disponibles, sin filas vacías."""
        if sub_df.empty:
            return pd.DataFrame()
        # Solo columnas que existen
        cols_ok = [c for c in display_cols if c in sub_df.columns]
        d = sub_df[cols_ok].copy().rename(columns=display_cols)
        # Formatear fechas
        for col in ["Vencimiento", "Finalización"]:
            if col in d.columns:
                d[col] = pd.to_datetime(d[col], errors="coerce").dt.strftime("%d/%m/%Y")
        # Eliminar filas donde el nombre del requerimiento es vacío/NaN
        if "Requerimiento" in d.columns:
            d = d[d["Requerimiento"].notna() & (d["Requerimiento"].astype(str).str.strip() != "")]
        # Reemplazar NaN → "—" para visualización limpia
        d = d.fillna("—")
        d.index = range(1, len(d) + 1)
        return d

    def show_table(sub_df: pd.DataFrame, height: int = 380, empty_msg: str = "Sin registros para esta vista."):
        d = get_display(sub_df)
        if d.empty:
            st.markdown(
                f"<div style='text-align:center;padding:32px;color:#94a3b8;"
                f"font-size:13px;background:#f8fafc;border-radius:8px;"
                f"border:1px dashed #e2e8f0;margin:8px 0;'>"
                f"📭 {empty_msg}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.dataframe(d, use_container_width=True, height=min(height, 48 * len(d) + 60))

    with tab_all:
        show_table(df_f, height=420, empty_msg="No hay requerimientos con los filtros seleccionados.")
    with tab_ejec:
        sub = df_f[df_f["progreso"] == "En curso"]
        show_table(sub, height=360, empty_msg="No hay requerimientos en ejecución actualmente.")
    with tab_val:
        sub = df_f[df_f["bucket"].str.contains("validaci", case=False, na=False)]
        show_table(sub, height=360, empty_msg="No hay requerimientos en validación actualmente.")
    with tab_comp:
        sub = df_f[df_f["progreso"] == "Completado"]
        show_table(sub, height=360, empty_msg="No hay requerimientos completados en el período seleccionado.")
    with tab_ret:
        sub = df_f[df_f["retraso"] == True]
        show_table(sub, height=360, empty_msg="✅ Sin requerimientos con retraso — ¡excelente!")

    # ── Exportar ───────────────────────────────────────────────────────────
    st.markdown("---")
    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        csv_data = df_f.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇ Descargar datos filtrados (CSV)",
            data=csv_data,
            file_name=f"planner_td2026_{datetime.today().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
    with col_exp2:
        if not wl.empty:
            wl_csv = wl.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇ Descargar tabla de carga (CSV)",
                data=wl_csv,
                file_name=f"carga_equipo_{datetime.today().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )

    # ── REQ 4: Capacidad del Equipo ──────────────────────────────────────────
    render_capacidad_equipo(wl)

    # ── Botón de informe PDF ─────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:11px;font-weight:700;letter-spacing:1.2px;"
        "text-transform:uppercase;color:#8fa0b8;border-bottom:1px solid #e2e8f0;"
        "padding-bottom:6px;margin:1.4rem 0 .9rem;'>📄 Exportar Informe</div>",
        unsafe_allow_html=True,
    )
    _skpis_oper = calculate_strategic_kpis()
    render_pdf_download_button(_skpis_oper, df, key_suffix="operational")

    st.caption("Dashboard TD 2026 · Transformación Digital · Datos de Microsoft Planner")


# ─────────────────────────────────────────────────────────────────────────────
# 11. SESSION STATE — PATRÓN _sd (PERSISTENCIA GARANTIZADA ENTRE VISTAS)
# ─────────────────────────────────────────────────────────────────────────────
def init_session_state():
    """
    SOLUCIÓN CORRECTA AL PROBLEMA DE PERSISTENCIA EN STREAMLIT:
    ────────────────────────────────────────────────────────────
    Streamlit borra del session_state cualquier clave cuyo widget (key=) no
    se renderizó en el ciclo actual.  Al cambiar de vista, los widgets de la
    otra vista no se renderizan → sus claves desaparecen.

    FIX: guardar TODOS los valores en st.session_state["_sd"] — un dict
    Python plano.  Streamlit NUNCA borra keys que no son de widgets.
    Los widgets usan key="w_<nombre>" y sincronizan a _sd inmediatamente.
    """
    if "_sd" not in st.session_state:
        st.session_state["_sd"] = {
            # ── Navegación ─────────────────────────────────────────────────
            "nav_vista": "🟢  Control Operativo",

            # ── REQ 6: Sidebar toggle ───────────────────────────────────────
            "sidebar_visible": True,

            # ── REQ 1: Histórico de reportes mensuales ──────────────────────
            # Estructura: {"2026-01": df_enero, "2026-02": df_febrero, ...}
            "historial_reportes": {},
            "mes_activo": None,         # clave del mes seleccionado
            "historial_meta": {},       # {"2026-01": {"missing_cols":[], ...}}

            # ── Eficiencia Operativa ────────────────────────────────────────
            "eo_meta":        20,
            "eo_completados": 0,

            # ── Datos Confiables ────────────────────────────────────────────
            "dc_meta":        5,
            "dc_completados": 0,

            # ── Excelencia ERP ──────────────────────────────────────────────
            "erp_meta":        10,
            "erp_completados": 0,

            # ── Integración ─────────────────────────────────────────────────
            "int_meta":        5,
            "int_completadas": 0,

            # ── Seguridad de la Información ─────────────────────────────────
            "seg_meta":        80,   # % objetivo (ej: llegar a 80%)
            "seg_completados": 0,    # % actual alcanzado

            # ── Hitos estratégicos ──────────────────────────────────────────
            "hitos_tabla": pd.DataFrame({
                "Objetivo Estratégico": [
                    "Excelencia ERP", "Eficiencia Operativa",
                    "Seguridad de la Información", "Datos Confiables", "Integración",
                ],
                "Hito": [
                    "Cierre módulo de compras",
                    "Automatización proceso nómina",
                    "Implementación MDM corporativo",
                    "Tablero de calidad de datos",
                    "API hub empresarial",
                ],
                # Fechas como objetos date — compatible con DateColumn de Streamlit
                "Fecha": pd.to_datetime(["2026-03-31","2026-03-31","2026-06-30","2026-06-30","2026-09-30"]).date.tolist(),
                "Responsable": ["Jose Tellez","Lizeth Castro","Viviana Gallego","Diego Barahona","Jorge Villarraga"],
                "Estado (%)":  [40, 60, 20, 50, 10],
                "Comentario":  ["En desarrollo","En pruebas","Por iniciar","En análisis","Por definir"],
            }),

            # ── Entregables por objetivo ────────────────────────────────────
            "entregables_tabla": pd.DataFrame({
                "Objetivo": [
                    "Excelencia ERP", "Excelencia ERP",
                    "Eficiencia Operativa", "Eficiencia Operativa",
                    "Seguridad Info.", "Seguridad Info.",
                    "Datos Confiables", "Datos Confiables",
                    "Integración",
                ],
                "Entregable": [
                    "Documento config. módulo compras",
                    "Manual usuario cierre contable",
                    "Flujo automatizado de nómina",
                    "Reporte KPI operativos mensual",
                    "Política gestión MDM aprobada",
                    "Plan respuesta incidentes v2",
                    "Diccionario de datos corporativo",
                    "Dashboard calidad de datos v1",
                    "Especificación API hub empresarial",
                ],
                "Responsable": [
                    "Jose Tellez","Jose Tellez",
                    "Lizeth Castro","Lizeth Castro",
                    "Viviana Gallego","Viviana Gallego",
                    "Diego Barahona","Diego Barahona",
                    "Jorge Villarraga",
                ],
                "Fecha Límite": pd.to_datetime([
                    "2026-03-31","2026-04-30",
                    "2026-03-31","2026-05-31",
                    "2026-06-30","2026-08-31",
                    "2026-04-30","2026-06-30",
                    "2026-09-30",
                ]).date.tolist(),
                "Prioridad": ["Alta","Media","Alta","Media","Alta","Media","Alta","Media","Alta"],
                "Estado": ["En curso","Pendiente","En curso","Pendiente","Pendiente","Pendiente","En curso","Pendiente","Pendiente"],
                "% Avance": [60, 0, 40, 0, 10, 0, 35, 0, 5],
            }),
        }
        # REQ 3: Al crear _sd por primera vez, cargar valores guardados en JSON
        # si el archivo existe. Esto restaura la memoria entre reinicios.
        _saved = load_kpis_from_json()
        if _saved:
            _apply_json_to_sd(st.session_state["_sd"], _saved)


# ─────────────────────────────────────────────────────────────────────────────
# 12. CÁLCULO DE KPIs ESTRATÉGICOS
# ─────────────────────────────────────────────────────────────────────────────
def calculate_strategic_kpis() -> dict:
    """Lee de _sd — nunca de keys sueltos del session_state."""
    sd = st.session_state.get("_sd", {})

    def _pct(comp, meta):
        m = max(int(meta), 1)
        return min(round(max(int(comp), 0) / m * 100, 1), 100)

    p_eo  = _pct(sd.get("eo_completados", 0),  sd.get("eo_meta", 20))
    p_dc  = _pct(sd.get("dc_completados", 0),  sd.get("dc_meta", 5))
    p_erp = _pct(sd.get("erp_completados", 0), sd.get("erp_meta", 10))
    p_int = _pct(sd.get("int_completadas", 0),  sd.get("int_meta", 5))
    # Seguridad: comp es % directo (0–100), meta es el objetivo % a alcanzar
    p_seg = _pct(sd.get("seg_completados", 0),  sd.get("seg_meta", 80))

    global_pct = round((p_eo + p_dc + p_erp + p_int + p_seg) / 5, 1)

    return {
        "Eficiencia Operativa":        {"pct": p_eo,  "meta": sd.get("eo_meta", 20),
                                        "avance": sd.get("eo_completados", 0), "unit": "procesos"},
        "Datos Confiables":            {"pct": p_dc,  "meta": sd.get("dc_meta", 5),
                                        "avance": sd.get("dc_completados", 0), "unit": "procesos"},
        "Excelencia ERP":              {"pct": p_erp, "meta": sd.get("erp_meta", 10),
                                        "avance": sd.get("erp_completados", 0), "unit": "mejoras"},
        "Integración":                 {"pct": p_int, "meta": sd.get("int_meta", 5),
                                        "avance": sd.get("int_completadas", 0), "unit": "integ."},
        "Seguridad de la Información": {"pct": p_seg, "meta": sd.get("seg_meta", 80),
                                        "avance": sd.get("seg_completados", 0), "unit": "%"},
        "_global": global_pct,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 13. HELPERS VISUALES
# ─────────────────────────────────────────────────────────────────────────────
def semaforo_badge(pct: float) -> str:
    if pct > 80:
        return '<span class="badge-green">🟢 En meta</span>'
    elif pct >= 50:
        return '<span class="badge-yellow">🟡 Seguimiento</span>'
    return '<span class="badge-red">🔴 En riesgo</span>'


def semaforo_color(pct: float) -> str:
    if pct > 80:  return COLORS["green"]
    if pct >= 50: return COLORS["yellow"]
    return COLORS["red"]


def obj_card_html(titulo: str, pct: float, meta_str: str, color: str) -> str:
    """Legacy helper — usado por algunos places."""
    badge = semaforo_badge(pct)
    bar_w = min(int(pct), 100)
    bar_c = semaforo_color(pct)
    return f"""
    <div class="obj-card">
      <div class="obj-card-accent" style="background:{color};"></div>
      <div class="obj-label">{titulo}</div>
      <div class="obj-pct" style="color:{color};">{pct:.1f}%</div>
      <div style="background:#f1f5f9;border-radius:6px;height:6px;margin:8px 0;">
        <div style="background:{bar_c};width:{bar_w}%;height:6px;border-radius:6px;"></div>
      </div>
      {badge}
      <div class="obj-meta">{meta_str}</div>
    </div>"""


def _sec_header(icon: str, text: str):
    st.markdown(
        f"<div style='font-size:11px;font-weight:700;letter-spacing:1.2px;"
        f"text-transform:uppercase;color:#8fa0b8;border-bottom:1px solid #e2e8f0;"
        f"padding-bottom:6px;margin:1.4rem 0 .9rem;'>{icon} {text}</div>",
        unsafe_allow_html=True,
    )


def _section_divider(emoji: str, titulo: str):
    st.markdown(
        f"<div style='font-size:11px;font-weight:700;text-transform:uppercase;"
        f"letter-spacing:1px;color:#3b82f6;padding:8px 0 5px;border-bottom:"
        f"2px solid #dbeafe;margin-bottom:10px;'>{emoji} {titulo}</div>",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 14. GRÁFICOS ESTRATÉGICOS
# ─────────────────────────────────────────────────────────────────────────────
def chart_barras_objetivos(kpis: dict) -> go.Figure:
    """
    REQ 1/2: Gráfico de barras horizontales ejecutivo — reemplaza el radar.
    Muestra % de cumplimiento de cada objetivo con colores semáforo y línea de meta.
    """
    OBJS = ["Eficiencia Operativa", "Datos Confiables", "Excelencia ERP",
            "Integración", "Seguridad de la Información"]
    OBJ_COLORS_MAP = {
        "Eficiencia Operativa":        COLORS["green"],
        "Datos Confiables":            COLORS["purple"],
        "Excelencia ERP":              COLORS["primary"],
        "Integración":                 COLORS["cyan"],
        "Seguridad de la Información": COLORS["red"],
    }
    vals   = [kpis[o]["pct"] for o in OBJS]
    # Semáforo por barra
    bar_colors = [
        semaforo_color(v) for v in vals
    ]

    fig = go.Figure()
    # Barras de fondo (pista 100%)
    fig.add_trace(go.Bar(
        x=[100]*len(OBJS), y=OBJS, orientation="h",
        marker=dict(color="#f1f5f9", line=dict(width=0)),
        showlegend=False, hoverinfo="skip",
    ))
    # Barras de avance
    fig.add_trace(go.Bar(
        x=vals, y=OBJS, orientation="h",
        marker=dict(color=bar_colors, line=dict(width=0)),
        text=[f"  {v:.1f}%" for v in vals],
        textposition="outside",
        textfont=dict(size=13, family="Inter, sans-serif", color="#334155"),
        hovertemplate="%{y}: <b>%{x:.1f}%</b><extra></extra>",
        showlegend=False,
    ))
    fig.add_vline(x=80, line_dash="dot", line_color="#94a3b8", line_width=1.5,
                  annotation_text="Meta 80%", annotation_position="top right",
                  annotation_font=dict(size=10, color="#94a3b8"))
    fig.update_layout(
        barmode="overlay",
        xaxis=dict(range=[0, 125], showgrid=False, ticksuffix="%",
                   tickfont=dict(size=10, color="#8fa0b8"), zeroline=False),
        yaxis=dict(showgrid=False, tickfont=dict(size=13, color="#334155"), automargin=True),
        margin=dict(l=0, r=70, t=10, b=10),
        plot_bgcolor="white", paper_bgcolor="white",
        height=300,
        font=dict(family="Inter, sans-serif"),
    )
    return fig


def chart_reqs_por_categoria(df: pd.DataFrame) -> go.Figure:
    counts = df.groupby("categoria").size().reset_index(name="n").sort_values("n", ascending=True)
    colors_list = [CATEGORY_COLORS.get(c, COLORS["gray"]) for c in counts["categoria"]]
    fig = go.Figure(go.Bar(
        x=counts["n"], y=counts["categoria"], orientation="h",
        marker=dict(color=colors_list),
        text=counts["n"], textposition="outside",
        hovertemplate="%{y}: <b>%{x}</b><extra></extra>",
    ))
    fig.update_layout(
        xaxis=dict(showgrid=False, tickfont=dict(size=10)),
        yaxis=dict(tickfont=dict(size=11)),
        margin=dict(l=10, r=30, t=10, b=10),
        plot_bgcolor="white", paper_bgcolor="white",
        height=200, showlegend=False,
    )
    return fig


def chart_reqs_por_area(df: pd.DataFrame) -> go.Figure:
    area_counts = (
        df["etiquetas"].dropna()
        .str.split(",").explode().str.strip()
        .loc[lambda s: ~s.isin(list(CATEGORY_COLORS.keys()) + [""])]
        .value_counts().head(10).reset_index()
    )
    area_counts.columns = ["area", "n"]
    fig = go.Figure(go.Bar(
        x=area_counts["n"],
        y=area_counts["area"],
        orientation="h",
        marker=dict(color=COLORS["cyan"]),
        text=area_counts["n"], textposition="outside",
    ))
    fig.update_layout(
        xaxis=dict(showgrid=False, tickfont=dict(size=10)),
        yaxis=dict(tickfont=dict(size=11)),
        margin=dict(l=10, r=30, t=10, b=10),
        plot_bgcolor="white", paper_bgcolor="white",
        height=260, showlegend=False,
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# 15. VISTA ESTRATÉGICA — COMPONENTES
# ─────────────────────────────────────────────────────────────────────────────

# Configuración de objetivos: (meta_key, comp_key, comp_label, max_meta, max_comp, is_pct)
_OBJ_CFG = {
    "Eficiencia Operativa":        ("eo_meta",  "eo_completados",  "Completados", 999, 9999, False),
    "Datos Confiables":            ("dc_meta",  "dc_completados",  "Completados", 999, 9999, False),
    "Excelencia ERP":              ("erp_meta", "erp_completados", "Completados", 999, 9999, False),
    "Integración":                 ("int_meta", "int_completadas", "Completadas", 999, 9999, False),
    "Seguridad de la Información": ("seg_meta", "seg_completados", "% Actual",   100,  100, True),
}

_OBJS_ORDER = [
    "Eficiencia Operativa", "Datos Confiables", "Excelencia ERP",
    "Integración", "Seguridad de la Información",
]

_OBJ_COLORS = {
    "Eficiencia Operativa":        COLORS["green"],
    "Datos Confiables":            COLORS["purple"],
    "Excelencia ERP":              COLORS["primary"],
    "Integración":                 COLORS["cyan"],
    "Seguridad de la Información": COLORS["red"],
}


def _executive_kpi_card_html(obj: str, pct: float, color: str, data: dict) -> str:
    """
    REQ 2: Tarjeta ejecutiva completa para un objetivo estratégico.
    Incluye: nombre, %, barra de progreso, semáforo, meta/avance.
    Diseño optimizado para audiencias directivas — legible en < 5 segundos.
    """
    bar_c = semaforo_color(pct)
    bar_w = min(int(pct), 100)
    # Segmentos de la barra (10 bloques de 10%)
    filled = int(bar_w / 10)
    bar_html = "".join(
        f"<span style='display:inline-block;width:9%;height:8px;border-radius:3px;"
        f"background:{bar_c};margin-right:1%;opacity:{0.9 if i < filled else 0.2};'></span>"
        for i in range(10)
    )

    if pct > 80:
        badge_bg, badge_c, badge_txt = "#dcfce7", "#15803d", "🟢 En meta"
        icon = "✅"
    elif pct >= 50:
        badge_bg, badge_c, badge_txt = "#fef9c3", "#a16207", "🟡 Seguimiento"
        icon = "⚠️"
    else:
        badge_bg, badge_c, badge_txt = "#fee2e2", "#b91c1c", "🔴 En riesgo"
        icon = "🚨"

    unit   = data.get("unit", "")
    meta   = data.get("meta", "—")
    avance = data.get("avance", 0)
    if unit == "%":
        progress_txt = f"{avance}% alcanzado · Meta {meta}%"
    else:
        progress_txt = f"{avance} / {meta} {unit}"

    # Nombre corto para el encabezado de la tarjeta
    short = (obj
             .replace("de la Información", "Info.")
             .replace("Operativa", "Op.")
             .replace("Excelencia ", "")
             .replace("Datos ", "")
             .replace("Integración", "Integración"))

    return f"""
<div style="background:white;border:1px solid #e2e8f0;
            border-top:4px solid {color};border-radius:14px;
            padding:18px 16px 14px;box-shadow:0 2px 8px rgba(0,0,0,.06);
            display:flex;flex-direction:column;gap:8px;min-height:200px;">

  <!-- Encabezado: ícono semáforo + nombre -->
  <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:4px;">
    <div style="font-size:9px;font-weight:800;text-transform:uppercase;
                letter-spacing:1.1px;color:#94a3b8;line-height:1.4;flex:1;">{obj}</div>
    <div style="font-size:14px;">{icon}</div>
  </div>

  <!-- Porcentaje grande -->
  <div style="font-size:2.6rem;font-weight:900;line-height:1;color:{color};">
    {pct:.1f}%
  </div>

  <!-- Barra de progreso segmentada -->
  <div style="display:flex;align-items:center;gap:0;width:100%;margin:2px 0;">
    {bar_html}
  </div>

  <!-- Texto de progreso -->
  <div style="font-size:11px;font-weight:600;color:#475569;">{progress_txt}</div>

  <!-- Badge semáforo -->
  <div style="margin-top:auto;">
    <span style="display:inline-block;background:{badge_bg};color:{badge_c};
                 font-size:10px;font-weight:700;padding:3px 10px;
                 border-radius:20px;">{badge_txt}</span>
  </div>
</div>"""


def render_strategic_kpis(skpis: dict, objs_order: list, obj_colors: dict):
    """
    SECCIÓN 1 — Tarjetas ejecutivas (REQ 2) + edición inline + botón guardar (REQ 3/4).
    Todos los valores se guardan en _sd → persisten entre vistas.
    Al presionar 'Guardar cambios' se escribe el JSON y se añade una fila al CSV histórico.
    """
    _sec_header("📊", "Cumplimiento por Objetivo Estratégico")

    sd         = st.session_state["_sd"]
    global_pct = skpis["_global"]
    g_icon     = "🟢 En meta" if global_pct > 80 else ("🟡 Seguimiento" if global_pct >= 50 else "🔴 En riesgo")

    # ── Fila 1: 5 tarjetas ejecutivas (REQ 2) ─────────────────────────────
    card_cols = st.columns(5)
    for i, obj in enumerate(objs_order):
        color = obj_colors[obj]
        pct   = skpis[obj]["pct"]
        data  = skpis[obj]
        with card_cols[i]:
            st.markdown(_executive_kpi_card_html(obj, pct, color, data),
                        unsafe_allow_html=True)

    # ── KPI Global debajo de las tarjetas ─────────────────────────────────
    st.markdown(
        f"<div style='background:linear-gradient(135deg,#1d6af5 0%,#0891b2 100%);"
        f"border-radius:12px;padding:14px 24px;margin:14px 0 6px;"
        f"display:flex;align-items:center;justify-content:space-between;"
        f"box-shadow:0 4px 16px rgba(29,106,245,.22);'>"
        f"<div style='display:flex;align-items:center;gap:16px;'>"
        f"<div>"
        f"<div style='font-size:8px;font-weight:800;text-transform:uppercase;"
        f"letter-spacing:1.2px;color:rgba(255,255,255,.65);'>Cumplimiento Estratégico Global · 5 Objetivos · TD 2026</div>"
        f"<div style='font-size:2rem;font-weight:900;color:white;line-height:1.1;'>{global_pct:.1f}%</div>"
        f"</div></div>"
        f"<div style='background:rgba(255,255,255,.18);color:white;font-size:11px;"
        f"font-weight:700;padding:5px 16px;border-radius:20px;'>{g_icon}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div style='margin-top:.6rem'></div>", unsafe_allow_html=True)

    # ── Fila 2: Paneles de edición por objetivo ────────────────────────────
    with st.expander("✏️ Editar metas y avances", expanded=False):
        st.markdown(
            "<div style='font-size:12px;color:#64748b;margin-bottom:10px;'>"
            "Ajusta los valores de cada objetivo. Presiona <b>💾 Guardar cambios</b> "
            "para persistir en disco y registrar el histórico.</div>",
            unsafe_allow_html=True,
        )
        edit_cols = st.columns(5)
        for i, obj in enumerate(objs_order):
            meta_k, comp_k, comp_lbl, max_m, max_c, is_pct = _OBJ_CFG[obj]
            color = obj_colors[obj]

            with edit_cols[i]:
                st.markdown(
                    f"<div style='font-size:9px;font-weight:800;text-transform:uppercase;"
                    f"letter-spacing:1px;color:{color};margin-bottom:6px;border-bottom:"
                    f"2px solid {color};padding-bottom:4px;'>{obj.split()[0]} {obj.split()[1] if len(obj.split())>1 else ''}</div>",
                    unsafe_allow_html=True,
                )
                lbl_m = "Meta %" if is_pct else "Meta"
                lbl_c = "Actual %" if is_pct else comp_lbl
                v_meta = st.number_input(
                    lbl_m, min_value=1, max_value=max_m,
                    value=int(sd.get(meta_k, 1)),
                    step=1, key=f"w_{meta_k}",
                    label_visibility="visible",
                )
                sd[meta_k] = v_meta

                v_comp = st.number_input(
                    lbl_c, min_value=0, max_value=max_c,
                    value=int(sd.get(comp_k, 0)),
                    step=1, key=f"w_{comp_k}",
                    label_visibility="visible",
                )
                sd[comp_k] = v_comp

        # ── REQ 3 + 4: Botón de guardado con feedback ─────────────────────
        st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)
        col_save, col_msg = st.columns([1, 3])
        with col_save:
            if st.button("💾 Guardar cambios", key="btn_save_kpis",
                         type="primary", use_container_width=True):
                ok_json = save_kpis_to_json(sd)
                ok_hist = append_history_row(sd)
                if ok_json:
                    st.session_state["_kpi_save_msg"] = (
                        "success",
                        f"✅ Guardado en **data/strategic_kpis.json** · "
                        f"{datetime.today().strftime('%d/%m/%Y %H:%M')}",
                    )
                else:
                    st.session_state["_kpi_save_msg"] = (
                        "warning",
                        "⚠️ No se pudo escribir en disco (entorno de solo lectura). "
                        "Los datos persisten en memoria durante la sesión.",
                    )
        with col_msg:
            msg = st.session_state.get("_kpi_save_msg")
            if msg:
                lvl, txt = msg
                if lvl == "success":
                    st.success(txt)
                else:
                    st.warning(txt)


def render_global_vision(skpis: dict):
    """
    SECCIÓN 2 — Gráfico de barras ejecutivo a ancho completo.
    REQ 1: El radar estratégico fue eliminado. Esta sección muestra únicamente
    el gráfico de barras de cumplimiento que es más claro para gerencia.
    """
    _sec_header("🎯", "Perfil de Cumplimiento por Objetivo Estratégico")

    col_chart, col_global = st.columns([3, 1])
    with col_chart:
        st.markdown(
            "<div style='font-size:12px;font-weight:600;color:#475569;margin-bottom:4px;'>"
            "% de cumplimiento vs meta (línea punteada = meta 80%)</div>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(chart_barras_objetivos(skpis), use_container_width=True, key="ev_barras")

    with col_global:
        global_pct = skpis["_global"]
        g_color    = semaforo_color(global_pct)
        g_icon     = "🟢 En meta" if global_pct > 80 else ("🟡 Seguimiento" if global_pct >= 50 else "🔴 En riesgo")
        # Mini resumen de semáforos
        objs = ["Eficiencia Operativa","Datos Confiables","Excelencia ERP",
                "Integración","Seguridad de la Información"]
        en_meta    = sum(1 for o in objs if skpis[o]["pct"] > 80)
        seguim     = sum(1 for o in objs if 50 <= skpis[o]["pct"] <= 80)
        en_riesgo  = sum(1 for o in objs if skpis[o]["pct"] < 50)
        st.markdown(
            f"<div style='background:linear-gradient(160deg,#1d6af5 0%,#0891b2 100%);"
            f"border-radius:12px;padding:18px 14px;text-align:center;"
            f"box-shadow:0 4px 18px rgba(29,106,245,.28);'>"
            f"<div style='font-size:9px;font-weight:800;color:rgba(255,255,255,.7);"
            f"text-transform:uppercase;letter-spacing:1.2px;margin-bottom:8px;'>"
            f"Cumplimiento Global</div>"
            f"<div style='font-size:2.8rem;font-weight:900;color:white;line-height:1;"
            f"margin-bottom:8px;'>{global_pct:.1f}%</div>"
            f"<div style='background:rgba(255,255,255,.2);color:white;font-size:10px;"
            f"font-weight:700;padding:3px 10px;border-radius:20px;margin-bottom:12px;'>"
            f"{g_icon}</div>"
            f"<div style='display:flex;justify-content:space-around;margin-top:8px;'>"
            f"<div style='text-align:center;'>"
            f"<div style='font-size:1.4rem;font-weight:900;color:#4ade80;'>{en_meta}</div>"
            f"<div style='font-size:8px;color:rgba(255,255,255,.6);'>En meta</div></div>"
            f"<div style='text-align:center;'>"
            f"<div style='font-size:1.4rem;font-weight:900;color:#fde047;'>{seguim}</div>"
            f"<div style='font-size:8px;color:rgba(255,255,255,.6);'>Seguim.</div></div>"
            f"<div style='text-align:center;'>"
            f"<div style='font-size:1.4rem;font-weight:900;color:#f87171;'>{en_riesgo}</div>"
            f"<div style='font-size:8px;color:rgba(255,255,255,.6);'>Riesgo</div></div>"
            f"</div></div>",
            unsafe_allow_html=True,
        )


def _safe_date_df(df: pd.DataFrame, date_cols: list) -> pd.DataFrame:
    """Convierte columnas string/timestamp a objetos date.date para compatibilidad
    con st.column_config.DateColumn — evita StreamlitAPIException."""
    df = df.copy()
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.date
    return df


def render_strategic_configuration():
    """
    SECCIÓN 3 — Hitos estratégicos + Tabla de Entregables editables.
    Fix DateColumn: fechas convertidas a date.date antes de pasar al editor.
    """
    sd = st.session_state["_sd"]

    OBJS_OPTS = [
        "Eficiencia Operativa", "Datos Confiables", "Excelencia ERP",
        "Integración", "Seguridad de la Información",
    ]
    PRIORIDAD_OPTS = ["Alta", "Media", "Baja"]
    ESTADO_OPTS    = ["Pendiente", "En curso", "Completado", "Bloqueado"]

    # ══ TAB 1: Hitos estratégicos ══════════════════════════════════════════
    tab_hitos, tab_entregables = st.tabs([
        "📍 Hitos Estratégicos",
        "📦 Entregables por Objetivo",
    ])

    # ─── Hitos ─────────────────────────────────────────────────────────────
    with tab_hitos:
        st.markdown(
            "<div style='font-size:12px;color:#64748b;margin:6px 0 10px;'>"
            "Registra y actualiza los hitos clave de cada objetivo. "
            "Usa <b>+ Agregar fila</b> para nuevos hitos.</div>",
            unsafe_allow_html=True,
        )

        # FIX ERROR: convertir Fecha (string) → date.date antes del editor
        hitos_raw = sd.get("hitos_tabla", pd.DataFrame({
            "Objetivo Estratégico": [], "Hito": [], "Fecha": [],
            "Responsable": [], "Estado (%)": [], "Comentario": [],
        }))
        hitos_df = _safe_date_df(hitos_raw, ["Fecha"])

        edited_h = st.data_editor(
            hitos_df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Objetivo Estratégico": st.column_config.SelectboxColumn(
                    "Objetivo", options=OBJS_OPTS, width="medium", required=True),
                "Hito":        st.column_config.TextColumn("Hito / Entregable", width="large"),
                "Fecha":       st.column_config.DateColumn("Fecha límite"),
                "Responsable": st.column_config.TextColumn("Responsable", width="medium"),
                "Estado (%)":  st.column_config.NumberColumn(
                    "Estado %", min_value=0, max_value=100, step=5, format="%d%%"),
                "Comentario":  st.column_config.TextColumn("Comentario", width="medium"),
            },
            key="w_hitos_editor",
            height=280,
        )
        sd["hitos_tabla"] = edited_h

        # Resumen por objetivo
        if len(edited_h) > 0:
            st.markdown("<br>", unsafe_allow_html=True)
            resumen = (
                edited_h.groupby("Objetivo Estratégico")["Estado (%)"]
                .mean().round(1).reset_index()
                .rename(columns={"Estado (%)": "Avance Promedio %"})
                .sort_values("Avance Promedio %", ascending=False)
                .reset_index(drop=True)
            )
            resumen["Estado"] = resumen["Avance Promedio %"].apply(
                lambda v: "🟢 En meta" if v > 80 else ("🟡 Seguimiento" if v >= 50 else "🔴 En riesgo")
            )
            st.dataframe(
                resumen, use_container_width=True, hide_index=True, height=200,
                column_config={
                    "Objetivo Estratégico": st.column_config.TextColumn("Objetivo", width="large"),
                    "Avance Promedio %": st.column_config.ProgressColumn(
                        "Avance Promedio", min_value=0, max_value=100, format="%.1f%%"),
                    "Estado": st.column_config.TextColumn("Estado", width="small"),
                },
            )

    # ─── Entregables ────────────────────────────────────────────────────────
    with tab_entregables:
        st.markdown(
            "<div style='font-size:12px;color:#64748b;margin:6px 0 10px;'>"
            "Gestiona los principales entregables de cada objetivo estratégico. "
            "Edita en línea · Usa <b>+ Agregar fila</b> para nuevos entregables.</div>",
            unsafe_allow_html=True,
        )

        # FIX: convertir Fecha Límite → date.date
        entregables_raw = sd.get("entregables_tabla", pd.DataFrame({
            "Objetivo": [], "Entregable": [], "Responsable": [],
            "Fecha Límite": [], "Prioridad": [], "Estado": [], "% Avance": [],
        }))
        entregables_df = _safe_date_df(entregables_raw, ["Fecha Límite"])

        edited_e = st.data_editor(
            entregables_df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Objetivo": st.column_config.SelectboxColumn(
                    "Objetivo Estratégico", options=OBJS_OPTS, width="medium", required=True),
                "Entregable":   st.column_config.TextColumn("Entregable", width="large"),
                "Responsable":  st.column_config.TextColumn("Responsable", width="medium"),
                "Fecha Límite": st.column_config.DateColumn("Fecha límite"),
                "Prioridad":    st.column_config.SelectboxColumn(
                    "Prioridad", options=PRIORIDAD_OPTS, width="small"),
                "Estado":       st.column_config.SelectboxColumn(
                    "Estado", options=ESTADO_OPTS, width="medium"),
                "% Avance":     st.column_config.NumberColumn(
                    "% Avance", min_value=0, max_value=100, step=5, format="%d%%"),
            },
            key="w_entregables_editor",
            height=340,
        )
        sd["entregables_tabla"] = edited_e

        # Mini dashboard de entregables
        if len(edited_e) > 0:
            st.markdown("<br>", unsafe_allow_html=True)
            ca, cb, cc, cd = st.columns(4)
            total_e     = len(edited_e)
            completados = (edited_e["Estado"] == "Completado").sum()
            en_curso    = (edited_e["Estado"] == "En curso").sum()
            alta_prio   = (edited_e.get("Prioridad","") == "Alta").sum() if "Prioridad" in edited_e.columns else 0
            ca.metric("Total entregables", total_e)
            cb.metric("✅ Completados", completados, f"{round(completados/max(total_e,1)*100,0):.0f}%")
            cc.metric("🔄 En curso", en_curso)
            cd.metric("🔴 Alta prioridad", alta_prio)


def _render_kpi_history():
    """
    REQ 4: Muestra el histórico de cambios de los indicadores estratégicos.
    Lee data/strategic_history.csv y lo presenta como tabla interactiva
    con gráfico de tendencia por objetivo.
    """
    hist_df = load_history_df()
    if hist_df.empty:
        return  # Sin historial aún → no mostrar la sección

    _sec_header("📋", "Histórico de Cambios en Indicadores Estratégicos")

    with st.expander(f"Ver histórico ({len(hist_df)} registros)", expanded=False):
        # Filtro por objetivo
        objs_disp = ["Todos"] + sorted(hist_df["objetivo"].unique().tolist())
        col_f, _ = st.columns([1, 3])
        with col_f:
            obj_filtro = st.selectbox(
                "Filtrar por objetivo", options=objs_disp, key="w_hist_filtro"
            )

        df_show = hist_df.copy()
        if obj_filtro != "Todos":
            df_show = df_show[df_show["objetivo"] == obj_filtro]

        df_show = df_show.sort_values("fecha", ascending=False).reset_index(drop=True)
        df_show["% cumpl."] = (df_show["avance"] / df_show["meta"].clip(lower=1) * 100).round(1).astype(str) + "%"

        # Formatear fecha para visualización
        try:
            df_show["fecha"] = pd.to_datetime(df_show["fecha"]).dt.strftime("%d/%m/%Y %H:%M")
        except Exception:
            pass

        st.dataframe(
            df_show[["fecha","objetivo","meta","avance","% cumpl."]].rename(columns={
                "fecha": "Fecha", "objetivo": "Objetivo", "meta": "Meta",
                "avance": "Avance", "% cumpl.": "% Cumpl.",
            }),
            use_container_width=True,
            hide_index=True,
            height=min(60 + 48 * len(df_show), 400),
        )

        # Descargar histórico como CSV
        csv_bytes = hist_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇ Descargar histórico (CSV)",
            data=csv_bytes,
            file_name=f"strategic_history_{datetime.today().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            key="dl_history_csv",
        )

        # Gráfico de tendencia de % cumplimiento por objetivo
        if len(hist_df) >= 2:
            st.markdown(
                "<div style='font-size:12px;font-weight:600;color:#334155;margin:10px 0 4px;'>"
                "Tendencia de cumplimiento por objetivo</div>",
                unsafe_allow_html=True,
            )
            trend_df = hist_df.copy()
            trend_df["pct"] = (trend_df["avance"] / trend_df["meta"].clip(lower=1) * 100).round(1)
            try:
                trend_df["fecha"] = pd.to_datetime(trend_df["fecha"])
            except Exception:
                pass

            fig_trend = go.Figure()
            obj_color_map = {
                "Eficiencia Operativa":        COLORS["green"],
                "Datos Confiables":            COLORS["purple"],
                "Excelencia ERP":              COLORS["primary"],
                "Integración":                 COLORS["cyan"],
                "Seguridad de la Información": COLORS["red"],
            }
            for obj in trend_df["objetivo"].unique():
                sub = trend_df[trend_df["objetivo"] == obj].sort_values("fecha")
                fig_trend.add_trace(go.Scatter(
                    x=sub["fecha"], y=sub["pct"],
                    mode="lines+markers",
                    name=obj,
                    line=dict(color=obj_color_map.get(obj, "#94a3b8"), width=2),
                    marker=dict(size=6),
                    hovertemplate=f"<b>{obj}</b><br>%{{x}}<br>%{{y:.1f}}%<extra></extra>",
                ))
            fig_trend.add_hline(y=80, line_dash="dot", line_color="#94a3b8",
                                annotation_text="Meta 80%",
                                annotation_font=dict(size=9, color="#94a3b8"))
            fig_trend.update_layout(
                xaxis=dict(title=None, tickfont=dict(size=10)),
                yaxis=dict(title=None, ticksuffix="%", range=[0, 110],
                           showgrid=True, gridcolor="#f1f5f9"),
                legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center",
                            font=dict(size=10)),
                plot_bgcolor="white", paper_bgcolor="white",
                margin=dict(l=10, r=20, t=10, b=50),
                height=280,
                font=dict(family="Inter, sans-serif", size=11),
            )
            st.plotly_chart(fig_trend, use_container_width=True, key="hist_trend_chart")


# ─────────────────────────────────────────────────────────────────────────────
# 16. VISTA ESTRATÉGICA — ORQUESTADOR
# ─────────────────────────────────────────────────────────────────────────────
def create_executive_view(df: pd.DataFrame):
    """Vista Indicadores Estratégicos — Vicepresidencia TD 2026."""

    # ── Header ─────────────────────────────────────────────────────────────
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown(
            "<h2 style='color:#0f1c2e;font-weight:900;margin-bottom:2px;font-size:1.8rem;'>"
            "🔵 Indicadores Estratégicos — Vicepresidencia</h2>"
            f"<p style='color:#64748b;font-size:13px;margin-top:0;'>"
            f"Panel editable de metas y avances · TD 2026 · "
            f"Actualizado: {datetime.today().strftime('%d/%m/%Y')}</p>",
            unsafe_allow_html=True,
        )
    with col_h2:
        if not df.empty:
            st.markdown(
                f"<div style='text-align:right;padding-top:18px;'>"
                f"<span style='background:#eff6ff;color:#1d6af5;font-size:12px;"
                f"font-weight:700;padding:6px 14px;border-radius:20px;'>"
                f"📂 {len(df)} reqs. del Excel</span></div>",
                unsafe_allow_html=True,
            )

    # ── Calcular KPIs ──────────────────────────────────────────────────────
    skpis = calculate_strategic_kpis()

    # ══ SECCIÓN 1 — KPIs + edición inline ════════════════════════════════
    render_strategic_kpis(skpis, _OBJS_ORDER, _OBJ_COLORS)

    # Recalcular tras edición del ciclo actual
    skpis = calculate_strategic_kpis()

    # ══ SECCIÓN 2 — Radar + Barras ════════════════════════════════════════
    render_global_vision(skpis)

    # ══ SECCIÓN 3 — Hitos ═════════════════════════════════════════════════
    render_strategic_configuration()

    # ══ Indicadores de portafolio (si hay Excel) ══════════════════════════
    if not df.empty:
        _sec_header("📂", "Indicadores de Portafolio — Datos del Excel")
        total = len(df)
        comp  = (df["progreso"] == "Completado").sum()
        sin_a = (df["asignado_raw"] == "Sin asignar").sum()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Requerimientos", total)
        c2.metric("Categorías estratégicas", df["categoria"].nunique())
        c3.metric("Completados", comp, f"{round(comp/total*100,1)}% del total")
        c4.metric("Sin asignar", sin_a, delta_color="inverse")

        st.markdown("<br>", unsafe_allow_html=True)
        col_rcat, col_rarea = st.columns([1, 1.6])
        with col_rcat:
            st.markdown(
                "<div style='font-size:12px;font-weight:600;color:#334155;margin-bottom:4px;'>"
                "Reqs. por Categoría Estratégica</div>", unsafe_allow_html=True)
            st.plotly_chart(chart_reqs_por_categoria(df), use_container_width=True, key="ev_cat")
        with col_rarea:
            st.markdown(
                "<div style='font-size:12px;font-weight:600;color:#334155;margin-bottom:4px;'>"
                "Reqs. por Área de Negocio</div>", unsafe_allow_html=True)
            st.plotly_chart(chart_reqs_por_area(df), use_container_width=True, key="ev_area")

    # ── Botón de informe PDF ─────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)

    # REQ 4: Histórico de cambios
    _render_kpi_history()

    _sec_header("📄", "Exportar Informe")
    skpis_for_pdf = calculate_strategic_kpis()
    render_pdf_download_button(skpis_for_pdf, df, key_suffix="strategic")

    st.caption("Vista Estratégica TD 2026 · Vicepresidencia Transformación Digital · "
               "Metas editables en tiempo real")

# prueba deploy

# ─────────────────────────────────────────────────────────────────────────────
# REQ 4: CAPACIDAD DEL EQUIPO — helpers y render
# ─────────────────────────────────────────────────────────────────────────────

def render_capacidad_equipo(wl: pd.DataFrame):
    """
    REQ 4: Indicador de capacidad del equipo vs carga de trabajo.
    Muestra utilización por especialista con capacidad configurable.
    """
    if wl.empty:
        st.info("Sin datos de carga de equipo.")
        return

    sd = st.session_state["_sd"]

    _sec_header("⚡", "Capacidad del Equipo vs Carga de Trabajo")

    col_cfg, _ = st.columns([1, 3])
    with col_cfg:
        cap_default = st.number_input(
            "Capacidad por especialista (reqs activos)",
            min_value=1, max_value=50,
            value=int(sd.get("capacidad_default", 8)),
            step=1, key="w_capacidad_default",
            help="Número máximo de requerimientos activos que puede manejar un especialista",
        )
        sd["capacidad_default"] = cap_default

    # Calcular utilización
    cap_df = wl.copy()
    cap_df = cap_df[cap_df["Especialista"] != "Sin asignar"]
    cap_df["Capacidad"] = cap_default
    cap_df["Utilización %"] = (cap_df["Carga Activa"] / cap_default * 100).round(1).clip(upper=150)

    def fmt_util(val):
        if val >= 100: return f"🔴 {val:.1f}%"
        if val >= 75:  return f"🟡 {val:.1f}%"
        return f"🟢 {val:.1f}%"

    cap_display = cap_df[["Especialista","Carga Activa","Capacidad","Utilización %"]].copy()
    cap_display["Utilización"] = cap_display["Utilización %"].apply(fmt_util)
    cap_display = cap_display.drop(columns=["Utilización %"])

    # KPI global
    global_util = cap_df["Utilización %"].mean() if not cap_df.empty else 0
    g_color = "#e03030" if global_util >= 100 else ("#d97706" if global_util >= 75 else "#0da063")
    g_icon  = "🔴" if global_util >= 100 else ("🟡" if global_util >= 75 else "🟢")

    c_kpi1, c_kpi2, c_kpi3, c_kpi4 = st.columns(4)
    c_kpi1.metric("Utilización Global", f"{global_util:.1f}%")
    sobrecargados = (cap_df["Utilización %"] >= 100).sum()
    en_limite     = ((cap_df["Utilización %"] >= 75) & (cap_df["Utilización %"] < 100)).sum()
    disponibles   = (cap_df["Utilización %"] < 75).sum()
    c_kpi2.metric("🔴 Sobrecargados", int(sobrecargados))
    c_kpi3.metric("🟡 En límite (≥75%)", int(en_limite))
    c_kpi4.metric("🟢 Con capacidad", int(disponibles))

    st.markdown(
        f"<div style='background:{g_color}22;border:1px solid {g_color}44;border-radius:8px;"
        f"padding:10px 16px;margin:8px 0 12px;font-size:13px;font-weight:600;color:{g_color};'>"
        f"{g_icon} Capacidad del equipo: <strong>{global_util:.1f}%</strong> de utilización promedio</div>",
        unsafe_allow_html=True,
    )

    # Tabla de utilización
    st.dataframe(cap_display, use_container_width=True, hide_index=True,
                 height=min(60 + 48 * len(cap_display), 420))

    # Gráfico de utilización
    if not cap_df.empty:
        top = cap_df.sort_values("Utilización %", ascending=True).tail(10)
        colors_util = [
            "#e03030" if v >= 100 else ("#d97706" if v >= 75 else "#0da063")
            for v in top["Utilización %"]
        ]
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=top["Utilización %"], y=top["Especialista"],
            orientation="h",
            marker_color=colors_util,
            marker_line_width=0,
            text=[f"{v:.1f}%" for v in top["Utilización %"]],
            textposition="outside",
            textfont=dict(size=11),
            cliponaxis=False,
            name="Utilización",
        ))
        fig.add_vline(x=100, line_dash="dot", line_color="#e03030",
                      annotation_text="Capacidad 100%",
                      annotation_font=dict(size=10, color="#e03030"))
        fig.add_vline(x=75, line_dash="dot", line_color="#d97706",
                      annotation_text="Alerta 75%",
                      annotation_position="bottom",
                      annotation_font=dict(size=10, color="#d97706"))
        fig.update_layout(
            xaxis=dict(title=None, ticksuffix="%", range=[0, max(top["Utilización %"].max() * 1.2, 120)],
                       showgrid=True, gridcolor="#f1f5f9"),
            yaxis=dict(title=None, tickfont=dict(size=11)),
            plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(l=10, r=60, t=10, b=10),
            height=max(280, 42 * len(top) + 40),
            font=dict(family="Inter, sans-serif", size=12),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True, key="cap_util_chart")


# ─────────────────────────────────────────────────────────────────────────────
# REQ 1/2/3: EVOLUCIÓN DEL PORTAFOLIO — helpers, gráficos y render principal
# ─────────────────────────────────────────────────────────────────────────────

MES_ES_FULL = {
    "01":"Enero","02":"Febrero","03":"Marzo","04":"Abril",
    "05":"Mayo","06":"Junio","07":"Julio","08":"Agosto",
    "09":"Septiembre","10":"Octubre","11":"Noviembre","12":"Diciembre",
}

def _mes_label(key: str) -> str:
    """'2026-03' → 'Mar 26'"""
    MES_SHORT = {"01":"Ene","02":"Feb","03":"Mar","04":"Abr",
                 "05":"May","06":"Jun","07":"Jul","08":"Ago",
                 "09":"Sep","10":"Oct","11":"Nov","12":"Dic"}
    try:
        yr  = key[2:4]
        mon = key[5:7]
        return f"{MES_SHORT.get(mon, mon)} '{yr}"
    except Exception:
        return key


def build_evolution_df() -> pd.DataFrame:
    """
    REQ 2: Construye un DataFrame de evolución mensual del portafolio.
    Una fila por mes cargado en historial_reportes.
    """
    sd = st.session_state.get("_sd", {})
    hist = sd.get("historial_reportes", {})
    if not hist:
        return pd.DataFrame()

    rows = []
    for mes_key in sorted(hist.keys()):
        df_mes = hist[mes_key]
        if df_mes.empty:
            continue
        total       = len(df_mes)
        completados = int((df_mes["progreso"] == "Completado").sum())
        en_curso    = int((df_mes["progreso"] == "En curso").sum())
        no_iniciado = int((df_mes["progreso"] == "No iniciado").sum())
        con_retraso = int(df_mes["retraso"].sum()) if "retraso" in df_mes.columns else 0
        pct_comp    = round(completados / total * 100, 1) if total > 0 else 0.0
        backlog     = total - completados

        rows.append({
            "Clave":         mes_key,
            "Mes":           _mes_label(mes_key),
            "Total":         total,
            "Completados":   completados,
            "En Curso":      en_curso,
            "No Iniciado":   no_iniciado,
            "Con Retraso":   con_retraso,
            "Backlog":       backlog,
            "% Completado":  pct_comp,
        })

    return pd.DataFrame(rows)


def chart_evolucion_completados(evo_df: pd.DataFrame) -> go.Figure:
    """Line chart de completados y velocidad de entrega mes a mes."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=evo_df["Mes"], y=evo_df["Completados"],
        mode="lines+markers+text",
        name="Completados acumulados",
        line=dict(color=COLORS["green"], width=2.5),
        marker=dict(size=8, color=COLORS["green"]),
        text=evo_df["Completados"],
        textposition="top center",
        textfont=dict(size=11),
    ))
    fig.add_trace(go.Scatter(
        x=evo_df["Mes"], y=evo_df["En Curso"],
        mode="lines+markers",
        name="En curso",
        line=dict(color=COLORS["yellow"], width=2, dash="dot"),
        marker=dict(size=7, color=COLORS["yellow"]),
    ))
    fig.update_layout(
        xaxis=dict(title=None, type="category", tickfont=dict(size=11)),
        yaxis=dict(title=None, showgrid=True, gridcolor="#f1f5f9", zeroline=False),
        legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=10, r=20, t=16, b=40),
        height=280, font=dict(family="Inter, sans-serif", size=12),
    )
    return fig


def chart_evolucion_backlog(evo_df: pd.DataFrame) -> go.Figure:
    """Line chart de evolución del backlog (no completados)."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=evo_df["Mes"], y=evo_df["Backlog"],
        mode="lines+markers+text",
        name="Backlog",
        fill="tozeroy",
        fillcolor="rgba(29,106,245,0.08)",
        line=dict(color=COLORS["primary"], width=2.5),
        marker=dict(size=8),
        text=evo_df["Backlog"],
        textposition="top center",
        textfont=dict(size=11),
    ))
    fig.add_trace(go.Bar(
        x=evo_df["Mes"], y=evo_df["No Iniciado"],
        name="No iniciados",
        marker_color="#cbd5e1",
        opacity=0.6,
    ))
    fig.update_layout(
        barmode="overlay",
        xaxis=dict(title=None, type="category", tickfont=dict(size=11)),
        yaxis=dict(title=None, showgrid=True, gridcolor="#f1f5f9", zeroline=False),
        legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=10, r=20, t=16, b=40),
        height=280, font=dict(family="Inter, sans-serif", size=12),
    )
    return fig


def chart_evolucion_retrasos(evo_df: pd.DataFrame) -> go.Figure:
    """Bar chart de retrasos mes a mes."""
    fig = go.Figure(go.Bar(
        x=evo_df["Mes"], y=evo_df["Con Retraso"],
        marker_color=COLORS["red"],
        marker_line_width=0,
        text=evo_df["Con Retraso"],
        textposition="outside",
        textfont=dict(size=12),
        cliponaxis=False,
        name="Con retraso",
    ))
    fig.update_layout(
        xaxis=dict(title=None, type="category", tickfont=dict(size=11), showgrid=False),
        yaxis=dict(title=None, showgrid=True, gridcolor="#f1f5f9", zeroline=False),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=10, r=20, t=16, b=10),
        height=260, bargap=0.4,
    )
    return fig


def chart_velocidad_historica(evo_df: pd.DataFrame) -> go.Figure:
    """Velocidad de entrega mensual (delta de completados)."""
    vel = evo_df["Completados"].diff().fillna(evo_df["Completados"])
    vel = vel.clip(lower=0).astype(int)
    colors_v = [COLORS["green"] if v > 0 else "#cbd5e1" for v in vel]
    fig = go.Figure(go.Bar(
        x=evo_df["Mes"], y=vel,
        marker_color=colors_v,
        marker_line_width=0,
        text=vel,
        textposition="outside",
        textfont=dict(size=12),
        cliponaxis=False,
    ))
    fig.update_layout(
        xaxis=dict(title=None, type="category", tickfont=dict(size=11), showgrid=False),
        yaxis=dict(title=None, showgrid=True, gridcolor="#f1f5f9", zeroline=False),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=10, r=20, t=16, b=10),
        height=260, bargap=0.4,
    )
    return fig


def chart_forecast(evo_df: pd.DataFrame, backlog_actual: int, vel_prom: float) -> go.Figure:
    """
    REQ 3: Gráfico de forecast — proyecta completados futuros hasta cerrar el backlog.
    """
    if vel_prom <= 0 or len(evo_df) == 0:
        fig = go.Figure()
        fig.add_annotation(text="Sin datos suficientes para forecast",
                           xref="paper", yref="paper", x=0.5, y=0.5,
                           showarrow=False, font=dict(size=13, color="#94a3b8"))
        fig.update_layout(height=280, paper_bgcolor="white", plot_bgcolor="white")
        return fig

    # Datos históricos
    hist_x = list(evo_df["Mes"])
    hist_y = list(evo_df["Completados"])
    ultimo_comp = hist_y[-1] if hist_y else 0
    total_reqs  = (evo_df["Total"].iloc[-1] if not evo_df.empty else backlog_actual + ultimo_comp)

    # Proyección futura
    meses_necesarios = int(np.ceil(backlog_actual / vel_prom)) if vel_prom > 0 else 0
    proj_x = [f"Mes +{i+1}" for i in range(min(meses_necesarios + 1, 18))]
    proj_y = [min(ultimo_comp + int(vel_prom * (i + 1)), total_reqs)
              for i in range(len(proj_x))]

    fig = go.Figure()
    # Histórico
    fig.add_trace(go.Scatter(
        x=hist_x, y=hist_y,
        mode="lines+markers",
        name="Completados (real)",
        line=dict(color=COLORS["green"], width=2.5),
        marker=dict(size=8, color=COLORS["green"]),
    ))
    # Línea meta total
    fig.add_hline(y=total_reqs, line_dash="dot", line_color="#94a3b8",
                  annotation_text=f"Total: {total_reqs}",
                  annotation_font=dict(size=10, color="#94a3b8"))
    # Forecast
    if proj_x:
        fig.add_trace(go.Scatter(
            x=[hist_x[-1]] + proj_x if hist_x else proj_x,
            y=[ultimo_comp] + proj_y if hist_x else proj_y,
            mode="lines+markers",
            name="Proyección",
            line=dict(color=COLORS["primary"], width=2, dash="dash"),
            marker=dict(size=7, symbol="diamond", color=COLORS["primary"]),
        ))
    fig.update_layout(
        xaxis=dict(title=None, type="category", tickfont=dict(size=10), tickangle=-30),
        yaxis=dict(title=None, showgrid=True, gridcolor="#f1f5f9", zeroline=False),
        legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center"),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=10, r=20, t=16, b=50),
        height=300, font=dict(family="Inter, sans-serif", size=12),
    )
    return fig


def render_evolucion_portafolio():
    """
    REQ 2 + REQ 3: Vista de Evolución del Portafolio + Forecast.
    Integra datos de todos los meses cargados en historial_reportes.
    """
    sd   = st.session_state.get("_sd", {})
    hist = sd.get("historial_reportes", {})

    # Header
    st.markdown(
        "<h2 style='color:#0f1c2e;font-weight:900;margin-bottom:2px;font-size:1.8rem;'>"
        "📈 Evolución del Portafolio</h2>"
        "<p style='color:#64748b;font-size:13px;'>Análisis histórico mes a mes + Forecast de cierre · TD 2026</p>",
        unsafe_allow_html=True,
    )

    if len(hist) == 0:
        st.info("👈 Carga al menos **dos meses** de datos en el panel lateral para ver la evolución del portafolio.")
        return

    evo_df = build_evolution_df()

    if evo_df.empty:
        st.warning("No se pudieron construir los datos de evolución.")
        return

    # ── KPIs globales de evolución ─────────────────────────────────────────
    _sec_header("📊", "Resumen de Evolución Mensual")

    # Tabla de avance por mes
    tabla_avance = evo_df[["Mes","Total","Completados","En Curso","No Iniciado","Con Retraso","% Completado"]].copy()
    tabla_avance["% Completado"] = tabla_avance["% Completado"].apply(lambda v: f"{v:.1f}%")

    c_tab, c_kpi = st.columns([2.5, 1])
    with c_tab:
        st.dataframe(
            tabla_avance,
            use_container_width=True,
            hide_index=True,
            height=min(60 + 48 * len(evo_df), 360),
            column_config={
                "Mes":           st.column_config.TextColumn("Mes"),
                "Total":         st.column_config.NumberColumn("Total"),
                "Completados":   st.column_config.NumberColumn("✅ Completados"),
                "En Curso":      st.column_config.NumberColumn("🔄 En Curso"),
                "No Iniciado":   st.column_config.NumberColumn("⏸ No Iniciado"),
                "Con Retraso":   st.column_config.NumberColumn("⚠ Retraso"),
                "% Completado":  st.column_config.TextColumn("% Completado"),
            },
        )

    with c_kpi:
        ultimo = evo_df.iloc[-1]
        primero = evo_df.iloc[0]
        delta_comp = ultimo["Completados"] - primero["Completados"]
        delta_retr = int(ultimo["Con Retraso"]) - int(primero["Con Retraso"])
        st.metric("📦 Total actual", int(ultimo["Total"]))
        st.metric("✅ Completados", int(ultimo["Completados"]), delta=f"+{delta_comp}" if delta_comp >= 0 else str(delta_comp))
        st.metric("⚠ Retrasos", int(ultimo["Con Retraso"]),
                  delta=str(delta_retr) if delta_retr != 0 else "0",
                  delta_color="inverse")

    # ── Gráficos de evolución ──────────────────────────────────────────────
    if len(evo_df) >= 2:
        _sec_header("📈", "Gráficos de Evolución")

        col_comp, col_back = st.columns(2)
        with col_comp:
            st.markdown("<p style='font-size:13px;font-weight:600;color:#334155;margin-bottom:4px;'>"
                        "Completados y En Curso por Mes</p>", unsafe_allow_html=True)
            st.plotly_chart(chart_evolucion_completados(evo_df),
                            use_container_width=True, key="evo_comp")

        with col_back:
            st.markdown("<p style='font-size:13px;font-weight:600;color:#334155;margin-bottom:4px;'>"
                        "Evolución del Backlog</p>", unsafe_allow_html=True)
            st.plotly_chart(chart_evolucion_backlog(evo_df),
                            use_container_width=True, key="evo_back")

        col_ret, col_vel = st.columns(2)
        with col_ret:
            st.markdown("<p style='font-size:13px;font-weight:600;color:#334155;margin-bottom:4px;'>"
                        "Retrasos por Mes</p>", unsafe_allow_html=True)
            st.plotly_chart(chart_evolucion_retrasos(evo_df),
                            use_container_width=True, key="evo_ret")

        with col_vel:
            st.markdown("<p style='font-size:13px;font-weight:600;color:#334155;margin-bottom:4px;'>"
                        "Velocidad de Entrega Mensual (delta)</p>", unsafe_allow_html=True)
            st.plotly_chart(chart_velocidad_historica(evo_df),
                            use_container_width=True, key="evo_vel")

    # ── REQ 3: Forecast ────────────────────────────────────────────────────
    _sec_header("🔮", "Forecast del Portafolio")

    # Calcular velocidad promedio (delta de completados por mes)
    if len(evo_df) >= 2:
        deltas    = evo_df["Completados"].diff().dropna().clip(lower=0)
        vel_prom  = float(deltas.mean())
    elif len(evo_df) == 1:
        vel_prom  = float(evo_df["Completados"].iloc[0])
    else:
        vel_prom  = 0.0

    backlog_actual   = int(evo_df["Backlog"].iloc[-1]) if not evo_df.empty else 0
    meses_estimados  = int(np.ceil(backlog_actual / vel_prom)) if vel_prom > 0 else None

    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    col_f1.metric("📦 Backlog actual", backlog_actual, "requerimientos pendientes")
    col_f2.metric("⚡ Velocidad promedio", f"{vel_prom:.1f}", "completados/mes")
    col_f3.metric("🗓 Meses estimados", meses_estimados if meses_estimados else "—",
                  "para cerrar el backlog")
    if meses_estimados:
        fecha_est = pd.Timestamp.today() + pd.DateOffset(months=meses_estimados)
        col_f4.metric("📅 Fecha estimada cierre", fecha_est.strftime("%b %Y"))
    else:
        col_f4.metric("📅 Fecha estimada cierre", "Sin datos")

    # Caja resumen del forecast
    if meses_estimados and vel_prom > 0:
        st.markdown(
            f"<div style='background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;"
            f"padding:14px 20px;margin:8px 0 16px;'>"
            f"<div style='font-size:13px;font-weight:700;color:#1d4ed8;margin-bottom:4px;'>"
            f"📋 Resumen del Forecast</div>"
            f"<div style='font-size:13px;color:#1e3a5f;'>"
            f"Backlog actual: <strong>{backlog_actual}</strong> requerimientos · "
            f"Velocidad promedio: <strong>{vel_prom:.1f}</strong> completados/mes · "
            f"Tiempo estimado: <strong>{meses_estimados} meses</strong>"
            f"</div></div>",
            unsafe_allow_html=True,
        )

        st.markdown("<p style='font-size:13px;font-weight:600;color:#334155;margin-bottom:4px;'>"
                    "Proyección de Completados hasta Cierre del Backlog</p>",
                    unsafe_allow_html=True)
        st.plotly_chart(chart_forecast(evo_df, backlog_actual, vel_prom),
                        use_container_width=True, key="evo_forecast")
    else:
        st.info("Carga más meses para generar un forecast preciso.")

    # ── Comparación entre meses seleccionados ─────────────────────────────
    if len(evo_df) >= 2:
        _sec_header("🔍", "Comparar Meses")
        meses_disp = list(evo_df["Clave"])
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            mes_a = st.selectbox("Mes base", options=meses_disp,
                                 format_func=_mes_label, index=0, key="w_comp_mes_a")
        with col_m2:
            idx_b = min(1, len(meses_disp) - 1)
            mes_b = st.selectbox("Mes a comparar", options=meses_disp,
                                 format_func=_mes_label, index=idx_b, key="w_comp_mes_b")

        if mes_a != mes_b:
            row_a = evo_df[evo_df["Clave"] == mes_a].iloc[0]
            row_b = evo_df[evo_df["Clave"] == mes_b].iloc[0]

            metrics = ["Total","Completados","En Curso","No Iniciado","Con Retraso","% Completado"]
            comp_data = []
            for m in metrics:
                va = row_a[m]
                vb = row_b[m]
                if isinstance(va, float):
                    delta = f"{vb - va:+.1f}"
                else:
                    delta = f"{int(vb) - int(va):+d}"
                comp_data.append({"Indicador": m,
                                  _mes_label(mes_a): va,
                                  _mes_label(mes_b): vb,
                                  "Delta": delta})
            st.dataframe(pd.DataFrame(comp_data), use_container_width=True, hide_index=True)

    st.caption("Vista Evolución del Portafolio · TD 2026 · Datos de Microsoft Planner")


# ─────────────────────────────────────────────────────────────────────────────

# ── Paleta corporativa para PDF ───────────────────────────────────────────────
_PDF_BLUE      = rl_colors.HexColor("#1d6af5")
_PDF_CYAN      = rl_colors.HexColor("#0891b2")
_PDF_DARK      = rl_colors.HexColor("#0f1c2e")
_PDF_SLATE     = rl_colors.HexColor("#334155")
_PDF_GRAY      = rl_colors.HexColor("#64748b")
_PDF_LIGHTGRAY = rl_colors.HexColor("#f4f6fb")
_PDF_BORDER    = rl_colors.HexColor("#e2e8f0")
_PDF_GREEN     = rl_colors.HexColor("#16a34a")
_PDF_YELLOW    = rl_colors.HexColor("#d97706")
_PDF_RED       = rl_colors.HexColor("#dc2626")
_PDF_WHITE     = rl_colors.white

_PDF_STYLES = None  # lazy init


def _get_pdf_styles():
    global _PDF_STYLES
    if _PDF_STYLES:
        return _PDF_STYLES
    base = getSampleStyleSheet()
    s = {}

    s["title"] = ParagraphStyle(
        "pdf_title", fontSize=22, fontName="Helvetica-Bold",
        textColor=_PDF_DARK, spaceAfter=4, leading=26,
    )
    s["subtitle"] = ParagraphStyle(
        "pdf_subtitle", fontSize=10, fontName="Helvetica",
        textColor=_PDF_GRAY, spaceAfter=14, leading=14,
    )
    s["section"] = ParagraphStyle(
        "pdf_section", fontSize=9, fontName="Helvetica-Bold",
        textColor=_PDF_GRAY, spaceBefore=16, spaceAfter=6,
        leading=12, textTransform="uppercase", letterSpacing=0.8,
    )
    s["body"] = ParagraphStyle(
        "pdf_body", fontSize=9, fontName="Helvetica",
        textColor=_PDF_SLATE, leading=13, spaceAfter=6,
    )
    s["bold"] = ParagraphStyle(
        "pdf_bold", fontSize=9, fontName="Helvetica-Bold",
        textColor=_PDF_DARK, leading=13,
    )
    s["small"] = ParagraphStyle(
        "pdf_small", fontSize=7.5, fontName="Helvetica",
        textColor=_PDF_GRAY, leading=10,
    )
    s["kpi_val"] = ParagraphStyle(
        "pdf_kpi_val", fontSize=20, fontName="Helvetica-Bold",
        textColor=_PDF_BLUE, leading=24, alignment=TA_CENTER,
    )
    s["kpi_lbl"] = ParagraphStyle(
        "pdf_kpi_lbl", fontSize=7, fontName="Helvetica-Bold",
        textColor=_PDF_GRAY, leading=9, alignment=TA_CENTER,
        textTransform="uppercase",
    )
    s["header_cell"] = ParagraphStyle(
        "pdf_hcell", fontSize=7.5, fontName="Helvetica-Bold",
        textColor=_PDF_WHITE, leading=10,
    )
    s["body_cell"] = ParagraphStyle(
        "pdf_bcell", fontSize=7.5, fontName="Helvetica",
        textColor=_PDF_SLATE, leading=10,
    )
    _PDF_STYLES = s
    return s


def _semaforo_pdf(pct: float):
    """Retorna (color reportlab, texto) del semáforo."""
    if pct > 80:   return _PDF_GREEN,  "En meta"
    if pct >= 50:  return _PDF_YELLOW, "Seguimiento"
    return _PDF_RED, "En riesgo"


def _divider():
    return HRFlowable(width="100%", thickness=0.5, color=_PDF_BORDER,
                      spaceAfter=10, spaceBefore=4)


def _section_title(text: str, icon: str = ""):
    s = _get_pdf_styles()
    label = f"{icon}  {text}" if icon else text
    return Paragraph(label.upper(), s["section"])


def _kpi_row_table(items: list) -> Table:
    """Fila de tarjetas KPI — items: [(label, value, sub, color), ...]"""
    s = _get_pdf_styles()
    ncols = len(items)
    cell_w = (A4[0] - 3.4*cm) / ncols

    rows = []
    for label, value, sub, color in items:
        cell = [
            Paragraph(label, s["kpi_lbl"]),
            Spacer(1, 3),
            Paragraph(str(value), ParagraphStyle(
                "kv", fontSize=18, fontName="Helvetica-Bold",
                textColor=color, leading=22, alignment=TA_CENTER)),
            Spacer(1, 2),
            Paragraph(sub, s["small"]) if sub else Spacer(1, 1),
        ]
        rows.append(cell)

    tdata   = [rows]
    col_ws  = [cell_w] * ncols
    tbl = Table(tdata, colWidths=col_ws, rowHeights=None)
    tbl.setStyle(TableStyle([
        ("ALIGN",       (0,0), (-1,-1), "CENTER"),
        ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
        ("BOX",         (0,0), (0,0),  0.5, _PDF_BORDER),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [_PDF_WHITE]),
        ("LEFTPADDING",  (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING",   (0,0), (-1,-1), 10),
        ("BOTTOMPADDING",(0,0), (-1,-1), 10),
        *[("BOX", (i,0), (i,0), 0.5, _PDF_BORDER) for i in range(ncols)],
        *[("TOPPADDING", (i,0), (i,0), 10) for i in range(ncols)],
        *[("BACKGROUND", (i,0), (i,0), _PDF_LIGHTGRAY) for i in range(ncols)],
    ]))
    return tbl


def _obj_kpi_table(skpis: dict, objs_order: list) -> Table:
    """Tabla con los 5 objetivos estratégicos + semáforo."""
    s    = _get_pdf_styles()
    hdrs = ["Objetivo Estratégico", "Meta", "Avance", "Cumpl. %", "Estado"]
    header_row = [Paragraph(h, s["header_cell"]) for h in hdrs]

    data = [header_row]
    row_styles = []
    for i, obj in enumerate(objs_order):
        d       = skpis[obj]
        pct     = d["pct"]
        color, estado = _semaforo_pdf(pct)
        icon    = "● "
        row = [
            Paragraph(obj, s["body_cell"]),
            Paragraph(str(d["meta"]), s["body_cell"]),
            Paragraph(str(d["avance"]), s["body_cell"]),
            Paragraph(f"{pct:.1f}%", ParagraphStyle(
                "pct_c", fontSize=8, fontName="Helvetica-Bold",
                textColor=color, leading=10)),
            Paragraph(f"{icon}{estado}", ParagraphStyle(
                "est_c", fontSize=7.5, fontName="Helvetica",
                textColor=color, leading=10)),
        ]
        data.append(row)
        bg = _PDF_LIGHTGRAY if i % 2 == 0 else _PDF_WHITE
        row_styles.append(("BACKGROUND", (0, i+1), (-1, i+1), bg))

    col_ws = [7.2*cm, 2.5*cm, 2.5*cm, 2.4*cm, 3*cm]
    tbl = Table(data, colWidths=col_ws)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0), _PDF_BLUE),
        ("TEXTCOLOR",    (0,0), (-1,0), _PDF_WHITE),
        ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,0), 8),
        ("ALIGN",        (1,0), (-1,-1), "CENTER"),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("GRID",         (0,0), (-1,-1), 0.4, _PDF_BORDER),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [_PDF_LIGHTGRAY, _PDF_WHITE]),
        ("TOPPADDING",   (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",(0,0), (-1,-1), 6),
        ("LEFTPADDING",  (0,0), (-1,-1), 8),
    ] + row_styles))
    return tbl


def _df_to_table(df: pd.DataFrame, max_rows: int = 20,
                 col_widths: list = None) -> Table:
    """Convierte un DataFrame a tabla ReportLab con estilo corporativo."""
    s = _get_pdf_styles()
    df = df.head(max_rows).fillna("—")

    # Cabecera
    header = [Paragraph(str(c), s["header_cell"]) for c in df.columns]
    rows   = [header]
    for _, row in df.iterrows():
        rows.append([Paragraph(str(v), s["body_cell"]) for v in row])

    page_w = A4[0] - 3.4*cm
    if col_widths is None:
        n = len(df.columns)
        col_widths = [page_w / n] * n

    tbl = Table(rows, colWidths=col_widths)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), _PDF_DARK),
        ("TEXTCOLOR",     (0,0), (-1,0), _PDF_WHITE),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("GRID",          (0,0), (-1,-1), 0.4, _PDF_BORDER),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [_PDF_LIGHTGRAY, _PDF_WHITE]),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("FONTSIZE",      (0,0), (-1,-1), 7.5),
    ]))
    return tbl


def _global_kpi_block(global_pct: float) -> Table:
    """Bloque grande de cumplimiento global."""
    s = _get_pdf_styles()
    color, estado = _semaforo_pdf(global_pct)
    cell = [
        Paragraph("Cumplimiento Estratégico Global", ParagraphStyle(
            "gk_lbl", fontSize=8, fontName="Helvetica-Bold",
            textColor=_PDF_WHITE, leading=11, alignment=TA_CENTER,
            textTransform="uppercase",
        )),
        Spacer(1, 6),
        Paragraph(f"{global_pct:.1f}%", ParagraphStyle(
            "gk_val", fontSize=32, fontName="Helvetica-Bold",
            textColor=_PDF_WHITE, leading=38, alignment=TA_CENTER,
        )),
        Spacer(1, 4),
        Paragraph(estado, ParagraphStyle(
            "gk_est", fontSize=9, fontName="Helvetica",
            textColor=_PDF_WHITE, leading=12, alignment=TA_CENTER,
        )),
        Spacer(1, 2),
        Paragraph("5 Objetivos · TD 2026", ParagraphStyle(
            "gk_sub", fontSize=7, fontName="Helvetica",
            textColor=rl_colors.HexColor("#c7d9f8"), leading=9, alignment=TA_CENTER,
        )),
    ]
    tbl = Table([[cell]], colWidths=[A4[0] - 3.4*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,0), _PDF_BLUE),
        ("ROUNDEDCORNERS", [8]),
        ("TOPPADDING",    (0,0), (0,0), 16),
        ("BOTTOMPADDING", (0,0), (0,0), 16),
        ("LEFTPADDING",   (0,0), (0,0), 20),
        ("RIGHTPADDING",  (0,0), (0,0), 20),
        ("ALIGN",         (0,0), (0,0), "CENTER"),
    ]))
    return tbl


def _page_header(canvas_obj, doc):
    """Encabezado corporativo en cada página."""
    w, h = A4
    # Banda superior
    canvas_obj.saveState()
    canvas_obj.setFillColor(_PDF_DARK)
    canvas_obj.rect(0, h - 1.6*cm, w, 1.6*cm, fill=True, stroke=False)
    # Logo / marca
    canvas_obj.setFillColor(_PDF_WHITE)
    canvas_obj.setFont("Helvetica-Bold", 11)
    canvas_obj.drawString(1.7*cm, h - 1.1*cm, "⚡  TD 2026 Analytics")
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.setFillColor(rl_colors.HexColor("#94a3b8"))
    canvas_obj.drawRightString(w - 1.7*cm, h - 1.1*cm,
                               f"Transformación Digital  ·  {datetime.today().strftime('%d/%m/%Y')}")
    # Pie de página
    canvas_obj.setFillColor(_PDF_GRAY)
    canvas_obj.setFont("Helvetica", 7.5)
    canvas_obj.drawString(1.7*cm, 0.9*cm,
                          "Informe confidencial · Vicepresidencia Transformación Digital")
    canvas_obj.drawRightString(w - 1.7*cm, 0.9*cm, f"Página {doc.page}")
    canvas_obj.restoreState()


def generate_pdf_report(skpis: dict, sd: dict, df: pd.DataFrame) -> bytes:
    """
    Genera el PDF completo "Informe TD 2026" con:
    - Portada con cumplimiento global
    - Resumen de indicadores estratégicos
    - Tabla de objetivos con semáforos
    - Tabla de hitos
    - Tabla de entregables
    - Indicadores de portafolio (si hay Excel)
    Retorna bytes para descarga con st.download_button.

    REQ 5 FIX: Manejo defensivo de sd (puede faltar hitos/entregables).
    """
    # ── Defensivo: validar skpis ─────────────────────────────────────────────
    if not skpis or "_global" not in skpis:
        skpis = calculate_strategic_kpis()

    # ── Defensivo: sd puede no tener hitos/entregables ───────────────────────
    _empty_hitos = pd.DataFrame({
        "Objetivo Estratégico": [], "Hito": [], "Fecha": [],
        "Responsable": [], "Estado (%)": [], "Comentario": [],
    })
    _empty_entregables = pd.DataFrame({
        "Objetivo": [], "Entregable": [], "Responsable": [],
        "Fecha Límite": [], "Prioridad": [], "Estado": [], "% Avance": [],
    })
    buf = io.BytesIO()
    s   = _get_pdf_styles()
    fecha_str = datetime.today().strftime("%d/%m/%Y")
    fecha_file = datetime.today().strftime("%Y%m%d")

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=1.7*cm, rightMargin=1.7*cm,
        topMargin=2.2*cm,  bottomMargin=1.8*cm,
        title=f"Informe TD 2026 - {fecha_str}",
        author="Vicepresidencia Transformación Digital",
    )

    story = []
    objs_order = [
        "Eficiencia Operativa", "Datos Confiables", "Excelencia ERP",
        "Integración", "Seguridad de la Información",
    ]

    # ══════════════════════════════════════════════════════════════════════
    # PÁGINA 1 — PORTADA
    # ══════════════════════════════════════════════════════════════════════
    story.append(Spacer(1, 1.5*cm))
    story.append(Paragraph("INFORME EJECUTIVO", ParagraphStyle(
        "port_tag", fontSize=10, fontName="Helvetica-Bold",
        textColor=_PDF_BLUE, leading=14, textTransform="uppercase",
        letterSpacing=2,
    )))
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("Transformación Digital 2026", ParagraphStyle(
        "port_title", fontSize=28, fontName="Helvetica-Bold",
        textColor=_PDF_DARK, leading=34,
    )))
    story.append(Paragraph("Indicadores Estratégicos & Control Operativo", ParagraphStyle(
        "port_sub", fontSize=13, fontName="Helvetica",
        textColor=_PDF_SLATE, leading=18, spaceAfter=20,
    )))
    story.append(_divider())
    story.append(Spacer(1, 0.3*cm))

    # Bloque de cumplimiento global destacado
    story.append(_global_kpi_block(skpis["_global"]))
    story.append(Spacer(1, 0.6*cm))

    # KPIs de los 5 objetivos en 2 filas
    story.append(_section_title("Cumplimiento por Objetivo", "◉"))
    story.append(Spacer(1, 0.2*cm))
    story.append(_obj_kpi_table(skpis, objs_order))
    story.append(Spacer(1, 0.4*cm))

    # Meta info de portada
    meta_data = [
        ["Fecha de generación:", fecha_str,
         "Responsable:", "Vicepresidencia TD"],
        ["Periodo:", "Trimestre Actual 2026",
         "Versión:", "1.0"],
    ]
    meta_tbl = Table(meta_data, colWidths=[4*cm, 5.5*cm, 3.5*cm, 4*cm])
    meta_tbl.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE", (0,0), (-1,-1), 8),
        ("TEXTCOLOR", (0,0), (0,-1), _PDF_GRAY),
        ("TEXTCOLOR", (2,0), (2,-1), _PDF_GRAY),
        ("TEXTCOLOR", (1,0), (1,-1), _PDF_DARK),
        ("TEXTCOLOR", (3,0), (3,-1), _PDF_DARK),
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME", (2,0), (2,-1), "Helvetica-Bold"),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(meta_tbl)

    # ══════════════════════════════════════════════════════════════════════
    # PÁGINA 2 — INDICADORES ESTRATÉGICOS DETALLE
    # ══════════════════════════════════════════════════════════════════════
    story.append(PageBreak())

    story.append(Paragraph("Indicadores Estratégicos", s["title"]))
    story.append(Paragraph(
        f"Detalle de metas, avances y estado por objetivo estratégico · {fecha_str}",
        s["subtitle"]))
    story.append(_divider())

    # Tabla detallada por objetivo
    story.append(_section_title("Resumen de Objetivos Estratégicos", "▪"))
    story.append(Spacer(1, 0.2*cm))

    hdrs_det = ["Objetivo", "Meta", "Completados", "% Cumpl.", "Estado", "Unidad"]
    hrow_det = [Paragraph(h, s["header_cell"]) for h in hdrs_det]
    det_rows = [hrow_det]
    for obj in objs_order:
        d = skpis[obj]
        color, estado = _semaforo_pdf(d["pct"])
        det_rows.append([
            Paragraph(obj, s["body_cell"]),
            Paragraph(str(d["meta"]), s["body_cell"]),
            Paragraph(str(d["avance"]), s["body_cell"]),
            Paragraph(f"{d['pct']:.1f}%", ParagraphStyle(
                "dp", fontSize=8, fontName="Helvetica-Bold", textColor=color, leading=10)),
            Paragraph(estado, ParagraphStyle(
                "de", fontSize=7.5, fontName="Helvetica", textColor=color, leading=10)),
            Paragraph(str(d.get("unit", "")), s["body_cell"]),
        ])

    det_tbl = Table(det_rows, colWidths=[6.5*cm, 2*cm, 2.5*cm, 2.5*cm, 3*cm, 2.5*cm])
    det_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), _PDF_DARK),
        ("TEXTCOLOR",     (0,0), (-1,0), _PDF_WHITE),
        ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
        ("ALIGN",         (1,0), (-1,-1), "CENTER"),
        ("GRID",          (0,0), (-1,-1), 0.4, _PDF_BORDER),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [_PDF_LIGHTGRAY, _PDF_WHITE]),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(det_tbl)
    story.append(Spacer(1, 0.5*cm))

    # Hitos estratégicos (defensivo)
    hitos_df = sd.get("hitos_tabla", _empty_hitos)
    if hitos_df is None or not isinstance(hitos_df, pd.DataFrame):
        hitos_df = _empty_hitos
    if len(hitos_df) > 0:
        story.append(_section_title("Hitos Estratégicos", "▪"))
        story.append(Spacer(1, 0.2*cm))
        _hcols = ["Objetivo Estratégico","Hito","Fecha","Responsable","Estado (%)","Comentario"]
        _hcols_ok = [c for c in _hcols if c in hitos_df.columns]
        hitos_show = hitos_df[_hcols_ok].copy()
        if "Estado (%)" in hitos_show.columns:
            hitos_show["Estado (%)"] = hitos_show["Estado (%)"].astype(str) + "%"
        if "Fecha" in hitos_show.columns:
            hitos_show["Fecha"] = hitos_show["Fecha"].astype(str)
        story.append(_df_to_table(
            hitos_show.rename(columns={"Objetivo Estratégico":"Objetivo","Estado (%)":"Estado %"}),
            col_widths=[3.8*cm, 4.5*cm, 2.2*cm, 3*cm, 1.8*cm, 3.7*cm],
        ))
        story.append(Spacer(1, 0.5*cm))

    # Entregables (defensivo)
    entregables_df = sd.get("entregables_tabla", _empty_entregables)
    if entregables_df is None or not isinstance(entregables_df, pd.DataFrame):
        entregables_df = _empty_entregables
    if len(entregables_df) > 0:
        story.append(_section_title("Entregables por Objetivo", "▪"))
        story.append(Spacer(1, 0.2*cm))
        ent_show = entregables_df.copy()
        if "Fecha Límite" in ent_show.columns:
            ent_show["Fecha Límite"] = ent_show["Fecha Límite"].astype(str)
        if "% Avance" in ent_show.columns:
            ent_show["% Avance"] = ent_show["% Avance"].astype(str) + "%"
        cols_ent = ["Objetivo","Entregable","Responsable","Fecha Límite","Prioridad","Estado","% Avance"]
        cols_ent = [c for c in cols_ent if c in ent_show.columns]
        story.append(_df_to_table(
            ent_show[cols_ent],
            col_widths=[3*cm, 5.5*cm, 3*cm, 2.4*cm, 2*cm, 2.3*cm, 1.8*cm],
        ))

    # ══════════════════════════════════════════════════════════════════════
    # PÁGINA 3 — CONTROL OPERATIVO (si hay Excel)
    # ══════════════════════════════════════════════════════════════════════
    if not df.empty:
        story.append(PageBreak())

        story.append(Paragraph("Control Operativo", s["title"]))
        story.append(Paragraph(
            f"Indicadores de portafolio desde Microsoft Planner · {fecha_str}",
            s["subtitle"]))
        story.append(_divider())

        total   = len(df)
        comp    = (df["progreso"] == "Completado").sum() if "progreso" in df.columns else 0
        retras  = df["retraso"].sum() if "retraso" in df.columns else 0
        sin_a   = (df.get("asignado_raw", pd.Series([""] * total)) == "Sin asignar").sum()
        pct_comp = round(comp / max(total, 1) * 100, 1)

        story.append(_section_title("KPIs Operativos del Portafolio", "▪"))
        story.append(Spacer(1, 0.2*cm))
        story.append(_kpi_row_table([
            ("Total Reqs.", total, "", _PDF_BLUE),
            ("Completados", f"{comp}", f"{pct_comp}% del total", _PDF_GREEN),
            ("Retrasados", retras, "Requieren atención", _PDF_RED),
            ("Sin asignar", sin_a, "Requieren asignación", _PDF_YELLOW),
            ("Categorías", df["categoria"].nunique() if "categoria" in df.columns else "—", "OKR", _PDF_CYAN),
        ]))
        story.append(Spacer(1, 0.5*cm))

        # Top 10 por especialista
        if "asignado_raw" in df.columns and "progreso" in df.columns:
            story.append(_section_title("Distribución por Especialista (Top 10)", "▪"))
            story.append(Spacer(1, 0.2*cm))
            esp_df = (
                df.groupby("asignado_raw")
                .agg(Total=("nombre","count"),
                     Completados=("progreso", lambda x: (x=="Completado").sum()))
                .assign(**{"% Cumpl.": lambda d: (d["Completados"]/d["Total"]*100).round(1).astype(str)+"%"})
                .sort_values("Total", ascending=False)
                .head(10)
                .reset_index()
                .rename(columns={"asignado_raw": "Especialista"})
            )
            story.append(_df_to_table(esp_df,
                col_widths=[6*cm, 3*cm, 3.5*cm, 3.5*cm]))
            story.append(Spacer(1, 0.5*cm))

        # Por categoría estratégica
        if "categoria" in df.columns:
            story.append(_section_title("Reqs. por Categoría Estratégica", "▪"))
            story.append(Spacer(1, 0.2*cm))
            cat_df = (df.groupby("categoria").size()
                      .reset_index(name="Cantidad")
                      .sort_values("Cantidad", ascending=False))
            story.append(_df_to_table(cat_df, col_widths=[10*cm, 4*cm]))

    # ══════════════════════════════════════════════════════════════════════
    # Build
    # ══════════════════════════════════════════════════════════════════════
    doc.build(story, onFirstPage=_page_header, onLaterPages=_page_header)
    buf.seek(0)
    return buf.read()


# ─────────────────────────────────────────────────────────────────────────────
# 17B. BOTÓN DE DESCARGA PDF (componente reutilizable)
# ─────────────────────────────────────────────────────────────────────────────
def render_pdf_download_button(skpis: dict, df: pd.DataFrame, key_suffix: str = ""):
    """
    REQ 5 FIX: Renderiza el botón de generación y descarga del PDF.
    - Siempre usa st.session_state["_sd"] (nunca falla si _sd existe)
    - No depende de ningún widget visible en la vista actual
    - Usa key_suffix para evitar duplicate-key errors entre vistas
    - El PDF se genera una vez y se guarda en session_state
    """
    if "_sd" not in st.session_state:
        init_session_state()
    sd = st.session_state["_sd"]
    fecha_file = datetime.today().strftime("%Y%m%d")

    # Recalcular skpis por si acaso se pasó un dict vacío
    if not skpis or "_global" not in skpis:
        skpis = calculate_strategic_kpis()

    # Usar df en su forma completa (sin filtros de sidebar)
    # Si df viene vacío pero hay historial, usar el mes activo
    if df.empty:
        hist = sd.get("historial_reportes", {})
        mes_activo = sd.get("mes_activo")
        if hist and mes_activo and mes_activo in hist:
            df = hist[mes_activo]

    col_btn, col_hint = st.columns([2, 5])
    pdf_key   = f"_pdf_bytes_{key_suffix}"
    ready_key = f"_pdf_ready_{key_suffix}"

    with col_btn:
        if st.button("📄 Generar Informe PDF", key=f"btn_pdf_{key_suffix}",
                     type="primary", use_container_width=True):
            with st.spinner("⚙ Generando Informe TD 2026..."):
                try:
                    pdf_bytes = generate_pdf_report(skpis, sd, df)
                    st.session_state[pdf_key]   = pdf_bytes
                    st.session_state[ready_key] = True
                except Exception as e:
                    st.error(f"❌ Error generando PDF: {e}")
                    import traceback
                    st.code(traceback.format_exc(), language="text")
                    st.session_state[ready_key] = False

    if st.session_state.get(ready_key):
        with col_btn:
            st.download_button(
                label="⬇ Descargar PDF",
                data=st.session_state[pdf_key],
                file_name=f"Informe_TD_2026_{fecha_file}.pdf",
                mime="application/pdf",
                key=f"dl_pdf_{key_suffix}",
                use_container_width=True,
            )
        with col_hint:
            st.success(
                f"✅ **Informe TD 2026** listo · "
                f"{datetime.today().strftime('%d/%m/%Y %H:%M')}  ·  "
                "Incluye indicadores estratégicos y control operativo",
                icon="📋",
            )

# ─────────────────────────────────────────────────────────────────────────────
# 18. SELECTOR DE VISTA (FIJO EN TOP — FUERA DEL SIDEBAR)
# ─────────────────────────────────────────────────────────────────────────────
def render_view_selector() -> str:
    """
    Selector horizontal fijo en la parte superior.
    Persiste en _sd["nav_vista"] → no desaparece al ocultar sidebar.

    REQ 6: Botón toggle de sidebar siempre visible aquí.
    """
    sd = st.session_state["_sd"]

    col_brand, col_nav, col_toggle, col_date = st.columns([1.8, 3.5, 0.7, 1.8])
    with col_brand:
        st.markdown(
            "<div style='padding:8px 0 0;font-size:17px;font-weight:900;color:#0f1c2e;'>"
            "⚡ TD 2026 Analytics</div>",
            unsafe_allow_html=True,
        )
    with col_nav:
        # Determinar índice actual
        _nav_opts = [
            "🟢  Control Operativo",
            "🔵  Indicadores Estratégicos",
            "📈  Evolución del Portafolio",
        ]
        _cur = sd.get("nav_vista", _nav_opts[0])
        _cur_idx = _nav_opts.index(_cur) if _cur in _nav_opts else 0
        selected = st.radio(
            "Vista",
            options=_nav_opts,
            index=_cur_idx,
            horizontal=True,
            label_visibility="collapsed",
            key="w_nav",
        )
        sd["nav_vista"] = selected

    with col_toggle:
        # REQ 6: Botón toggle siempre visible en top bar
        sidebar_vis = sd.get("sidebar_visible", True)
        icon = "◀ Ocultar" if sidebar_vis else "▶ Mostrar"
        if st.button(icon, key="btn_sidebar_toggle", help="Mostrar/ocultar panel lateral"):
            sd["sidebar_visible"] = not sidebar_vis
            st.rerun()

    with col_date:
        st.markdown(
            f"<div style='text-align:right;padding-top:10px;font-size:11px;color:#8fa0b8;'>"
            f"Transformación Digital · {datetime.today().strftime('%d/%m/%Y')}</div>",
            unsafe_allow_html=True,
        )

    st.markdown(
        "<hr style='margin:4px 0 1.2rem 0;border:none;border-top:1px solid #e2e8f0;'>",
        unsafe_allow_html=True,
    )
    return sd["nav_vista"]


# ─────────────────────────────────────────────────────────────────────────────
# 19. PUNTO DE ENTRADA
# ─────────────────────────────────────────────────────────────────────────────
def main():
    inject_css()

    # 1. Inicializar _sd (solo si no existe — NUNCA sobrescribe)
    init_session_state()

    sd = st.session_state["_sd"]

    # 2. Selector de vistas fijo en top (lee/escribe _sd)
    vista = render_view_selector()

    # ── REQ 6: Sidebar toggle — renderiza solo si visible ─────────────────
    sidebar_visible = sd.get("sidebar_visible", True)

    MES_NOMBRES = {
        "01": "Enero",   "02": "Febrero",  "03": "Marzo",    "04": "Abril",
        "05": "Mayo",    "06": "Junio",    "07": "Julio",    "08": "Agosto",
        "09": "Septiembre","10": "Octubre","11": "Noviembre","12": "Diciembre",
    }

    if sidebar_visible:
        with st.sidebar:
            # ── REQ 1: Carga de histórico mensual ──────────────────────────
            st.markdown(
                "<div style='font-size:14px;font-weight:700;color:#0f1c2e;"
                "padding:8px 0 4px;'>📂 Fuente de datos</div>",
                unsafe_allow_html=True,
            )

            # Subir nuevo archivo con mes asociado
            with st.expander("➕ Agregar reporte mensual", expanded=len(sd["historial_reportes"]) == 0):
                col_yr, col_mn = st.columns(2)
                with col_yr:
                    año_sel = st.number_input("Año", min_value=2020, max_value=2030,
                                              value=2026, step=1, key="w_año_upload")
                with col_mn:
                    mes_num = st.selectbox(
                        "Mes", options=list(MES_NOMBRES.keys()),
                        format_func=lambda m: MES_NOMBRES[m],
                        key="w_mes_upload",
                    )
                mes_key = f"{año_sel}-{mes_num}"
                uploaded = st.file_uploader(
                    f"Excel — {MES_NOMBRES[mes_num]} {año_sel}",
                    type=["xlsx", "xls"], key="w_file_uploader",
                    help="Exporta desde Microsoft Planner → Exportar a Excel",
                )
                if uploaded is not None:
                    if st.button(f"💾 Guardar {MES_NOMBRES[mes_num]} {año_sel}",
                                 key="btn_guardar_mes", use_container_width=True):
                        with st.spinner("⚙ Procesando..."):
                            raw = load_data(uploaded)
                            if not raw.empty:
                                df_mes, meta_mes = preprocess_data(raw)
                                sd["historial_reportes"][mes_key] = df_mes
                                sd["historial_meta"][mes_key] = meta_mes
                                sd["mes_activo"] = mes_key
                                st.success(f"✅ {MES_NOMBRES[mes_num]} {año_sel} guardado")
                                st.rerun()
                            else:
                                st.error("El archivo está vacío o no pudo leerse.")

            # ── Selector de mes activo ──────────────────────────────────────
            hist = sd["historial_reportes"]
            if hist:
                st.markdown(
                    "<div style='font-size:12px;font-weight:700;color:#0f1c2e;"
                    "margin:8px 0 4px;'>📅 Mes activo</div>",
                    unsafe_allow_html=True,
                )
                meses_disp = sorted(hist.keys())
                meses_labels = {
                    k: f"{MES_NOMBRES.get(k[5:7], k[5:7])} {k[:4]}"
                    for k in meses_disp
                }
                mes_idx = meses_disp.index(sd["mes_activo"]) if sd["mes_activo"] in meses_disp else 0
                mes_sel = st.selectbox(
                    "Mes activo",
                    options=meses_disp,
                    index=mes_idx,
                    format_func=lambda k: meses_labels[k],
                    key="w_mes_activo",
                    label_visibility="collapsed",
                )
                sd["mes_activo"] = mes_sel

                # Eliminar mes
                if len(hist) > 0:
                    mes_del = st.selectbox(
                        "Eliminar mes", options=["— no eliminar —"] + meses_disp,
                        key="w_mes_del",
                    )
                    if mes_del != "— no eliminar —":
                        if st.button(f"🗑 Eliminar {meses_labels.get(mes_del, mes_del)}",
                                     key="btn_del_mes", use_container_width=True):
                            del sd["historial_reportes"][mes_del]
                            if mes_del in sd["historial_meta"]:
                                del sd["historial_meta"][mes_del]
                            if sd["mes_activo"] == mes_del:
                                remaining = [k for k in sd["historial_reportes"]]
                                sd["mes_activo"] = remaining[0] if remaining else None
                            st.rerun()

                # Resumen de meses cargados
                st.markdown("---")
                st.markdown(
                    f"<div style='font-size:11px;color:#64748b;'>"
                    f"📁 <b>{len(hist)}</b> mes(es) cargado(s)</div>",
                    unsafe_allow_html=True,
                )
                for k in sorted(hist.keys()):
                    n = len(hist[k])
                    lbl = meses_labels[k]
                    active_marker = " ◀" if k == sd["mes_activo"] else ""
                    st.caption(f"• {lbl}: {n} reqs{active_marker}")
            else:
                st.caption("Sin archivo — sube el primero arriba.")

            st.markdown("---")
            st.caption(f"v6.0 · {datetime.today().strftime('%d/%m/%Y')}")

    # 4. Obtener df activo desde historial
    hist = sd["historial_reportes"]
    mes_activo = sd.get("mes_activo")

    if hist and mes_activo and mes_activo in hist:
        df = hist[mes_activo]
        meta_d = sd["historial_meta"].get(mes_activo, {})
        if meta_d.get("missing_cols"):
            with st.expander(f"⚠ {len(meta_d['missing_cols'])} columnas no encontradas"):
                st.warning("Columnas no encontradas:\n" + ", ".join(meta_d["missing_cols"]))
    else:
        df, meta_d = pd.DataFrame(), {}

    # 5. Enrutar vista
    if "Estratégicos" in vista:
        create_executive_view(df)
    elif "Evolución" in vista:
        render_evolucion_portafolio()
    else:
        _render_operational_view(df, meta_d, bool(hist))


def _render_operational_view(df: pd.DataFrame, meta_d: dict, has_data: bool):
    """Vista Operativa."""
    if not has_data:
        st.markdown("""
        <div style='text-align:center;padding:60px 20px 40px;'>
          <div style='font-size:72px;margin-bottom:16px;'>⚡</div>
          <h1 style='font-size:2.2rem;font-weight:800;color:#0f1c2e;margin-bottom:8px;'>
            Dashboard Gestión de Requerimientos</h1>
          <p style='font-size:1.1rem;color:#64748b;margin-bottom:40px;'>
            Analítica ejecutiva para Microsoft Planner · Transformación Digital 2026</p>
        </div>
        """, unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.info("**📊 KPIs Ejecutivos**\n\nCompletitud, retrasos, lead time y velocidad de entrega.")
        with c2:
            st.info("**👥 Carga de Equipo**\n\nSemáforos de cumplimiento, vencidas abiertas y carga activa.")
        with c3:
            st.info("**🔄 Pipeline Estratégico**\n\nDistribución por categoría OKR, área y especialista.")
        st.markdown("""
        <div style='text-align:center;margin-top:40px;padding:24px;background:white;
                    border-radius:12px;border:1px solid #e2e8f0;'>
          <p style='color:#64748b;font-size:14px;margin-bottom:8px;'>
            👈 <strong>Sube tu archivo Excel</strong> exportado desde Microsoft Planner.</p>
          <p style='color:#94a3b8;font-size:12px;'>Formatos: .xlsx · .xls</p>
        </div>
        """, unsafe_allow_html=True)
    elif df.empty:
        st.error("El archivo está vacío o no pudo leerse correctamente.")
    else:
        create_dashboard(df, meta_d)


if __name__ == "__main__":
    main()
