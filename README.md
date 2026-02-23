# ⚡ Dashboard Gestión de Requerimientos TD 2026

Aplicación profesional en **Streamlit** para analizar archivos Excel exportados desde **Microsoft Planner**.  
Diseñada para equipos de Transformación Digital con visión ejecutiva nivel Dirección.

---

## 📁 Estructura del Proyecto

```
planner_dashboard/
├── app.py               # Aplicación principal (toda la lógica)
├── requirements.txt     # Dependencias Python
├── README.md            # Este archivo
└── .streamlit/
    └── config.toml      # Configuración visual (opcional)
```

---

## 🚀 Despliegue en Streamlit Cloud (paso a paso)

### Paso 1 — Preparar repositorio en GitHub

1. Crea un repositorio en [github.com](https://github.com) (puede ser privado)
2. Sube los archivos:
   ```
   app.py
   requirements.txt
   README.md
   ```
3. Haz commit y push

### Paso 2 — Crear cuenta en Streamlit Cloud

1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Inicia sesión con tu cuenta de **GitHub**
3. Autoriza el acceso al repositorio

### Paso 3 — Crear nueva App

1. Click en **"New app"**
2. Selecciona tu repositorio y rama (`main`)
3. Archivo principal: `app.py`
4. Click en **"Deploy!"**

> ⏱ El primer despliegue tarda ~2 minutos mientras instala dependencias.

### Paso 4 — Usar la aplicación

1. Abre Microsoft Planner → tu plan
2. Click en **"..."** (opciones) → **"Exportar a Excel"**
3. Sube el `.xlsx` directamente en el panel lateral de la app

---

## 🏗️ Arquitectura de Funciones

| Función | Responsabilidad |
|---|---|
| `load_data(file)` | Carga el Excel con caché |
| `preprocess_data(df)` | Limpia, normaliza fechas, calcula lead time |
| `extract_strategic_category(label)` | Detecta categoría OKR desde Etiquetas |
| `calculate_kpis(df)` | KPIs ejecutivos del portafolio |
| `calculate_workload(df)` | Tabla de carga por especialista |
| `style_workload(wl)` | Semáforos y highlights visuales |
| `apply_sidebar_filters(df)` | Filtros dinámicos en sidebar |
| `create_dashboard(df, meta)` | Orquesta todo el layout |
| `chart_*()` | Gráficos Plotly individuales |

---

## 🎯 KPIs y Métricas Calculadas

- **Total / % Completados / En Curso / No Iniciados / Con Retraso**
- **Lead Time promedio** = `Fecha finalización − Fecha creación`
- **Lead Time por especialista** (solo tareas completadas)
- **Velocidad mensual** = tareas completadas por mes
- **Carga activa** = tareas ≠ Completado
- **Vencidas abiertas** = `Vencimiento < HOY AND Progreso ≠ Completado`
- **% Cumplimiento** = `Completadas / Total asignadas × 100`

---

## 🎨 Semáforos de Cumplimiento

| Color | Umbral | Significado |
|---|---|---|
| 🟢 Verde | ≥ 60% | Óptimo |
| 🟡 Amarillo | 30–59% | En seguimiento |
| 🔴 Rojo | < 30% | Alerta crítica |

**Highlights de fila:**
- 🟥 Fondo rojo → especialista tiene tareas vencidas abiertas
- 🟨 Fondo amarillo → carga activa ≥ 4 tareas (umbral configurable)

---

## 📊 Categorías Estratégicas (detección automática)

Extraídas desde la columna `Etiquetas` mediante expresiones regulares:

| Categoría | Patrón detectado |
|---|---|
| Excelencia ERP | `Excelencia ERP`, emoji `🟨` |
| Eficiencia Operativa | `Eficiencia Operativa`, emoji `🟦` |
| Seguridad de la Información | `Seguridad`, emoji `🟥` |
| Datos Confiables | `Datos Confiables`, emoji `🟩` |
| Integración | `Integración`, `Integracion` |

---

## ⚙️ Ejecución Local

```bash
# Clonar o descargar el proyecto
cd planner_dashboard

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
streamlit run app.py
```

La app abre en `http://localhost:8501`

---

## 🔧 Personalización

### Cambiar umbral de carga alta
En `style_workload()`:
```python
UMBRAL_ACTIVAS = 4  # Cambiar a tu criterio
```

### Agregar nueva categoría estratégica
En `STRATEGIC_PATTERNS`:
```python
"Nueva Categoría": r"patron_regex",
```

Y en `CATEGORY_COLORS`:
```python
"Nueva Categoría": "#hexcolor",
```

---

*Dashboard TD 2026 · Transformación Digital · Desarrollado con Streamlit + Plotly*
