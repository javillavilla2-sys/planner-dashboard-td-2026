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

      /* ── VISTA ESTRATÉGICA ─────────────────────────────────────────────── */

      /* Tarjeta de objetivo estratégico */
      .obj-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 20px 24px;
        box-shadow: 0 1px 6px rgba(0,0,0,.06);
        position: relative;
        overflow: hidden;
        transition: box-shadow .2s;
      }
      .obj-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,.10); }
      .obj-card-accent {
        position: absolute; top: 0; left: 0;
        width: 4px; height: 100%;
        border-radius: 14px 0 0 14px;
      }
      .obj-label {
        font-size: 10px; font-weight: 700; text-transform: uppercase;
        letter-spacing: 1px; color: #8fa0b8; margin-bottom: 6px;
      }
      .obj-pct {
        font-size: 2.6rem; font-weight: 900; line-height: 1;
        margin-bottom: 4px;
      }
      .obj-meta { font-size: 11px; color: #94a3b8; margin-top: 6px; }

      /* Semáforo badge */
      .badge-green  { display:inline-block; background:#dcfce7; color:#15803d;
                      font-size:11px; font-weight:700; padding:3px 10px;
                      border-radius:20px; }
      .badge-yellow { display:inline-block; background:#fef9c3; color:#a16207;
                      font-size:11px; font-weight:700; padding:3px 10px;
                      border-radius:20px; }
      .badge-red    { display:inline-block; background:#fee2e2; color:#b91c1c;
                      font-size:11px; font-weight:700; padding:3px 10px;
                      border-radius:20px; }

      /* Panel de configuración editable */
      .config-panel {
        background: #f8faff;
        border: 1px solid #dbeafe;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 1rem;
      }
      .config-title {
        font-size: 12px; font-weight: 700; text-transform: uppercase;
        letter-spacing: 1px; color: #3b82f6; margin-bottom: 12px;
        display: flex; align-items: center; gap: 8px;
      }

      /* Indicador global */
      .global-kpi {
        background: linear-gradient(135deg, #1d6af5 0%, #0891b2 100%);
        border-radius: 16px;
        padding: 28px 32px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 20px rgba(29,106,245,.25);
      }
      .global-kpi-label { font-size: 12px; font-weight: 600; opacity: .8;
                          text-transform: uppercase; letter-spacing: 1px; }
      .global-kpi-value { font-size: 4rem; font-weight: 900; line-height: 1.1; }
      .global-kpi-sub   { font-size: 12px; opacity: .7; margin-top: 4px; }

      /* Nav pills sidebar */
      .nav-pill {
        display: block; width: 100%; text-align: left;
        padding: 10px 14px; border-radius: 8px; margin-bottom: 4px;
        font-size: 13px; font-weight: 600; cursor: pointer;
        border: none; background: transparent; transition: all .15s;
      }
      .nav-pill.active { background: #eff6ff; color: #1d6af5; }
      .nav-pill:hover  { background: #f1f5f9; }
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
def style_workload(wl: pd.DataFrame) -> pd.DataFrame.style:
    """Aplica semáforos, highlights y formato visual a la tabla de carga."""

    UMBRAL_ACTIVAS = 4  # ≥ X activas → highlight amarillo

    def color_cumplimiento(val):
        if pd.isna(val):
            return "color: #94a3b8"
        if val >= 60:
            return "color: #0da063; font-weight: 700"
        elif val >= 30:
            return "color: #d97706; font-weight: 700"
        else:
            return "color: #e03030; font-weight: 700"

    def color_row(row):
        styles = [""] * len(row)
        cols = list(row.index)
        if row.get("Vencidas Abiertas", 0) > 0:
            bg = "background: #fff0f0"
        elif row.get("Carga Activa", 0) >= UMBRAL_ACTIVAS:
            bg = "background: #fffbeb"
        else:
            bg = ""
        return [bg] * len(row)

    def fmt_lead(val):
        if pd.isna(val):
            return "—"
        return f"{val:.1f} d"

    def fmt_pct(val):
        if pd.isna(val):
            return "—"
        emoji = "🟢" if val >= 60 else ("🟡" if val >= 30 else "🔴")
        return f"{emoji} {val:.1f}%"

    display = wl.copy()
    display["% Cumplimiento"]  = display["% Cumplimiento"].apply(fmt_pct)
    display["Lead Time (días)"] = display["Lead Time (días)"].apply(fmt_lead)
    display.index = range(1, len(display) + 1)

    styled = (
        display.style
        .apply(color_row, axis=1)
        .set_properties(**{
            "font-size":  "13px",
            "text-align": "center",
        })
        .set_properties(subset=["Especialista"], **{
            "text-align":  "left",
            "font-weight": "600",
        })
        .set_table_styles([
            {"selector": "thead th", "props": [
                ("background", "#f4f6fb"),
                ("font-size", "10px"),
                ("font-weight", "700"),
                ("text-transform", "uppercase"),
                ("letter-spacing", "0.6px"),
                ("color", "#64748b"),
                ("padding", "10px 14px"),
                ("border-bottom", "2px solid #e2e8f0"),
            ]},
            {"selector": "tbody td", "props": [
                ("padding", "10px 14px"),
                ("border-bottom", "1px solid #f1f5f9"),
            ]},
            {"selector": "tbody tr:hover td", "props": [
                ("background", "#f8faff !important"),
            ]},
        ])
    )
    return styled


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

    fig.update_layout(
        annotations=[dict(
            text=f"<b style='font-size:18px'>{pct_comp}%</b><br>"
                 f"<span style='font-size:10px;color:#8fa0b8'>de {total} reqs.</span>",
            x=0.5, y=0.5,
            font=dict(size=14, family="Inter, sans-serif", color="#0f1c2e"),
            showarrow=False,
            align="center",
        )],
        legend=dict(
            orientation="h",
            x=0.5, xanchor="center",
            y=-0.08, yanchor="top",
            font=dict(size=11, family="Inter, sans-serif"),
            itemgap=12,
        ),
        margin=dict(l=10, r=10, t=10, b=10),
        height=290,
        paper_bgcolor="white",
        font=dict(family="Inter, sans-serif"),
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
        legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center",
                    font=dict(size=11, family="Inter, sans-serif"), itemgap=16),
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
    col_l4.markdown("🟥 Fondo rojo = tiene vencidas abiertas")

    if not wl.empty:
        styled_wl = style_workload(wl)
        st.dataframe(styled_wl, use_container_width=True, height=min(60 + 48 * len(wl), 520))

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

    st.caption("Dashboard TD 2026 · Transformación Digital · Datos de Microsoft Planner")


# ─────────────────────────────────────────────────────────────────────────────
# 11. INICIALIZACIÓN DE SESSION STATE ESTRATÉGICO
# ─────────────────────────────────────────────────────────────────────────────
def init_session_state():
    """Inicializa los valores por defecto de metas estratégicas en session_state.
    Solo se ejecuta una vez; valores editables desde la UI sin tocar el código."""

    defaults = {
        # ── Eficiencia Operativa ───────────────────────────────────────────────
        "eo_meta":        20,      # Meta trimestral procesos
        "eo_completados": 0,       # Procesos completados

        # ── Datos Confiables ───────────────────────────────────────────────────
        "dc_meta": 5,              # Meta procesos automáticos
        "dc_tabla": pd.DataFrame({
            "Proceso":   ["Juan Montoya", "Ventas VP"],
            "% Avance":  [100, 60],
        }),

        # ── Excelencia ERP ─────────────────────────────────────────────────────
        "erp_meta": 10,            # Meta mejoras ERP
        "erp_tabla": pd.DataFrame({
            "Mejora ERP": ["Módulo de compras", "Cierre contable", "Reportes"],
            "% Avance":   [80, 50, 30],
        }),

        # ── Integración ────────────────────────────────────────────────────────
        "int_meta":        5,      # Meta integraciones
        "int_completadas": 0,      # Completadas

        # ── Seguridad de la Información ────────────────────────────────────────
        "seg_pct_cookies":    0.0, # % ajuste cookies
        "seg_meta_conting":   10,  # Meta procesos contingencia
        "seg_comp_conting":   0,   # Procesos completados contingencia
        "seg_pct_mdm":        0.0, # % MDM dispositivos
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ─────────────────────────────────────────────────────────────────────────────
# 12. CÁLCULO DE KPIs ESTRATÉGICOS
# ─────────────────────────────────────────────────────────────────────────────
def calculate_strategic_kpis() -> dict:
    """Calcula los % de cumplimiento de cada objetivo estratégico
    a partir de los valores editados en session_state."""

    ss = st.session_state

    # ── 1. Eficiencia Operativa ────────────────────────────────────────────────
    meta_eo = max(ss.get("eo_meta", 1), 1)
    pct_eo  = min(round(ss.get("eo_completados", 0) / meta_eo * 100, 1), 100)

    # ── 2. Datos Confiables ────────────────────────────────────────────────────
    meta_dc  = max(ss.get("dc_meta", 1), 1)
    df_dc    = ss.get("dc_tabla", pd.DataFrame({"Proceso": [], "% Avance": []}))
    suma_dc  = float(df_dc["% Avance"].sum()) if len(df_dc) > 0 else 0
    pct_dc   = min(round(suma_dc / (meta_dc * 100) * 100, 1), 100)

    # ── 3. Excelencia ERP ──────────────────────────────────────────────────────
    meta_erp = max(ss.get("erp_meta", 1), 1)
    df_erp   = ss.get("erp_tabla", pd.DataFrame({"Mejora ERP": [], "% Avance": []}))
    suma_erp = float(df_erp["% Avance"].sum()) if len(df_erp) > 0 else 0
    pct_erp  = min(round(suma_erp / (meta_erp * 100) * 100, 1), 100)

    # ── 4. Integración ─────────────────────────────────────────────────────────
    meta_int = max(ss.get("int_meta", 1), 1)
    pct_int  = min(round(ss.get("int_completadas", 0) / meta_int * 100, 1), 100)

    # ── 5. Seguridad de la Información ────────────────────────────────────────
    pct_cookies = float(ss.get("seg_pct_cookies", 0))
    meta_cont   = max(ss.get("seg_meta_conting", 1), 1)
    comp_cont   = ss.get("seg_comp_conting", 0)
    pct_cont    = min(round(comp_cont / meta_cont * 100, 1), 100)
    pct_mdm     = float(ss.get("seg_pct_mdm", 0))
    pct_seg     = round((pct_cookies + pct_cont + pct_mdm) / 3, 1)  # promedio ponderado igual

    # ── Global ────────────────────────────────────────────────────────────────
    global_pct = round((pct_eo + pct_dc + pct_erp + pct_int + pct_seg) / 5, 1)

    return {
        "Eficiencia Operativa":       {"pct": pct_eo,  "meta": meta_eo,  "avance": ss.get("eo_completados", 0)},
        "Datos Confiables":           {"pct": pct_dc,  "meta": meta_dc,  "avance": round(suma_dc, 1)},
        "Excelencia ERP":             {"pct": pct_erp, "meta": meta_erp, "avance": round(suma_erp, 1)},
        "Integración":                {"pct": pct_int, "meta": meta_int, "avance": ss.get("int_completadas", 0)},
        "Seguridad de la Información":{"pct": pct_seg, "meta": "—",      "avance": f"C:{pct_cookies}% / Cont:{pct_cont}% / MDM:{pct_mdm}%"},
        "_global": global_pct,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 13. HELPERS DE SEMÁFORO
# ─────────────────────────────────────────────────────────────────────────────
def semaforo_badge(pct: float) -> str:
    if pct > 80:
        return f'<span class="badge-green">🟢 En meta</span>'
    elif pct >= 50:
        return f'<span class="badge-yellow">🟡 En seguimiento</span>'
    else:
        return f'<span class="badge-red">🔴 En riesgo</span>'

def semaforo_color(pct: float) -> str:
    if pct > 80:  return COLORS["green"]
    if pct >= 50: return COLORS["yellow"]
    return COLORS["red"]

def obj_card_html(titulo: str, pct: float, meta_str: str, color: str) -> str:
    badge = semaforo_badge(pct)
    bar_w = min(int(pct), 100)
    bar_c = semaforo_color(pct)
    return f"""
    <div class="obj-card">
      <div class="obj-card-accent" style="background:{color};"></div>
      <div class="obj-label">{titulo}</div>
      <div class="obj-pct" style="color:{color};">{pct:.1f}%</div>
      <div style="background:#f1f5f9;border-radius:6px;height:6px;margin:8px 0;">
        <div style="background:{bar_c};width:{bar_w}%;height:6px;
                    border-radius:6px;transition:width .6s;"></div>
      </div>
      {badge}
      <div class="obj-meta">{meta_str}</div>
    </div>"""


# ─────────────────────────────────────────────────────────────────────────────
# 14. PANEL DE CONFIGURACIÓN EDITABLE (POR OBJETIVO)
# ─────────────────────────────────────────────────────────────────────────────
def _section_divider(emoji: str, titulo: str):
    st.markdown(
        f"<div style='font-size:12px;font-weight:700;text-transform:uppercase;"
        f"letter-spacing:1px;color:#3b82f6;padding:10px 0 6px;border-bottom:"
        f"2px solid #dbeafe;margin-bottom:12px;'>{emoji} {titulo}</div>",
        unsafe_allow_html=True,
    )

def config_eficiencia_operativa():
    _section_divider("1️⃣", "Eficiencia Operativa")
    c1, c2 = st.columns(2)
    with c1:
        st.session_state["eo_meta"] = st.number_input(
            "Meta trimestral (procesos)", min_value=1, max_value=500,
            value=int(st.session_state["eo_meta"]), step=1, key="inp_eo_meta",
            help="Total de procesos que se espera completar este trimestre",
        )
    with c2:
        st.session_state["eo_completados"] = st.number_input(
            "Procesos completados", min_value=0,
            max_value=int(st.session_state["eo_meta"]),
            value=int(st.session_state["eo_completados"]), step=1, key="inp_eo_comp",
        )
    meta = max(st.session_state["eo_meta"], 1)
    pct  = min(round(st.session_state["eo_completados"] / meta * 100, 1), 100)
    st.progress(pct / 100, text=f"Avance automático: **{pct}%**")
    st.markdown("<br>", unsafe_allow_html=True)


def config_datos_confiables():
    _section_divider("2️⃣", "Datos Confiables")
    c1, _ = st.columns([1, 2])
    with c1:
        st.session_state["dc_meta"] = st.number_input(
            "Meta procesos automáticos", min_value=1, max_value=100,
            value=int(st.session_state["dc_meta"]), step=1, key="inp_dc_meta",
            help="Denominador para calcular el % total del objetivo",
        )
    st.markdown(
        "<div style='font-size:12px;color:#64748b;margin:6px 0 4px;'>"
        "📋 Edita la tabla de procesos y sus avances:</div>",
        unsafe_allow_html=True,
    )
    edited = st.data_editor(
        st.session_state["dc_tabla"],
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Proceso":   st.column_config.TextColumn("Proceso / Responsable", width="medium"),
            "% Avance":  st.column_config.NumberColumn("% Avance", min_value=0, max_value=100, step=1, format="%d%%"),
        },
        key="editor_dc",
    )
    st.session_state["dc_tabla"] = edited
    meta = max(st.session_state["dc_meta"], 1)
    suma = float(edited["% Avance"].sum()) if len(edited) > 0 else 0
    pct  = min(round(suma / (meta * 100) * 100, 1), 100)
    st.info(f"**% Total Datos Confiables = {suma:.0f} / ({meta} × 100) = {pct:.1f}%**")
    st.markdown("<br>", unsafe_allow_html=True)


def config_excelencia_erp():
    _section_divider("3️⃣", "Excelencia ERP")
    c1, _ = st.columns([1, 2])
    with c1:
        st.session_state["erp_meta"] = st.number_input(
            "Meta mejoras ERP", min_value=1, max_value=200,
            value=int(st.session_state["erp_meta"]), step=1, key="inp_erp_meta",
        )
    st.markdown(
        "<div style='font-size:12px;color:#64748b;margin:6px 0 4px;'>"
        "📋 Edita la tabla de mejoras ERP:</div>",
        unsafe_allow_html=True,
    )
    edited = st.data_editor(
        st.session_state["erp_tabla"],
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Mejora ERP": st.column_config.TextColumn("Mejora / Funcionalidad", width="medium"),
            "% Avance":   st.column_config.NumberColumn("% Avance", min_value=0, max_value=100, step=1, format="%d%%"),
        },
        key="editor_erp",
    )
    st.session_state["erp_tabla"] = edited
    meta = max(st.session_state["erp_meta"], 1)
    suma = float(edited["% Avance"].sum()) if len(edited) > 0 else 0
    pct  = min(round(suma / (meta * 100) * 100, 1), 100)
    st.info(f"**% Total Excelencia ERP = {suma:.0f} / ({meta} × 100) = {pct:.1f}%**")
    st.markdown("<br>", unsafe_allow_html=True)


def config_integracion():
    _section_divider("4️⃣", "Integración")
    c1, c2 = st.columns(2)
    with c1:
        st.session_state["int_meta"] = st.number_input(
            "Meta integraciones", min_value=1, max_value=100,
            value=int(st.session_state["int_meta"]), step=1, key="inp_int_meta",
        )
    with c2:
        st.session_state["int_completadas"] = st.number_input(
            "Integraciones completadas", min_value=0,
            max_value=int(st.session_state["int_meta"]),
            value=int(st.session_state["int_completadas"]), step=1, key="inp_int_comp",
        )
    meta = max(st.session_state["int_meta"], 1)
    pct  = min(round(st.session_state["int_completadas"] / meta * 100, 1), 100)
    st.progress(pct / 100, text=f"Avance automático: **{pct}%**")
    st.markdown("<br>", unsafe_allow_html=True)


def config_seguridad():
    _section_divider("5️⃣", "Seguridad de la Información")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.session_state["seg_pct_cookies"] = st.slider(
            "% Ajuste cookies", min_value=0.0, max_value=100.0,
            value=float(st.session_state["seg_pct_cookies"]),
            step=0.5, format="%.1f%%", key="sl_seg_cookies",
        )
    with c2:
        st.session_state["seg_pct_mdm"] = st.slider(
            "% MDM dispositivos", min_value=0.0, max_value=100.0,
            value=float(st.session_state["seg_pct_mdm"]),
            step=0.5, format="%.1f%%", key="sl_seg_mdm",
        )
    with c3:
        pass  # espaciado

    st.markdown(
        "<div style='font-size:12px;color:#64748b;margin:8px 0 4px;'>"
        "🛡️ Procesos críticos de contingencia:</div>",
        unsafe_allow_html=True,
    )
    c4, c5 = st.columns(2)
    with c4:
        st.session_state["seg_meta_conting"] = st.number_input(
            "Meta procesos contingencia", min_value=1, max_value=200,
            value=int(st.session_state["seg_meta_conting"]), step=1, key="inp_seg_meta",
        )
    with c5:
        st.session_state["seg_comp_conting"] = st.number_input(
            "Procesos completados contingencia", min_value=0,
            max_value=int(st.session_state["seg_meta_conting"]),
            value=int(st.session_state["seg_comp_conting"]), step=1, key="inp_seg_comp",
        )

    meta_c = max(st.session_state["seg_meta_conting"], 1)
    pct_c  = min(round(st.session_state["seg_comp_conting"] / meta_c * 100, 1), 100)
    pct_seg = round((st.session_state["seg_pct_cookies"] + pct_c + st.session_state["seg_pct_mdm"]) / 3, 1)

    c6, c7, c8, c9 = st.columns(4)
    c6.metric("Cookies", f"{st.session_state['seg_pct_cookies']:.1f}%")
    c7.metric("Contingencia", f"{pct_c:.1f}%")
    c8.metric("MDM", f"{st.session_state['seg_pct_mdm']:.1f}%")
    c9.metric("⭐ Promedio Seguridad", f"{pct_seg:.1f}%")
    st.markdown("<br>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# 15. GRÁFICOS ESTRATÉGICOS
# ─────────────────────────────────────────────────────────────────────────────
def chart_radar_estrategico(kpis: dict) -> go.Figure:
    """Radar de araña con los 5 objetivos estratégicos."""
    OBJS = [
        "Eficiencia Operativa",
        "Datos Confiables",
        "Excelencia ERP",
        "Integración",
        "Seguridad de la Información",
    ]
    values = [kpis[o]["pct"] for o in OBJS]
    values_closed = values + [values[0]]   # cerrar polígono
    labels_closed = OBJS + [OBJS[0]]

    fig = go.Figure()
    # Zona sombreada de meta (100%)
    fig.add_trace(go.Scatterpolar(
        r=[100] * (len(OBJS) + 1),
        theta=labels_closed,
        fill="toself",
        fillcolor="rgba(226,232,240,0.4)",
        line=dict(color="#e2e8f0", width=1),
        name="Meta 100%",
        hoverinfo="skip",
    ))
    # Valores reales
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=labels_closed,
        fill="toself",
        fillcolor="rgba(29,106,245,0.18)",
        line=dict(color=COLORS["primary"], width=3),
        marker=dict(size=8, color=COLORS["primary"]),
        name="Cumplimiento actual",
        hovertemplate="<b>%{theta}</b><br>%{r:.1f}%<extra></extra>",
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True, range=[0, 100],
                ticksuffix="%", tickfont=dict(size=10, color="#8fa0b8"),
                gridcolor="#e2e8f0", linecolor="#e2e8f0",
            ),
            angularaxis=dict(
                tickfont=dict(size=12, color="#334155", family="Inter, sans-serif"),
                gridcolor="#e2e8f0", linecolor="#e2e8f0",
            ),
            bgcolor="white",
        ),
        showlegend=True,
        legend=dict(orientation="h", y=-0.08, x=0.5, xanchor="center",
                    font=dict(size=11, family="Inter, sans-serif")),
        paper_bgcolor="white",
        margin=dict(l=40, r=40, t=20, b=40),
        height=400,
        font=dict(family="Inter, sans-serif"),
    )
    return fig


def chart_barras_objetivos(kpis: dict) -> go.Figure:
    """Barras horizontales comparativas de los 5 objetivos."""
    OBJS = [
        "Eficiencia Operativa",
        "Datos Confiables",
        "Excelencia ERP",
        "Integración",
        "Seguridad de la Información",
    ]
    pcts   = [kpis[o]["pct"] for o in OBJS]
    colors = [semaforo_color(p) for p in pcts]

    fig = go.Figure(go.Bar(
        x=pcts,
        y=OBJS,
        orientation="h",
        marker_color=colors,
        marker_line_width=0,
        text=[f"{p:.1f}%" for p in pcts],
        textposition="outside",
        textfont=dict(size=13, family="Inter, sans-serif"),
        cliponaxis=False,
    ))
    fig.update_layout(
        xaxis=dict(range=[0, 115], showgrid=True, gridcolor="#f1f5f9",
                   ticksuffix="%", zeroline=False, title=None,
                   tickfont=dict(size=11, color="#8fa0b8")),
        yaxis=dict(showgrid=False, title=None, automargin=True,
                   tickfont=dict(size=12, color="#334155")),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=0, r=60, t=8, b=8),
        height=260,
        bargap=0.38,
        font=dict(family="Inter, sans-serif"),
        shapes=[
            dict(type="line", x0=80, x1=80, y0=-0.5, y1=len(OBJS)-0.5,
                 line=dict(color="#0da063", width=1.5, dash="dash")),
        ],
        annotations=[
            dict(x=81, y=len(OBJS)-0.5, text="Meta 80%",
                 font=dict(size=10, color="#0da063"), showarrow=False,
                 xanchor="left", yanchor="top"),
        ],
    )
    return fig


def chart_reqs_por_categoria(df: pd.DataFrame) -> go.Figure:
    """Barras de reqs por categoría estratégica desde el Excel."""
    if df.empty:
        return go.Figure()
    cat = (
        df.groupby("categoria").size()
        .reset_index(name="count")
        .sort_values("count", ascending=True)
    )
    if cat.empty:
        return go.Figure()
    colors = [CATEGORY_COLORS.get(c, "#94a3b8") for c in cat["categoria"]]
    max_val = cat["count"].max()
    fig = go.Figure(go.Bar(
        x=cat["count"], y=cat["categoria"], orientation="h",
        marker_color=colors, marker_line_width=0,
        text=cat["count"], textposition="outside",
        textfont=dict(size=12, family="Inter, sans-serif"),
        cliponaxis=False,
    ))
    fig.update_layout(
        xaxis=dict(range=[0, max_val * 1.25], showgrid=True, gridcolor="#f1f5f9",
                   title=None, zeroline=False, tickfont=dict(size=11, color="#8fa0b8")),
        yaxis=dict(showgrid=False, title=None, automargin=True,
                   tickfont=dict(size=12, color="#334155")),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=0, r=50, t=8, b=8),
        height=max(200, 42 * len(cat) + 30),
        bargap=0.35,
        font=dict(family="Inter, sans-serif"),
    )
    return fig


