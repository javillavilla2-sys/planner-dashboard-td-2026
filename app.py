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
import warnings

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

    # ── Botón de informe PDF ─────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:11px;font-weight:700;letter-spacing:1.2px;"
        "text-transform:uppercase;color:#8fa0b8;border-bottom:1px solid #e2e8f0;"
        "padding-bottom:6px;margin:1.4rem 0 .9rem;'>📄 Exportar Informe</div>",
        unsafe_allow_html=True,
    )
    _sd_ref = st.session_state.get("_sd", {})
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
def chart_radar_estrategico(kpis: dict) -> go.Figure:
    OBJS = ["Eficiencia Operativa", "Datos Confiables", "Excelencia ERP",
            "Integración", "Seguridad de la Información"]
    values  = [kpis[o]["pct"] for o in OBJS]
    values += [values[0]]
    cats    = OBJS + [OBJS[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[100]*len(cats), theta=cats, fill=None,
        line=dict(color="#e2e8f0", width=1, dash="dash"), name="Meta 100%",
    ))
    fig.add_trace(go.Scatterpolar(
        r=values, theta=cats, fill="toself",
        fillcolor="rgba(29,106,245,.12)",
        line=dict(color=COLORS["primary"], width=2.5),
        name="Cumplimiento actual",
        hovertemplate="%{theta}: <b>%{r:.1f}%</b><extra></extra>",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="white",
            radialaxis=dict(visible=True, range=[0, 100], ticksuffix="%",
                            tickfont=dict(size=10, color="#94a3b8"),
                            gridcolor="#f1f5f9"),
            angularaxis=dict(tickfont=dict(size=11, color="#334155")),
        ),
        showlegend=True,
        legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.1),
        margin=dict(t=20, b=60, l=40, r=40),
        height=380,
        paper_bgcolor="white",
    )
    return fig


