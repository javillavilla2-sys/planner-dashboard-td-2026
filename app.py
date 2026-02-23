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
                    font=dict(size=11, family="Inter, sans-serif")),
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
# 10. PUNTO DE ENTRADA
# ─────────────────────────────────────────────────────────────────────────────
def main():
    inject_css()

    # ── Pantalla de carga ──────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### ⚡ TD 2026 Analytics")
        st.markdown("---")
        uploaded = st.file_uploader(
            "📂 Subir Excel de Planner",
            type=["xlsx", "xls"],
            help="Exporta el plan desde Microsoft Planner → Excel",
        )
        st.markdown("---")

    if uploaded is None:
        # ── Landing / Welcome ──────────────────────────────────────────────
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
            👈 <strong>Sube tu archivo Excel</strong> exportado desde Microsoft Planner en el panel lateral para comenzar.
          </p>
          <p style='color:#94a3b8;font-size:12px;'>
            Formatos soportados: .xlsx · .xls
          </p>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Cargar y procesar ──────────────────────────────────────────────────
    with st.spinner("⚙ Cargando y procesando datos..."):
        raw_df  = load_data(uploaded)
        if raw_df.empty:
            st.error("El archivo está vacío o no pudo leerse correctamente.")
            return

        df, meta = preprocess_data(raw_df)

    # Advertir columnas faltantes (no bloquear)
    if meta.get("missing_cols"):
        with st.expander(f"⚠ {len(meta['missing_cols'])} columnas no encontradas — click para ver"):
            st.warning(
                "Las siguientes columnas no se encontraron y se usarán valores vacíos:\n"
                + ", ".join(meta["missing_cols"])
            )

    create_dashboard(df, meta)


if __name__ == "__main__":
    main()