def chart_reqs_por_area(df: pd.DataFrame) -> go.Figure:
    """Barras de reqs por área de negocio (etiquetas sin categoría estratégica)."""
    if df.empty:
        return go.Figure()

    skip_patterns = list(STRATEGIC_PATTERNS.values()) + [
        r"excelencia erp", r"eficiencia operativa",
        r"seguridad", r"datos confiables", r"integraci",
    ]
    area_counts = {}
    for etiq in df["etiquetas"].fillna(""):
        for tag in str(etiq).split(";"):
            tag_c = re.sub(r"^[🟨🟦🟩🟥🔴⬛]\s*", "", tag.strip()).strip()
            if not tag_c:
                continue
            if any(re.search(p, tag.lower(), re.IGNORECASE) for p in skip_patterns):
                continue
            if len(tag_c) > 1:
                area_counts[tag_c] = area_counts.get(tag_c, 0) + 1

    if not area_counts:
        return go.Figure()

    areas = (
        pd.Series(area_counts).sort_values(ascending=False).head(12).reset_index()
    )
    areas.columns = ["Área", "Cantidad"]
    max_y = areas["Cantidad"].max()
    palette = ["#1d6af5","#0da063","#6d28d9","#0891b2","#d97706","#e03030",
               "#ea580c","#059669","#7c3aed","#dc2626","#db2777","#2563eb"]
    colors = [palette[i % len(palette)] for i in range(len(areas))]

    fig = go.Figure(go.Bar(
        x=areas["Área"], y=areas["Cantidad"],
        marker_color=colors, marker_line_width=0,
        text=areas["Cantidad"], textposition="outside",
        textfont=dict(size=11, family="Inter, sans-serif"),
        cliponaxis=False,
    ))
    fig.update_layout(
        xaxis=dict(title=None, tickangle=-35, showgrid=False, type="category",
                   tickfont=dict(size=11, color="#334155"), automargin=True),
        yaxis=dict(title=None, showgrid=True, gridcolor="#f1f5f9", zeroline=False,
                   range=[0, max_y * 1.25], tickfont=dict(size=11, color="#8fa0b8")),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=10, r=20, t=8, b=10),
        height=280, bargap=0.35,
        font=dict(family="Inter, sans-serif", size=11),
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# 16. VISTA ESTRATÉGICA – VICEPRESIDENCIA
# ─────────────────────────────────────────────────────────────────────────────
def create_executive_view(df: pd.DataFrame):
    """Vista completa de Indicadores Estratégicos – Vicepresidencia."""

    # ── Header ──────────────────────────────────────────────────────────────
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown(
            "<h2 style='color:#0f1c2e;font-weight:900;margin-bottom:2px;'>"
            "🔵 Indicadores Estratégicos — Vicepresidencia</h2>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='color:#64748b;font-size:14px;margin-top:0;'>"
            "Panel editable de metas y avances por objetivo estratégico TD 2026 · "
            f"Actualizado: {datetime.today().strftime('%d/%m/%Y')}</p>",
            unsafe_allow_html=True,
        )
    with col_h2:
        if not df.empty:
            st.markdown(
                f"<div style='text-align:right;padding-top:16px;'>"
                f"<span style='background:#eff6ff;color:#1d6af5;font-size:12px;"
                f"font-weight:700;padding:6px 14px;border-radius:20px;'>"
                f"📂 {len(df)} reqs. del Excel</span></div>",
                unsafe_allow_html=True,
            )

    # ════════════════════════════════════════════════════════════════════════
    # PANEL DE CONFIGURACIÓN EDITABLE
    # ════════════════════════════════════════════════════════════════════════
    st.markdown(
        "<div style='font-size:11px;font-weight:700;letter-spacing:1.2px;"
        "text-transform:uppercase;color:#8fa0b8;border-bottom:1px solid #e2e8f0;"
        "padding-bottom:6px;margin:1.4rem 0 1rem;'>⚙️ Configuración de Metas Estratégicas</div>",
        unsafe_allow_html=True,
    )

    with st.container():
        st.markdown(
            "<div class='config-panel'>"
            "<div class='config-title'>✏️ Edita las metas y avances de cada objetivo — "
            "los KPIs se actualizan automáticamente</div></div>",
            unsafe_allow_html=True,
        )

    tab_eo, tab_dc, tab_erp, tab_int, tab_seg = st.tabs([
        "1️⃣ Eficiencia Op.",
        "2️⃣ Datos Confiables",
        "3️⃣ Excelencia ERP",
        "4️⃣ Integración",
        "5️⃣ Seguridad Info.",
    ])

    with tab_eo:
        config_eficiencia_operativa()
    with tab_dc:
        config_datos_confiables()
    with tab_erp:
        config_excelencia_erp()
    with tab_int:
        config_integracion()
    with tab_seg:
        config_seguridad()

    # ── Calcular KPIs estratégicos ─────────────────────────────────────────
    skpis = calculate_strategic_kpis()
    OBJS_ORDER = [
        "Eficiencia Operativa",
        "Datos Confiables",
        "Excelencia ERP",
        "Integración",
        "Seguridad de la Información",
    ]
    OBJ_COLORS = {
        "Eficiencia Operativa":        COLORS["green"],
        "Datos Confiables":            COLORS["purple"],
        "Excelencia ERP":              COLORS["primary"],
        "Integración":                 COLORS["cyan"],
        "Seguridad de la Información": COLORS["red"],
    }
    global_pct = skpis["_global"]

    # ════════════════════════════════════════════════════════════════════════
    # KPIs ESTRATÉGICOS — TARJETAS GRANDES
    # ════════════════════════════════════════════════════════════════════════
    st.markdown(
        "<div class='section-header'>📊 Cumplimiento por Objetivo Estratégico</div>",
        unsafe_allow_html=True,
    )
    cols_kpi = st.columns(5)
    for i, obj in enumerate(OBJS_ORDER):
        data   = skpis[obj]
        color  = OBJ_COLORS[obj]
        meta_s = f"Meta: {data['meta']}  ·  Avance: {data['avance']}" if data["meta"] != "—" else f"Avance: {data['avance']}"
        with cols_kpi[i]:
            st.markdown(
                obj_card_html(obj, data["pct"], meta_s, color),
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    # INDICADOR GLOBAL + RADAR
    # ════════════════════════════════════════════════════════════════════════
    st.markdown(
        "<div class='section-header'>🎯 Visión Global Estratégica</div>",
        unsafe_allow_html=True,
    )

    col_global, col_radar = st.columns([1, 2])

    with col_global:
        badge_g  = semaforo_badge(global_pct)
        color_g  = semaforo_color(global_pct)
        bar_g    = min(int(global_pct), 100)
        st.markdown(
            f"<div class='global-kpi'>"
            f"<div class='global-kpi-label'>Cumplimiento Estratégico Global</div>"
            f"<div class='global-kpi-value'>{global_pct:.1f}%</div>"
            f"<div class='global-kpi-sub'>Promedio de 5 objetivos TD 2026</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            "<p style='font-size:12px;font-weight:600;color:#64748b;'>"
            "Comparativa por objetivo:</p>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            chart_barras_objetivos(skpis),
            use_container_width=True, key="ev_barras",
        )

    with col_radar:
        st.markdown(
            "<p style='font-size:13px;font-weight:600;color:#334155;margin-bottom:4px;'>"
            "Radar Estratégico — Perfil de cumplimiento</p>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            chart_radar_estrategico(skpis),
            use_container_width=True, key="ev_radar",
        )

    # ════════════════════════════════════════════════════════════════════════
    # TABLA RESUMEN EJECUTIVA
    # ════════════════════════════════════════════════════════════════════════
    st.markdown(
        "<div class='section-header'>📋 Tabla Resumen Ejecutiva</div>",
        unsafe_allow_html=True,
    )

    summary_rows = []
    for obj in OBJS_ORDER:
        d   = skpis[obj]
        pct = d["pct"]
        estado = "🟢 En meta" if pct > 80 else ("🟡 En seguimiento" if pct >= 50 else "🔴 En riesgo")
        summary_rows.append({
            "Objetivo Estratégico": obj,
            "Meta":                 str(d["meta"]),
            "Avance":               str(d["avance"]),
            "% Cumplimiento":       f"{pct:.1f}%",
            "Estado":               estado,
        })
    summary_df = pd.DataFrame(summary_rows)

    def _style_summary(row):
        pct_val = float(str(row["% Cumplimiento"]).replace("%", ""))
        if pct_val > 80:
            bg = "background: #f0fdf4"
        elif pct_val >= 50:
            bg = "background: #fefce8"
        else:
            bg = "background: #fef2f2"
        return [bg] * len(row)

    styled_summary = (
        summary_df.style
        .apply(_style_summary, axis=1)
        .set_properties(**{"font-size": "13px", "text-align": "left"})
        .set_properties(subset=["% Cumplimiento"],
                        **{"font-weight": "700", "text-align": "center"})
        .set_properties(subset=["Estado"],
                        **{"text-align": "center"})
        .set_table_styles([
            {"selector": "thead th", "props": [
                ("background", "#f4f6fb"), ("font-size", "10px"),
                ("font-weight", "700"), ("text-transform", "uppercase"),
                ("letter-spacing", "0.6px"), ("color", "#64748b"),
                ("padding", "10px 16px"), ("border-bottom", "2px solid #e2e8f0"),
            ]},
            {"selector": "tbody td", "props": [
                ("padding", "12px 16px"), ("border-bottom", "1px solid #f1f5f9"),
            ]},
        ])
    )
    summary_df.index = range(1, len(summary_df) + 1)
    st.dataframe(styled_summary, use_container_width=True, height=260)

    # ════════════════════════════════════════════════════════════════════════
    # INDICADORES DE REQUERIMIENTOS DEL EXCEL
    # ════════════════════════════════════════════════════════════════════════
    st.markdown(
        "<div class='section-header'>📂 Indicadores de Portafolio — Datos del Excel</div>",
        unsafe_allow_html=True,
    )

    if df.empty:
        st.info("📭 Carga un archivo Excel desde el panel lateral para ver los indicadores de portafolio.")
        return

    total_reqs = len(df)
    col_r1, col_r2, col_r3, col_r4 = st.columns(4)
    col_r1.metric("Total Requerimientos", total_reqs)
    col_r2.metric(
        "Por categoría estratégica",
        df["categoria"].nunique(),
        help="Categorías únicas detectadas en etiquetas",
    )
    comp = (df["progreso"] == "Completado").sum()
    col_r3.metric("Completados", comp, f"{round(comp/total_reqs*100,1)}% del total")
    col_r4.metric(
        "Sin asignar",
        (df["asignado_raw"] == "Sin asignar").sum(),
        delta_color="inverse",
    )

    st.markdown("<br>", unsafe_allow_html=True)
    col_rcat, col_rarea = st.columns([1, 1.6])

    with col_rcat:
        st.markdown(
            "<p style='font-size:13px;font-weight:600;color:#334155;margin-bottom:4px;'>"
            "Requerimientos por Categoría Estratégica</p>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            chart_reqs_por_categoria(df),
            use_container_width=True, key="ev_cat",
        )

    with col_rarea:
        st.markdown(
            "<p style='font-size:13px;font-weight:600;color:#334155;margin-bottom:4px;'>"
            "Requerimientos por Área de Negocio</p>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            chart_reqs_por_area(df),
            use_container_width=True, key="ev_area",
        )

    st.caption(
        "Vista Estratégica TD 2026 · Vicepresidencia Transformación Digital · "
        "Metas editables — no requiere modificar el código"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 10. PUNTO DE ENTRADA
# ─────────────────────────────────────────────────────────────────────────────
def main():
    inject_css()
    init_session_state()

    # ── Sidebar ────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(
            "<div style='font-size:18px;font-weight:900;color:#0f1c2e;"
            "padding:8px 0 4px;'>⚡ TD 2026 Analytics</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='font-size:11px;color:#8fa0b8;margin-bottom:16px;'>"
            "Transformación Digital · Planner Dashboard</div>",
            unsafe_allow_html=True,
        )
        st.markdown("---")

        # ── Navegación ─────────────────────────────────────────────────────
        st.markdown(
            "<div style='font-size:10px;font-weight:700;text-transform:uppercase;"
            "letter-spacing:1px;color:#8fa0b8;margin-bottom:8px;'>Vistas</div>",
            unsafe_allow_html=True,
        )
        vista = st.radio(
            "Navegación",
            options=["🟢  Control Operativo", "🔵  Indicadores Estratégicos"],
            index=0,
            label_visibility="collapsed",
        )
        st.markdown("---")

        # ── Carga de archivo ───────────────────────────────────────────────
        st.markdown(
            "<div style='font-size:10px;font-weight:700;text-transform:uppercase;"
            "letter-spacing:1px;color:#8fa0b8;margin-bottom:8px;'>Fuente de datos</div>",
            unsafe_allow_html=True,
        )
        uploaded = st.file_uploader(
            "📂 Excel de Planner",
            type=["xlsx", "xls"],
            help="Exporta tu plan desde Microsoft Planner → Exportar a Excel",
            label_visibility="visible",
        )
        if uploaded:
            st.success("✅ Archivo cargado", icon="📊")
        else:
            st.caption("⚠ Sin archivo — algunas métricas no estarán disponibles.")

        st.markdown("---")
        st.caption(f"v3.0 · {datetime.today().strftime('%d/%m/%Y')}")

    # ── Cargar y procesar datos (si hay archivo) ───────────────────────────
    df     = pd.DataFrame()
    meta_d = {}

    if uploaded is not None:
        with st.spinner("⚙ Procesando datos..."):
            raw_df = load_data(uploaded)
            if not raw_df.empty:
                df, meta_d = preprocess_data(raw_df)

        if meta_d.get("missing_cols"):
            with st.expander(
                f"⚠ {len(meta_d['missing_cols'])} columnas no encontradas",
                expanded=False,
            ):
                st.warning(
                    "Columnas no encontradas (se usarán vacíos):\n"
                    + ", ".join(meta_d["missing_cols"])
                )

    # ── Enrutar vista ──────────────────────────────────────────────────────
    if "Estratégicos" in vista:
        create_executive_view(df)

    else:
        # ── Vista Operativa (sin cambios) ──────────────────────────────────
        if uploaded is None:
            # Landing
            st.markdown("""
            <div style='text-align:center;padding:60px 20px 40px;'>
              <div style='font-size:72px;margin-bottom:16px;'>⚡</div>
              <h1 style='font-size:2.2rem;font-weight:800;color:#0f1c2e;margin-bottom:8px;'>
                Dashboard Gestión de Requerimientos
              </h1>
              <p style='font-size:1.1rem;color:#64748b;margin-bottom:40px;'>
                Analítica ejecutiva para Microsoft Planner · Transformación Digital 2026
              </p>
            </div>
            """, unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info("**📊 KPIs Ejecutivos**\n\nCompletitud, retrasos, lead time y velocidad de entrega en tiempo real.")
            with col2:
                st.info("**👥 Carga de Equipo**\n\nTabla con semáforos de cumplimiento, vencidas abiertas y carga activa.")
            with col3:
                st.info("**🔄 Pipeline Estratégico**\n\nDistribución por categoría OKR, área de negocio y especialista.")
            st.markdown("""
            <div style='text-align:center;margin-top:40px;padding:24px;background:white;
                        border-radius:12px;border:1px solid #e2e8f0;'>
              <p style='color:#64748b;font-size:14px;margin-bottom:8px;'>
                👈 <strong>Sube tu archivo Excel</strong> exportado desde Microsoft Planner
                en el panel lateral para comenzar.
              </p>
              <p style='color:#94a3b8;font-size:12px;'>Formatos soportados: .xlsx · .xls</p>
            </div>
            """, unsafe_allow_html=True)

        elif df.empty:
            st.error("El archivo está vacío o no pudo leerse correctamente.")

        else:
            create_dashboard(df, meta_d)


if __name__ == "__main__":
    main()