def chart_barras_objetivos(kpis: dict) -> go.Figure:
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
    colors = [OBJ_COLORS_MAP[o] for o in OBJS]

    fig = go.Figure(go.Bar(
        x=vals, y=OBJS, orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"{v:.1f}%" for v in vals],
        textposition="outside",
        hovertemplate="%{y}: <b>%{x:.1f}%</b><extra></extra>",
    ))
    fig.add_vline(x=80, line_dash="dot", line_color="#94a3b8", line_width=1.5,
                  annotation_text="Meta 80%", annotation_position="top",
                  annotation_font=dict(size=10, color="#94a3b8"))
    fig.update_layout(
        xaxis=dict(range=[0, 115], showgrid=False, ticksuffix="%", tickfont=dict(size=10)),
        yaxis=dict(showgrid=False, tickfont=dict(size=11, color="#334155")),
        margin=dict(l=10, r=50, t=10, b=10),
        plot_bgcolor="white", paper_bgcolor="white",
        height=240,
        showlegend=False,
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


def _kpi_card_top(obj: str, pct: float, color: str, data: dict) -> str:
    """HTML de la parte superior de la tarjeta KPI."""
    bar_c = semaforo_color(pct)
    bar_w = min(int(pct), 100)
    if pct > 80:
        badge = f'<span style="background:#dcfce7;color:#15803d;font-size:10px;font-weight:700;padding:2px 8px;border-radius:20px;">🟢 En meta</span>'
    elif pct >= 50:
        badge = f'<span style="background:#fef9c3;color:#a16207;font-size:10px;font-weight:700;padding:2px 8px;border-radius:20px;">🟡 Seguimiento</span>'
    else:
        badge = f'<span style="background:#fee2e2;color:#b91c1c;font-size:10px;font-weight:700;padding:2px 8px;border-radius:20px;">🔴 En riesgo</span>'

    unit = data.get("unit", "")
    meta = data.get("meta", "—")
    avance = data.get("avance", 0)
    meta_txt = f"Meta: {meta} {unit}  ·  Actual: {avance} {unit}" if not data.get("unit") == "%" else f"Meta: {meta}%  ·  Actual: {avance}%"

    short_name = obj.replace("de la Información", "Info.").replace("Operativa", "Op.")

    return f"""
    <div style="background:white;border:1px solid #e2e8f0;border-top:3px solid {color};
                border-radius:12px 12px 0 0;padding:14px 14px 10px;min-height:130px;
                box-shadow:0 1px 4px rgba(0,0,0,.05);">
      <div style="font-size:9px;font-weight:800;text-transform:uppercase;letter-spacing:1.2px;
                  color:#94a3b8;margin-bottom:6px;line-height:1.3;">{short_name}</div>
      <div style="font-size:2.2rem;font-weight:900;line-height:1;color:{color};
                  margin-bottom:6px;">{pct:.1f}%</div>
      <div style="background:#f1f5f9;border-radius:4px;height:4px;margin:0 0 8px;">
        <div style="background:{bar_c};width:{bar_w}%;height:4px;border-radius:4px;"></div>
      </div>
      {badge}
      <div style="font-size:10px;color:#94a3b8;margin-top:6px;">{meta_txt}</div>
    </div>"""


def render_strategic_kpis(skpis: dict, objs_order: list, obj_colors: dict):
    """
    SECCIÓN 1 — 5 tarjetas KPI con edición inline + Global a la derecha.
    Todos los valores se guardan en _sd → persisten entre vistas.
    """
    _sec_header("📊", "Cumplimiento por Objetivo Estratégico")

    sd         = st.session_state["_sd"]
    global_pct = skpis["_global"]
    g_color    = semaforo_color(global_pct)
    g_icon     = "🟢 En meta" if global_pct > 80 else ("🟡 Seguimiento" if global_pct >= 50 else "🔴 En riesgo")
    g_badge_bg = "#dcfce7" if global_pct > 80 else ("#fef9c3" if global_pct >= 50 else "#fee2e2")
    g_badge_c  = "#15803d" if global_pct > 80 else ("#a16207" if global_pct >= 50 else "#b91c1c")

    # 5 cols objetivos + 1 global
    cols = st.columns([1, 1, 1, 1, 1, 1])

    for i, obj in enumerate(objs_order):
        meta_k, comp_k, comp_lbl, max_m, max_c, is_pct = _OBJ_CFG[obj]
        color = obj_colors[obj]
        pct   = skpis[obj]["pct"]
        data  = skpis[obj]

        with cols[i]:
            # ── Tarjeta visual ─────────────────────────────────────────────
            st.markdown(_kpi_card_top(obj, pct, color, data), unsafe_allow_html=True)

            # ── Panel de edición pegado a la tarjeta ───────────────────────
            st.markdown(
                f"<div style='background:#f8faff;border:1px solid #c7d9f8;border-top:none;"
                f"border-radius:0 0 12px 12px;padding:8px 10px 4px;"
                f"box-shadow:0 2px 4px rgba(0,0,0,.04);'>"
                f"<div style='font-size:9px;font-weight:700;text-transform:uppercase;"
                f"letter-spacing:.8px;color:{color};margin-bottom:4px;'>✏ Editar</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
            lbl_m = "Meta %" if is_pct else "Meta"
            lbl_c = "Actual %" if is_pct else comp_lbl
            ea, eb = st.columns(2)
            with ea:
                v_meta = st.number_input(
                    lbl_m, min_value=1, max_value=max_m,
                    value=int(sd.get(meta_k, 1)),
                    step=1, key=f"w_{meta_k}",
                    label_visibility="visible",
                )
                sd[meta_k] = v_meta  # ← escribe a _sd (persiste siempre)

            with eb:
                v_comp = st.number_input(
                    lbl_c, min_value=0, max_value=max_c,
                    value=int(sd.get(comp_k, 0)),
                    step=1, key=f"w_{comp_k}",
                    label_visibility="visible",
                )
                sd[comp_k] = v_comp  # ← escribe a _sd (persiste siempre)

    # ── Cumplimiento Global ────────────────────────────────────────────────
    with cols[5]:
        st.markdown(
            f"<div style='background:linear-gradient(160deg,#1d6af5 0%,#0891b2 100%);"
            f"border-radius:12px;padding:20px 12px;text-align:center;"
            f"box-shadow:0 4px 18px rgba(29,106,245,.28);min-height:218px;"
            f"display:flex;flex-direction:column;justify-content:center;align-items:center;'>"
            f"<div style='font-size:9px;font-weight:800;color:rgba(255,255,255,.7);"
            f"text-transform:uppercase;letter-spacing:1.2px;margin-bottom:10px;line-height:1.4;'>"
            f"Cumplimiento<br>Estratégico<br>Global</div>"
            f"<div style='font-size:3rem;font-weight:900;color:white;line-height:1;"
            f"margin-bottom:10px;'>{global_pct:.1f}%</div>"
            f"<div style='background:rgba(255,255,255,.2);color:white;font-size:10px;"
            f"font-weight:700;padding:3px 10px;border-radius:20px;margin-bottom:8px;'>"
            f"{g_icon}</div>"
            f"<div style='font-size:9px;color:rgba(255,255,255,.5);'>5 objetivos · TD 2026</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-top:.5rem'></div>", unsafe_allow_html=True)


def render_global_vision(skpis: dict):
    """
    SECCIÓN 2 — Radar estratégico + Barras comparativas.
    """
    _sec_header("🎯", "Radar Estratégico — Perfil de Cumplimiento")

    col_left, col_right = st.columns([1, 2])
    with col_left:
        st.markdown(
            "<div style='font-size:12px;font-weight:600;color:#475569;margin-bottom:4px;'>"
            "Comparativa por objetivo</div>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(chart_barras_objetivos(skpis), use_container_width=True, key="ev_barras")

    with col_right:
        st.plotly_chart(chart_radar_estrategico(skpis), use_container_width=True, key="ev_radar")


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
    _sec_header("📄", "Exportar Informe")
    skpis_for_pdf = calculate_strategic_kpis()
    render_pdf_download_button(skpis_for_pdf, df, key_suffix="strategic")

    st.caption("Vista Estratégica TD 2026 · Vicepresidencia Transformación Digital · "
               "Metas editables en tiempo real")



# ─────────────────────────────────────────────────────────────────────────────
# 17. GENERADOR DE INFORME PDF — "Informe TD 2026"
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
    """
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

    # Hitos estratégicos
    hitos_df = sd.get("hitos_tabla", pd.DataFrame())
    if len(hitos_df) > 0:
        story.append(_section_title("Hitos Estratégicos", "▪"))
        story.append(Spacer(1, 0.2*cm))
        hitos_show = hitos_df[["Objetivo Estratégico","Hito","Fecha","Responsable","Estado (%)","Comentario"]].copy()
        hitos_show["Estado (%)"] = hitos_show["Estado (%)"].astype(str) + "%"
        hitos_show["Fecha"] = hitos_show["Fecha"].astype(str)
        story.append(_df_to_table(
            hitos_show.rename(columns={"Objetivo Estratégico":"Objetivo","Estado (%)":"Estado %"}),
            col_widths=[3.8*cm, 4.5*cm, 2.2*cm, 3*cm, 1.8*cm, 3.7*cm],
        ))
        story.append(Spacer(1, 0.5*cm))

    # Entregables
    entregables_df = sd.get("entregables_tabla", pd.DataFrame())
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
        retras  = df.get("esta_retrasada", pd.Series([False]*total)).sum()
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
        if "asignado" in df.columns and "progreso" in df.columns:
            story.append(_section_title("Distribución por Especialista (Top 10)", "▪"))
            story.append(Spacer(1, 0.2*cm))
            esp_df = (
                df.groupby("asignado")
                .agg(Total=("titulo","count"),
                     Completados=("progreso", lambda x: (x=="Completado").sum()))
                .assign(**{"% Cumpl.": lambda d: (d["Completados"]/d["Total"]*100).round(1).astype(str)+"%"})
                .sort_values("Total", ascending=False)
                .head(10)
                .reset_index()
                .rename(columns={"asignado": "Especialista"})
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
    """Renderiza el botón de generación y descarga del PDF."""
    sd = st.session_state.get("_sd", {})
    fecha_file = datetime.today().strftime("%Y%m%d")

    col_btn, col_hint = st.columns([2, 5])
    with col_btn:
        if st.button("📄 Generar Informe PDF", key=f"btn_pdf_{key_suffix}",
                     type="primary", use_container_width=True):
            with st.spinner("⚙ Generando Informe TD 2026..."):
                try:
                    pdf_bytes = generate_pdf_report(skpis, sd, df)
                    st.session_state["_pdf_bytes"] = pdf_bytes
                    st.session_state["_pdf_ready"] = True
                except Exception as e:
                    st.error(f"❌ Error generando PDF: {e}")
                    st.session_state["_pdf_ready"] = False

    if st.session_state.get("_pdf_ready"):
        with col_btn:
            st.download_button(
                label="⬇ Descargar PDF",
                data=st.session_state["_pdf_bytes"],
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
    """
    sd = st.session_state["_sd"]

    col_brand, col_nav, col_date = st.columns([2, 3, 2])
    with col_brand:
        st.markdown(
            "<div style='padding:8px 0 0;font-size:17px;font-weight:900;color:#0f1c2e;'>"
            "⚡ TD 2026 Analytics</div>",
            unsafe_allow_html=True,
        )
    with col_nav:
        # key="w_nav" → widget key, sd["nav_vista"] → data store
        current_idx = 0 if "Estratégicos" not in sd.get("nav_vista", "") else 1
        selected = st.radio(
            "Vista",
            options=["🟢  Control Operativo", "🔵  Indicadores Estratégicos"],
            index=current_idx,
            horizontal=True,
            label_visibility="collapsed",
            key="w_nav",
        )
        sd["nav_vista"] = selected  # ← persiste en _sd

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

    # 2. Selector de vistas fijo en top (lee/escribe _sd)
    vista = render_view_selector()

    # 3. Sidebar: solo para carga de archivo
    with st.sidebar:
        st.markdown(
            "<div style='font-size:14px;font-weight:700;color:#0f1c2e;"
            "padding:8px 0 4px;'>📂 Fuente de datos</div>",
            unsafe_allow_html=True,
        )
        uploaded = st.file_uploader(
            "Excel de Planner", type=["xlsx", "xls"],
            help="Exporta desde Microsoft Planner → Exportar a Excel",
        )
        if uploaded:
            st.success("✅ Archivo cargado", icon="📊")
        else:
            st.caption("Sin archivo — métricas de portafolio no disponibles.")
        st.markdown("---")
        st.caption(f"v5.0 · {datetime.today().strftime('%d/%m/%Y')}")

    # 4. Cargar y procesar Excel
    df, meta_d = pd.DataFrame(), {}
    if uploaded is not None:
        with st.spinner("⚙ Procesando datos..."):
            raw_df = load_data(uploaded)
            if not raw_df.empty:
                df, meta_d = preprocess_data(raw_df)
        if meta_d.get("missing_cols"):
            with st.expander(f"⚠ {len(meta_d['missing_cols'])} columnas no encontradas"):
                st.warning("Columnas no encontradas:\n" + ", ".join(meta_d["missing_cols"]))

    # 5. Enrutar vista
    if "Estratégicos" in vista:
        create_executive_view(df)
    else:
        _render_operational_view(df, meta_d, uploaded)


def _render_operational_view(df: pd.DataFrame, meta_d: dict, uploaded):
    """Vista Operativa — sin cambios."""
    if uploaded is None:
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
