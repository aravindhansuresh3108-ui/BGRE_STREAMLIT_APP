import json
from datetime import date, datetime
import streamlit as st
import pandas as pd
import plotly.express as px
import snowflake.connector

# Optional: Excel-style table filters for Data Explorer
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
except Exception:
    AgGrid = None
    GridOptionsBuilder = None
    GridUpdateMode = None

st.set_page_config(page_title="ME2J Procurement Dashboard", page_icon="📊", layout="wide")

conn = snowflake.connector.connect(
    user="BGRE_CLIENT", password="BGRE@123456789a",
    account="TVSNEXT-TVSNEXT", warehouse="BGRE_WH",
    database="SNOWFLAKE_POC", schema="ME2J_SCHEMA"
)

BGR_LOGO_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 220 260" width="88" height="104">
  <circle cx="110" cy="82" r="62" fill="none" stroke="#2060B0" stroke-width="6"/>
  <circle cx="110" cy="82" r="56" fill="#ffffff"/>
  <circle cx="110" cy="82" r="38" fill="none" stroke="#2060B0" stroke-width="5"/>
  <circle cx="110" cy="82" r="33" fill="#ffffff"/>
  <circle cx="110" cy="82" r="16" fill="#D0112B"/>
  <circle cx="110" cy="82" r="5"  fill="#ffffff"/>
  <text x="110" y="182" text-anchor="middle" font-family="Arial,Helvetica,sans-serif"
        font-size="66" font-weight="800" fill="#1A5CA8" letter-spacing="1">BGR</text>
  <text x="110" y="218" text-anchor="middle" font-family="Arial,Helvetica,sans-serif"
        font-size="22" font-weight="600" fill="#D0112B" letter-spacing="7">ENERGY</text>
</svg>"""

PLOTLY_CONFIG = {"displayModeBar": False, "displaylogo": False,
                 "scrollZoom": False, "doubleClick": False, "responsive": True}

CHART_COLORS = {
    "vendor": "#1565C0", "material": "#2E7D32", "plant": "#E65100",
    "doc_type": "#6A1B9A", "delivery": "#C62828", "trend": "#00838F",
    "matl_group": "#00695C", "ai_bar": "#4527A0", "ai_line": "#00695C", "ai_hist": "#E65100",
}

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif !important; }

.kpi-card {
    background: #ffffff; border: 1px solid #e0e7f0; border-radius: 12px;
    padding: 16px 18px 14px; height: 170px;
    box-shadow: 0 1px 4px rgba(0,56,147,0.07);
    position: relative; display: flex; flex-direction: column; overflow: hidden;
}
.kpi-card::after {
    content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #003893, #E31937); border-radius: 0 0 12px 12px;
}
.kpi-title { font-size: 10px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 5px; flex-shrink: 0; }
.kpi-value, .kpi-amount, .kpi-value-sm {
    font-size: 13px !important;
    font-weight: 300 !important;
    color: #003893 !important;
    line-height: 1.7;
    font-family: 'IBM Plex Mono', monospace;
    flex-shrink: 0;
}
.kpi-value-sm {
    overflow-y: auto; flex: 1;
    margin-top: 4px; padding-right: 2px;
    scrollbar-width: thin; scrollbar-color: #c7d7f0 transparent;
}
.kpi-value-sm::-webkit-scrollbar { width: 4px; }
.kpi-value-sm::-webkit-scrollbar-thumb { background: #c7d7f0; border-radius: 4px; }
/* Nuclear option: strip bold from everything inside card except the title */
.kpi-card div:not(.kpi-title),
.kpi-card span,
.kpi-card b,
.kpi-card strong {
    font-weight: 300 !important;
}
.kpi-card .kpi-title { font-weight: 700 !important; }

.section-title { font-size: 16px; font-weight: 700; color: #003893; border-left: 4px solid #E31937; padding-left: 10px; margin: 20px 0 12px; }
.dash-header { background: linear-gradient(135deg,#003893 0%,#001f5b 100%); border-radius: 14px; padding: 20px 28px; display: flex; align-items: center; gap: 18px; margin-bottom: 16px; box-shadow: 0 4px 16px rgba(0,56,147,0.2); }
.dash-header-text { flex: 1; }
.dash-header-title { color: #fff; font-size: 22px; font-weight: 700; margin: 0; }
.dash-header-sub { color: rgba(255,255,255,0.65); font-size: 12px; margin-top: 3px; }
.dash-period { background: #E31937; color: #fff; font-size: 11px; font-weight: 700; padding: 3px 12px; border-radius: 20px; display: inline-block; margin-top: 6px; }
.dash-refresh-info { color: rgba(255,255,255,0.5); font-size: 11px; margin-top: 4px; font-family: 'IBM Plex Mono', monospace; }
.styled-divider { height: 1px; background: linear-gradient(90deg,#003893 0%,#E31937 50%,transparent 100%); border: none; margin: 20px 0; }

.stPlotlyChart *, .js-plotly-plot *, .plot-container *, .svg-container *,
.main-svg *, .cartesianlayer *, .pielayer *, .barlayer *, .scatterlayer *,
.nsewdrag, .drag, .draglayer *, .cursor-crosshair, .cursor-move,
.cursor-pointer, .cursor-ew-resize, .cursor-ns-resize { cursor: default !important; }
.modebar { display: none !important; }

div[data-testid="stButton"] button {
    font-size: 11px !important; font-weight: 600 !important; border-radius: 6px !important;
    padding: 5px 0 !important; border: 1px solid #d1daf0 !important;
    background: #f8faff !important; color: #003893 !important; transition: all 0.15s !important;
}
div[data-testid="stButton"] button:hover { background: #003893 !important; color: #fff !important; border-color: #003893 !important; }

[data-testid="stSidebar"] { background: #f0f4ff !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stDateInput label,
[data-testid="stSidebar"] h3 { font-size: 11px !important; font-weight: 700 !important; color: #334155 !important; text-transform: uppercase; letter-spacing: 0.06em; }
.sidebar-refresh-box { background: #fff; border: 1px solid #dbeafe; border-radius: 10px; padding: 10px 12px; margin-bottom: 12px; }
.sidebar-refresh-label { font-size: 10px; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; }
.sidebar-refresh-value { font-size: 12px; color: #003893; font-weight: 700; font-family: 'IBM Plex Mono', monospace; margin-top: 2px; }

.stChatMessage { border-radius: 12px !important; margin-bottom: 6px !important; }
[data-testid="stBottom"] {
    position: fixed !important; bottom: 0 !important; left: 300px !important; right: 0 !important;
    background: #ffffff !important; z-index: 9999 !important;
    padding: 10px 24px 14px !important; border-top: 2px solid #003893 !important;
    box-shadow: 0 -2px 12px rgba(0,56,147,0.08) !important;
}
section[data-testid="stMain"] > div { padding-bottom: 90px !important; }
[data-testid="stChatInput"] textarea { border-radius: 24px !important; border: 2px solid #d1daf0 !important; font-family: 'IBM Plex Sans', sans-serif !important; font-size: 14px !important; padding: 10px 18px !important; }
[data-testid="stChatInput"] textarea:focus { border-color: #003893 !important; box-shadow: 0 0 0 3px rgba(0,56,147,0.1) !important; outline: none !important; }
div[data-testid="stMetric"] { background: #f8faff; border-radius: 10px; padding: 12px; border: 1px solid #e0e7f0; }
</style>
"""

# ── Helpers ───────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_data():
    return pd.read_sql("SELECT * FROM SNOWFLAKE_POC.ME2J_SCHEMA.ME2J_FINAL_REPORT", conn)

@st.cache_data(ttl=300)
def get_snowflake_last_updated():
    try:
        cols_df = pd.read_sql("""
            SELECT COLUMN_NAME FROM SNOWFLAKE_POC.INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA='ME2J_SCHEMA' AND TABLE_NAME='ME2J_FINAL_REPORT'
              AND UPPER(COLUMN_NAME) IN ('LOAD_TIME','UPDATED_AT','CREATED_AT','LOAD_DATE','ETL_TIMESTAMP')
            LIMIT 1""", conn)
        if not cols_df.empty:
            col = cols_df["COLUMN_NAME"].iloc[0]
            ts_df = pd.read_sql(f'SELECT MAX("{col}") AS TS FROM SNOWFLAKE_POC.ME2J_SCHEMA.ME2J_FINAL_REPORT', conn)
            if not ts_df.empty and ts_df["TS"].iloc[0] is not None:
                return pd.to_datetime(ts_df["TS"].iloc[0]).strftime("%d %b %Y, %I:%M %p"), "Snowflake Load Time"
    except: pass
    try:
        meta_df = pd.read_sql("""SELECT LAST_ALTERED FROM SNOWFLAKE_POC.INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA='ME2J_SCHEMA' AND TABLE_NAME='ME2J_FINAL_REPORT' LIMIT 1""", conn)
        if not meta_df.empty and meta_df["LAST_ALTERED"].iloc[0] is not None:
            return pd.to_datetime(meta_df["LAST_ALTERED"].iloc[0]).strftime("%d %b %Y, %I:%M %p"), "Table Last Altered"
    except: pass
    try:
        date_df = pd.read_sql('SELECT MAX("PO Date") AS MAX_DT FROM SNOWFLAKE_POC.ME2J_SCHEMA.ME2J_FINAL_REPORT', conn)
        if not date_df.empty and date_df["MAX_DT"].iloc[0] is not None:
            ts = pd.to_datetime(date_df["MAX_DT"].iloc[0], dayfirst=True, errors="coerce")
            if pd.notna(ts): return ts.strftime("%d %b %Y"), "Latest PO Date in Data"
    except: pass
    return "—", "Unknown"

def clear_all_caches(): st.cache_data.clear()

def num_fmt(v):
    try: return f"{float(v):,.0f}"
    except: return "0"

# FIX: 3 decimal places for quantities — no rounding confusion
def qty_fmt(v):
    try:
        f = float(v)
        if f == 0: return None          # Return None so caller can skip zeros
        if f == int(f): return f"{f:,.0f}"
        return f"{f:,.3f}"
    except: return None

def compact_inr(v):
    try: v = float(v)
    except: v = 0.0
    if v >= 1e7: return f"₹ {v/1e7:,.2f} Cr"
    if v >= 1e5: return f"₹ {v/1e5:,.2f} L"
    return f"₹ {v:,.2f}"

def compact_usd(v):
    try: v = float(v)
    except: v = 0.0
    if v >= 1e6: return f"$ {v/1e6:,.2f} M"
    if v >= 1e3: return f"$ {v/1e3:,.2f} K"
    return f"$ {v:,.2f}"

def clean_numeric(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df

def kpi_card(title, main_value, sub_lines=None, is_amount=False):
    # Keep all values inside summary cards in the same size and weight.
    # Title remains separate; first value is not enlarged.
    lines = [str(main_value)]
    if sub_lines:
        lines.extend([str(l) for l in sub_lines if l and not str(l).strip().endswith(": 0") and not str(l).strip().endswith(": 0.000")])
    val_html = "<div class='kpi-value-sm'>" + "<br>".join(lines) + "</div>"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">{title}</div>
        {val_html}
    </div>""", unsafe_allow_html=True)

def detail_table(df, rows=25, height=400):
    show_cols = ["PurchDoc","Item","PO Date","Material Code","Project",
                 "Vendor/Supplying plant","Vendor Name","Short Text",
                 "Material Description","Order Unit","PO Quantity","GR Qty",
                 "Still to be del.","Crcy","PO Value","Plant","Matl Group",
                 "Release Status","Del Date"]
    available = [c for c in show_cols if c in df.columns]
    tdf = df[available].copy()

    for dcol in ["PO Date","Del Date"]:
        if dcol in tdf.columns:
            raw = tdf[dcol].copy()
            p1 = pd.to_datetime(raw, errors="coerce", dayfirst=True)
            p2 = pd.to_datetime(raw, errors="coerce")
            parsed = p1.fillna(p2)
            tdf[dcol] = parsed.dt.strftime("%d-%m-%Y").where(parsed.notna(), raw.astype(str))
            tdf[dcol] = tdf[dcol].replace({"NaT":"-","None":"-","nan":"-","NaN":"-"}).fillna("-")

    for c in ["Material Code","Material Description","Project","Vendor Name"]:
        if c in tdf.columns:
            tdf[c] = tdf[c].fillna("-").astype(str).str.strip()
            tdf.loc[tdf[c].isin(["","None","nan","NaN"]),c] = "-"

    # Show 3 decimal for quantity columns
    for qc in ["PO Quantity","GR Qty","Still to be del."]:
        if qc in tdf.columns:
            tdf[qc] = pd.to_numeric(tdf[qc], errors="coerce").round(3)

    display_df = tdf.head(rows)

    if AgGrid is not None:
        gb = GridOptionsBuilder.from_dataframe(display_df)
        gb.configure_default_column(
            filter=True,
            sortable=True,
            resizable=True,
            floatingFilter=True
        )
        gb.configure_pagination(
            paginationAutoPageSize=False,
            paginationPageSize=25
        )
        AgGrid(
            display_df,
            gridOptions=gb.build(),
            height=height,
            fit_columns_on_grid_load=False,
            theme="streamlit"
        )
    else:
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=height
        )

def mini_summary_4col(df):
    a,b,c,d = st.columns(4)
    pv = "PO Value" if "PO Value" in df.columns else "POH"
    inr = usd = 0
    if "Crcy" in df.columns and pv in df.columns:
        inr = df[df["Crcy"].astype(str).str.upper()=="INR"][pv].sum()
        usd = df[df["Crcy"].astype(str).str.upper()=="USD"][pv].sum()
    with a: kpi_card("Records", num_fmt(len(df)))
    with b: kpi_card("Unique POs", num_fmt(df["PurchDoc"].nunique() if "PurchDoc" in df.columns else 0))
    with c: kpi_card("INR Value", compact_inr(inr), is_amount=True)
    with d:
        # FIX: Pending = PO Qty - GR Qty (consistent logic)
        if "PO Quantity" in df.columns and "GR Qty" in df.columns:
            pend = (df["PO Quantity"] - df["GR Qty"]).clip(lower=0).sum()
        else:
            pend = df["Still to be del."].clip(lower=0).sum() if "Still to be del." in df.columns else 0
        kpi_card("Pending Qty", f"{pend:,.3f}")

def build_project_summary(df):
    if "Project" not in df.columns: return pd.DataFrame()
    grp = df[df["Project"].astype(str).str.strip().replace("",pd.NA).notna()].copy()
    if grp.empty: return pd.DataFrame()
    pv = "PO Value" if "PO Value" in grp.columns else None
    result = []
    for proj, g in grp.groupby("Project", dropna=True):
        inr_v = g[g["Crcy"].astype(str).str.upper()=="INR"][pv].sum() if pv and "Crcy" in g.columns else 0
        usd_v = g[g["Crcy"].astype(str).str.upper()=="USD"][pv].sum() if pv and "Crcy" in g.columns else 0
        po_qty = g["PO Quantity"].sum() if "PO Quantity" in g.columns else 0
        gr_q   = g["GR Qty"].sum() if "GR Qty" in g.columns else 0
        # FIX: Pending = PO Qty - GR Qty
        pend   = max(0, po_qty - gr_q)
        po_c   = g["PurchDoc"].nunique() if "PurchDoc" in g.columns else 0
        result.append({
            "Project": proj,
            "PO Count": int(po_c),
            "PO Value (INR)": round(inr_v, 2),
            "PO Value (USD)": round(usd_v, 2),
            "PO Qty":    round(po_qty, 3),
            "GR Qty":    round(gr_q, 3),
            "Pending Qty": round(pend, 3),
        })
    return pd.DataFrame(result).sort_values("PO Value (INR)", ascending=False)

def clean_chart(fig, height=500):
    fig.update_layout(
        height=height, dragmode=False, hovermode="closest", clickmode="event",
        margin=dict(l=8,r=90,t=28,b=55),
        font=dict(family="IBM Plex Sans, sans-serif", size=11),
        plot_bgcolor="rgba(248,250,255,0.5)", paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(font=dict(size=10)),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(0,56,147,0.06)", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(0,56,147,0.06)", zeroline=False)
    for t in fig.data:
        if getattr(t,"type",None) != "pie":
            t.update(selected=dict(marker=dict(opacity=1)), unselected=dict(marker=dict(opacity=0.92)))
    return fig

def chart_event(fig, key):
    return st.plotly_chart(fig, use_container_width=True, key=key,
        on_select=lambda k=key: st.session_state.update({"me2j_active_chart": k}),
        config=PLOTLY_CONFIG)

def get_val(ev, field):
    try:
        if ev and ev.selection.points:
            pt = ev.selection.points[0]
            if field in pt and pt.get(field) is not None: return pt[field]
            for alt in ["label","theta","legendgroup","customdata","point_name","name"]:
                v = pt.get(alt)
                if v is not None:
                    return v[0] if isinstance(v,(list,tuple)) and v else v
    except: pass
    return None

# ── Popup dialog ──────────────────────────────────────────────────────────────
@st.dialog("Drilldown Details", width="large")
def show_popup(title, df):
    st.markdown(f"### {title}")
    pv = "PO Value" if "PO Value" in df.columns else "POH"
    uu = "Order Unit" if "Order Unit" in df.columns else "UOM"

    def fmt_date(series):
        return (pd.to_datetime(series, errors="coerce", dayfirst=True)
                .dt.strftime("%d-%m-%Y").fillna("-"))

    def add_pending_qty(ddf):
        ddf = ddf.copy()
        if "PO Quantity" in ddf.columns:
            ddf["PO Quantity"] = pd.to_numeric(ddf["PO Quantity"], errors="coerce").fillna(0)
        if "GR Qty" in ddf.columns:
            ddf["GR Qty"] = pd.to_numeric(ddf["GR Qty"], errors="coerce").fillna(0)
        if "PO Quantity" in ddf.columns and "GR Qty" in ddf.columns:
            ddf["Pending Qty"] = (ddf["PO Quantity"] - ddf["GR Qty"]).clip(lower=0).round(3)
        elif "Still to be del." in ddf.columns:
            ddf["Pending Qty"] = pd.to_numeric(ddf["Still to be del."], errors="coerce").fillna(0).clip(lower=0).round(3)
        return ddf

    def money_by_currency(g):
        out = {}
        if "Crcy" in g.columns and pv in g.columns:
            vals = g.groupby("Crcy", dropna=False)[pv].sum()
            out["PO Value INR"] = round(float(vals.get("INR", 0)), 2)
            out["PO Value USD"] = round(float(vals.get("USD", 0)), 2)
        elif pv in g.columns:
            out["PO Value"] = round(float(pd.to_numeric(g[pv], errors="coerce").fillna(0).sum()), 2)
        return out

    def base_detail(ddf, extra_cols=None):
        extra_cols = extra_cols or []
        ddf = add_pending_qty(ddf)
        cols = extra_cols + [
            "Release Status", "PurchDoc", "Item", "Project", "Vendor/Supplying plant", "Vendor Name",
            "Short Text", "Material Description", "Order Unit", "PO Quantity", "GR Qty", "Pending Qty",
            "Crcy", "PO Value", "PO Date", "Del Date", "Plant", "Matl Group"
        ]
        cols = [c for c in cols if c in ddf.columns]
        out = ddf[cols].copy()
        for dc in ["PO Date", "Del Date"]:
            if dc in out.columns:
                out[dc] = fmt_date(out[dc])
        for qc in ["PO Quantity", "GR Qty", "Pending Qty", "Still to be del."]:
            if qc in out.columns:
                out[qc] = pd.to_numeric(out[qc], errors="coerce").round(3)
        for vc in ["PO Value", "Net Price"]:
            if vc in out.columns:
                out[vc] = pd.to_numeric(out[vc], errors="coerce").round(2)
        return out

    def show_table(tdf, caption="", height=360):
        if caption:
            st.caption(caption)
        tdf = tdf.copy()
        if len(tdf) == 0:
            st.info("No records available for this selection.")
            return
        if AgGrid is not None:
            gb = GridOptionsBuilder.from_dataframe(tdf)
            gb.configure_default_column(filter=True, sortable=True, resizable=True, floatingFilter=True)
            for nc in ["PO Count", "Vendor Count", "Project Count", "PO Quantity", "GR Qty", "Pending Qty", "PO Value", "PO Value INR", "PO Value USD", "Net Price"]:
                if nc in tdf.columns:
                    gb.configure_column(nc, type=["numericColumn"], filter="agNumberColumnFilter")
            opts = gb.build()
            opts["pagination"] = True
            opts["paginationPageSize"] = 25
            opts["enableCellTextSelection"] = True
            AgGrid(
                tdf,
                gridOptions=opts,
                height=height,
                fit_columns_on_grid_load=False,
                allow_unsafe_jscode=True,
                enable_enterprise_modules=False,
                update_mode=GridUpdateMode.NO_UPDATE if GridUpdateMode is not None else None,
                theme="alpine",
            )
        else:
            st.dataframe(tdf, use_container_width=True, hide_index=True, height=height)

    def group_summary(group_cols, source_df=None):
        source_df = add_pending_qty(source_df if source_df is not None else df)
        group_cols = [c for c in group_cols if c in source_df.columns]
        if not group_cols:
            return pd.DataFrame()
        rows = []
        for keys, g in source_df.groupby(group_cols, dropna=False):
            if not isinstance(keys, tuple):
                keys = (keys,)
            row = {col: val for col, val in zip(group_cols, keys)}
            row["PO Count"] = int(g["PurchDoc"].nunique()) if "PurchDoc" in g.columns else len(g)
            if "Vendor/Supplying plant" in g.columns:
                row["Vendor Count"] = int(g["Vendor/Supplying plant"].nunique())
            if "Project" in g.columns:
                row["Project Count"] = int(g["Project"].astype(str).str.strip().replace("", pd.NA).dropna().nunique())
            if "PO Quantity" in g.columns:
                row["PO Quantity"] = round(float(g["PO Quantity"].sum()), 3)
            if "GR Qty" in g.columns:
                row["GR Qty"] = round(float(g["GR Qty"].sum()), 3)
            if "Pending Qty" in g.columns:
                row["Pending Qty"] = round(float(g["Pending Qty"].sum()), 3)
            row.update(money_by_currency(g))
            rows.append(row)
        out = pd.DataFrame(rows)
        sort_col = "PO Value INR" if "PO Value INR" in out.columns else ("PO Value" if "PO Value" in out.columns else "PO Count")
        return out.sort_values(sort_col, ascending=False)

    st.markdown("##### Summary Breakdown")

    # 1. Total POs: show useful breakdown first, then PO line details
    if "Total POs" in title:
        by_cols = [c for c in ["POrg", "Plant", "Project"] if c in df.columns]
        summary = group_summary(by_cols[:2] if len(by_cols) >= 2 else by_cols)
        if summary.empty:
            summary = pd.DataFrame({"Metric": ["Total POs"], "PO Count": [df["PurchDoc"].nunique() if "PurchDoc" in df.columns else len(df)]})
        show_table(summary, "PO count/value/quantity breakdown", height=300)
        st.markdown("##### PO Line Details")
        show_table(base_detail(df).sort_values("PO Value", ascending=False) if "PO Value" in df.columns else base_detail(df), height=420)

    # 2. Vendors: vendor-wise project/PO/qty/value breakdown
    elif "Vendor" in title and ("Vendors" in title or "vendor" in title.lower()):
        summary = group_summary(["Vendor/Supplying plant", "Vendor Name"])
        show_table(summary, "Vendor-wise PO, project, quantity, GR and pending breakdown", height=360)
        st.markdown("##### Vendor PO Line Details")
        show_table(base_detail(df).sort_values("Vendor Name") if "Vendor Name" in df.columns else base_detail(df), height=420)

    # 3. PO Quantity by UOM
    elif "PO Quantity" in title:
        summary = group_summary([uu])
        if "PO Quantity" in summary.columns:
            summary = summary[summary["PO Quantity"] > 0]
        show_table(summary, "UOM-wise PO quantity with GR and pending", height=320)
        st.markdown("##### PO Quantity Line Details")
        detail = base_detail(df)
        if "PO Quantity" in detail.columns:
            detail = detail[detail["PO Quantity"] > 0].sort_values("PO Quantity", ascending=False)
        show_table(detail, height=420)

    # 4. PO Value by Currency
    elif "PO Value" in title or "Currency" in title:
        summary = group_summary(["Crcy"])
        show_table(summary, "Currency-wise PO value with related PO/quantity counts", height=280)
        st.markdown("##### Currency PO Line Details")
        detail = base_detail(df)
        if "PO Value" in detail.columns:
            detail = detail.sort_values("PO Value", ascending=False)
        show_table(detail, height=420)

    # 5. GR Quantity by UOM
    elif "GR Quantity" in title:
        summary = group_summary([uu])
        if "GR Qty" in summary.columns:
            summary = summary[summary["GR Qty"] > 0]
        show_table(summary, "UOM-wise received quantity with PO and pending", height=320)
        st.markdown("##### GR Quantity Line Details")
        detail = base_detail(df)
        if "GR Qty" in detail.columns:
            detail = detail[detail["GR Qty"] > 0].sort_values("GR Qty", ascending=False)
        show_table(detail, height=420)

    # 6. Pending Delivery by UOM
    elif "Pending" in title:
        dfx = add_pending_qty(df)
        summary = group_summary([uu], dfx)
        if "Pending Qty" in summary.columns:
            summary = summary[summary["Pending Qty"] > 0]
        show_table(summary, "UOM-wise pending delivery with PO and GR", height=320)
        st.markdown("##### Pending PO Line Details")
        detail = base_detail(dfx)
        if "Pending Qty" in detail.columns:
            detail = detail[detail["Pending Qty"] > 0].sort_values("Pending Qty", ascending=False)
        show_table(detail, height=420)

    # 7. Projects: project + vendor-wise details requested by client
    elif "Project" in title:
        dfx = df[df["Project"].astype(str).str.strip().replace("", pd.NA).notna()].copy() if "Project" in df.columns else df.copy()
        summary = group_summary(["Project", "Vendor/Supplying plant", "Vendor Name"], dfx)
        show_table(summary, "Project-wise vendor, PO, PO Qty, GR Qty, Pending Qty and value", height=420)
        st.markdown("##### Project PO Line Details")
        detail = base_detail(dfx)
        if "Project" in detail.columns:
            detail = detail.sort_values(["Project", "Vendor Name", "PurchDoc"], ascending=True, na_position="last") if "Vendor Name" in detail.columns and "PurchDoc" in detail.columns else detail
        show_table(detail, height=440)

    # 8. Material Groups
    elif "Material Group" in title:
        summary = group_summary(["Matl Group", "Vendor Name"])
        show_table(summary, "Material group + vendor breakdown with PO/GR/pending", height=400)
        st.markdown("##### Material Group PO Line Details")
        detail = base_detail(df)
        if "Matl Group" in detail.columns:
            detail = detail.sort_values(["Matl Group", "Vendor Name"], ascending=True, na_position="last") if "Vendor Name" in detail.columns else detail
        show_table(detail, height=420)

    # 9. Release Status: released/not released PO-wise details with PO/GR/Pending
    elif "Release" in title:
        rel_df = df.copy()
        if "Rel Bucket" not in rel_df.columns and "Release Status" in rel_df.columns:
            rel_df["Rel Bucket"] = rel_df["Release Status"].astype(str).str.strip().str.upper().map(
                lambda x: "Released" if x == "R" else "Not Released")
        rel_col = "Rel Bucket" if "Rel Bucket" in rel_df.columns else "Release Status"
        summary = group_summary([rel_col], rel_df)
        summary = summary.rename(columns={rel_col: "Release Status"})
        show_table(summary, "Released vs not released PO count with PO/GR/pending", height=260)
        st.markdown("##### Release Status PO Line Details")
        detail = base_detail(rel_df, extra_cols=[rel_col])
        if rel_col in detail.columns:
            detail = detail.rename(columns={rel_col: "Release Bucket"})
        if "PO Value" in detail.columns:
            detail = detail.sort_values("PO Value", ascending=False)
        show_table(detail, height=440)

    # Chart click drilldowns
    else:
        detail = base_detail(df)
        if "PO Value" in detail.columns:
            detail = detail.sort_values("PO Value", ascending=False)
        show_table(detail, "Chart-selected records", height=440)

    # Download always available
    csv = df.to_csv(index=False).encode("utf-8")
    safe = title[:15].replace(" ", "_")
    st.download_button("⬇ Download", csv, f"ME2J_{safe}.csv", "text/csv",
                       use_container_width=True, key=f"dl_pop_{safe}_{len(df)}")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(BGR_LOGO_SVG, unsafe_allow_html=True)
    st.markdown("**ME2J Procurement Dashboard**")
    st.markdown("---")
    sf_ts, ts_source = get_snowflake_last_updated()
    st.markdown(f"""
    <div class="sidebar-refresh-box">
        <div class="sidebar-refresh-label">Data Last Updated in Snowflake</div>
        <div class="sidebar-refresh-value">{sf_ts}</div>
        <div style="font-size:9px;color:#94a3b8;margin-top:2px;">Source: {ts_source}</div>
    </div>""", unsafe_allow_html=True)
    st.button("🔄 Refresh Data", on_click=clear_all_caches, use_container_width=True)
    st.markdown("---")

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🔍 Data Explorer", "🤖 AI Assistant"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 – DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    df_all = load_data()
    df_all = clean_numeric(df_all, ["PO Value","PO Quantity","GR Qty",
                                     "Still to be del.","Still to be inv.","Net Price"])
    pv_col  = "PO Value"    if "PO Value"    in df_all.columns else "POH"
    qty_col = "PO Quantity" if "PO Quantity" in df_all.columns else "PO Quantity Sto"
    uom_col = "Order Unit"  if "Order Unit"  in df_all.columns else "UOM"
    cur_col = "Crcy"        if "Crcy"        in df_all.columns else "Currency"
    po_date_col = "PO Date" if "PO Date"     in df_all.columns else "Item Doc Date"
    proj_col = "Project"    if "Project"     in df_all.columns else None

    if "Del Date" in df_all.columns:
        df_all["Del Date"] = pd.to_datetime(df_all["Del Date"], errors="coerce", dayfirst=True)
    if po_date_col in df_all.columns:
        df_all[po_date_col] = pd.to_datetime(df_all[po_date_col], errors="coerce", dayfirst=True)

    st.sidebar.subheader("Filters")
    has_plant = "Plant"          in df_all.columns
    has_vendor= "Vendor Name"    in df_all.columns
    has_doc   = "Doc Type"       in df_all.columns
    has_matl  = "Matl Group"     in df_all.columns
    has_rel   = "Release Status" in df_all.columns
    has_proj  = proj_col is not None
    has_mat_code = "Material Code" in df_all.columns
    div_col   = "POrg" if "POrg" in df_all.columns else None
    has_div   = div_col is not None
    has_date  = po_date_col in df_all.columns

    if has_div:
        div_opts = sorted(df_all[div_col].dropna().astype(str).unique().tolist())
        sel_div_list = st.sidebar.multiselect("Purchase Org", div_opts, key="f_div", placeholder="All")
    else: sel_div_list = []

    if has_date:
        mn = df_all[po_date_col].min(); mx = df_all[po_date_col].max()
        default_r = (mn.date() if pd.notna(mn) else date(2026,1,1),
                     mx.date() if pd.notna(mx) else date(2026,3,31))
        dr = st.sidebar.date_input("PO Date Range", value=default_r, key="f_date")
        ds, de = (dr if isinstance(dr,tuple) and len(dr)==2 else (dr,dr))
    else: ds = de = None

    if has_proj:
        proj_opts = sorted(df_all[proj_col].dropna().astype(str).unique().tolist())
        sel_proj_list = st.sidebar.multiselect("Project", proj_opts, key="f_proj", placeholder="All projects")
    else: sel_proj_list = []

    if has_vendor:
        vnd_opts = sorted(df_all["Vendor Name"].dropna().astype(str).unique().tolist())
        sel_vendor_list = st.sidebar.multiselect("Vendor", vnd_opts, key="f_vendor", placeholder="All")
    else: sel_vendor_list = []

    if has_plant:
        plt_opts = sorted(df_all["Plant"].dropna().astype(str).unique().tolist())
        sel_plant_list = st.sidebar.multiselect("Plant", plt_opts, key="f_plant", placeholder="All")
    else: sel_plant_list = []

    if has_doc:
        doc_opts = sorted(df_all["Doc Type"].dropna().astype(str).unique().tolist())
        sel_doc_list = st.sidebar.multiselect("Doc Type", doc_opts, key="f_doc", placeholder="All")
    else: sel_doc_list = []

    if has_matl:
        matl_opts = sorted(df_all["Matl Group"].dropna().astype(str).unique().tolist())
        sel_matl_list = st.sidebar.multiselect("Material Group", matl_opts, key="f_matl", placeholder="All")
    else: sel_matl_list = []

    if has_mat_code:
        mc_opts = sorted(df_all["Material Code"].dropna().astype(str).unique().tolist())
        sel_mc_list = st.sidebar.multiselect("Material Code", mc_opts, key="f_mc", placeholder="All")
    else: sel_mc_list = []

    # Apply filters
    fdf = df_all.copy()
    if has_div    and sel_div_list:    fdf = fdf[fdf[div_col].astype(str).isin(sel_div_list)]
    if has_date   and ds and de:       fdf = fdf[(fdf[po_date_col]>=pd.Timestamp(ds))&(fdf[po_date_col]<=pd.Timestamp(de))]
    if has_proj   and sel_proj_list:   fdf = fdf[fdf[proj_col].astype(str).isin(sel_proj_list)]
    if has_vendor and sel_vendor_list: fdf = fdf[fdf["Vendor Name"].astype(str).isin(sel_vendor_list)]
    if has_plant  and sel_plant_list:  fdf = fdf[fdf["Plant"].astype(str).isin(sel_plant_list)]
    if has_doc    and sel_doc_list:    fdf = fdf[fdf["Doc Type"].astype(str).isin(sel_doc_list)]
    if has_matl   and sel_matl_list:   fdf = fdf[fdf["Matl Group"].astype(str).isin(sel_matl_list)]
    if has_mat_code and sel_mc_list:   fdf = fdf[fdf["Material Code"].astype(str).isin(sel_mc_list)]

    # Header
    sf_ts_hdr, _ = get_snowflake_last_updated()
    st.markdown(f"""
    <div class="dash-header">
        {BGR_LOGO_SVG}
        <div class="dash-header-text">
            <div class="dash-header-title">ME2J Procurement Dashboard</div>
            <div class="dash-header-sub">BGR Energy Systems · SAP Purchase Order Analytics</div>
            <span class="dash-period">📅 Jan 2026 – Mar 2026</span>
            <div class="dash-refresh-info">Data Last Updated in Snowflake: {sf_ts_hdr} &nbsp;·&nbsp; {len(fdf):,} records filtered</div>
        </div>
    </div>""", unsafe_allow_html=True)

    # ── Aggregations — FIX: consistent PO Qty / GR Qty / Pending logic ────────
    qty_uom = (fdf.groupby(uom_col,dropna=True)[qty_col].sum()
               .reset_index(name="Q").sort_values("Q",ascending=False)
               if uom_col in fdf.columns and qty_col in fdf.columns
               else pd.DataFrame(columns=[uom_col,"Q"]))

    gr_uom  = (fdf.groupby(uom_col,dropna=True)["GR Qty"].sum()
               .reset_index(name="G").sort_values("G",ascending=False)
               if uom_col in fdf.columns and "GR Qty" in fdf.columns
               else pd.DataFrame(columns=[uom_col,"G"]))

    # FIX: Pending = PO Qty - GR Qty per UOM (no duplicate join issue)
    if uom_col in fdf.columns and qty_col in fdf.columns and "GR Qty" in fdf.columns:
        _po  = fdf.groupby(uom_col,dropna=True)[qty_col].sum()
        _gr  = fdf.groupby(uom_col,dropna=True)["GR Qty"].sum()
        pend_uom = (_po - _gr).clip(lower=0).reset_index()
        pend_uom.columns = [uom_col, "P"]
        pend_uom = pend_uom[pend_uom["P"] > 0].sort_values("P",ascending=False)
    else:
        pend_uom = pd.DataFrame(columns=[uom_col,"P"])

    cur_sum = (fdf.groupby(cur_col,dropna=True)[pv_col].sum()
               .reset_index(name="V").sort_values("V",ascending=False)
               if cur_col in fdf.columns and pv_col in fdf.columns
               else pd.DataFrame(columns=[cur_col,"V"]))

    rel_df = fdf.copy()
    rel_df["Rel Bucket"] = (
        rel_df["Release Status"].astype(str).str.strip().str.upper()
        .map(lambda x: "Released" if x=="R" else "Not Released")
        if has_rel else "N/A")
    rel_sum = rel_df.groupby("Rel Bucket",dropna=False)["PurchDoc"].nunique().reset_index(name="PO Count")

    inr_val = cur_sum.loc[cur_sum[cur_col].astype(str).str.upper()=="INR","V"].sum() if not cur_sum.empty else 0
    usd_val = cur_sum.loc[cur_sum[cur_col].astype(str).str.upper()=="USD","V"].sum() if not cur_sum.empty else 0
    rel_ok  = rel_sum.loc[rel_sum["Rel Bucket"]=="Released","PO Count"].sum()
    rel_no  = rel_sum.loc[rel_sum["Rel Bucket"]=="Not Released","PO Count"].sum()
    proj_ct = fdf[proj_col].astype(str).str.strip().replace("",pd.NA).dropna().nunique() if has_proj else 0
    matl_ct = fdf["Matl Group"].astype(str).str.strip().replace("",pd.NA).dropna().nunique() if has_matl else 0
    vc_col  = "Vendor/Supplying plant" if "Vendor/Supplying plant" in fdf.columns else ("Vendor Name" if has_vendor else None)

    if "me2j_popup" not in st.session_state:
        st.session_state.me2j_popup = None
        st.session_state.me2j_popup_df = None
    if "me2j_active_chart" not in st.session_state:
        st.session_state.me2j_active_chart = None

    def tpopup(title, df):
        st.session_state.me2j_popup = title
        st.session_state.me2j_popup_df = df

    st.markdown('<div class="section-title">Executive Summary</div>', unsafe_allow_html=True)

    # PO breakdown by org
    if has_div:
        pob = fdf.groupby(div_col,dropna=True)["PurchDoc"].nunique().reset_index(name="C").sort_values("C",ascending=False)
        pob_lines = [f"{r[div_col]}: {num_fmt(r['C'])}" for _,r in pob.iterrows()]
        total_po_main = num_fmt(fdf["PurchDoc"].nunique())
    else:
        pob_lines = None
        total_po_main = num_fmt(fdf["PurchDoc"].nunique())

    # FIX: qty lines with 3 decimal, zero filtered
    def uom_lines(df_uom, val_col):
        lines = []
        for _,r in df_uom.iterrows():
            v = qty_fmt(r[val_col])
            if v: lines.append(f"{r[df_uom.columns[0]]}: {v}")
        return lines

    qty_lines  = uom_lines(qty_uom,  "Q")
    gr_lines   = uom_lines(gr_uom,   "G")
    pend_lines = uom_lines(pend_uom, "P")

    # ROW 1
    c1,c2,c3 = st.columns(3)
    with c1:
        kpi_card("Total POs", total_po_main, sub_lines=pob_lines)
        if st.button("View Details", key="b_pos", use_container_width=True):
            tpopup("Total POs Drilldown", fdf.copy())
    with c2:
        kpi_card("Total Vendors", num_fmt(fdf[vc_col].nunique() if vc_col else 0))
        if st.button("View Details", key="b_vendors", use_container_width=True):
            tpopup("Vendors Drilldown", fdf.copy())
    with c3:
        kpi_card("PO Quantity by UOM",
                 qty_lines[0] if qty_lines else "0",
                 sub_lines=qty_lines[1:] if len(qty_lines)>1 else None)
        if st.button("View Details", key="b_qty", use_container_width=True):
            tpopup("PO Quantity by UOM Drilldown",
                   fdf[fdf[qty_col]>0].copy() if qty_col in fdf.columns else fdf.iloc[0:0])

    # ROW 2
    c4,c5,c6 = st.columns(3)
    with c4:
        kpi_card("PO Value by Currency",
                 f"{compact_inr(inr_val)}  ({inr_val:,.0f})",
                 sub_lines=[f"{compact_usd(usd_val)}  ({usd_val:,.0f})"] if usd_val>0 else None,
                 is_amount=True)
        if st.button("View Details", key="b_val", use_container_width=True):
            tpopup("PO Value by Currency Drilldown",
                   fdf[fdf[pv_col]>0].copy() if pv_col in fdf.columns else fdf.iloc[0:0])
    with c5:
        kpi_card("GR Quantity by UOM",
                 gr_lines[0] if gr_lines else "0",
                 sub_lines=gr_lines[1:] if len(gr_lines)>1 else None)
        if st.button("View Details", key="b_gr", use_container_width=True):
            tpopup("GR Quantity by UOM Drilldown",
                   fdf[fdf["GR Qty"]>0].copy() if "GR Qty" in fdf.columns else fdf.iloc[0:0])
    with c6:
        kpi_card("Pending Delivery by UOM",
                 pend_lines[0] if pend_lines else "0",
                 sub_lines=pend_lines[1:] if len(pend_lines)>1 else None)
        if st.button("View Details", key="b_pend", use_container_width=True):
            tpopup("Pending Delivery Quantity by UOM Drilldown",
                   fdf[fdf["Still to be del."]>0].copy() if "Still to be del." in fdf.columns else fdf.iloc[0:0])

    # ROW 3
    c7,c8,c9 = st.columns(3)
    with c7:
        kpi_card("No. of Projects", num_fmt(proj_ct))
        if st.button("View Details", key="b_proj", use_container_width=True):
            pj_df = fdf[fdf[proj_col].astype(str).str.strip().replace("",pd.NA).notna()].copy() if has_proj else fdf.iloc[0:0]
            tpopup("Projects Drilldown", pj_df)
    with c8:
        kpi_card("Material Groups", num_fmt(matl_ct))
        if st.button("View Details", key="b_matl", use_container_width=True):
            tpopup("Material Groups Drilldown",
                   fdf[fdf["Matl Group"].astype(str).str.strip()!=""].copy() if has_matl else fdf.iloc[0:0])
    with c9:
        kpi_card("Release Status",
                 f"✅ Released: {num_fmt(rel_ok)}",
                 sub_lines=[f"⏳ Not Released: {num_fmt(rel_no)}"])
        if st.button("View Details", key="b_rel", use_container_width=True):
            tpopup("Release Status Drilldown", rel_df.copy())

    # Single popup render
    if st.session_state.me2j_popup and st.session_state.me2j_popup_df is not None:
        show_popup(st.session_state.me2j_popup, st.session_state.me2j_popup_df)
        st.session_state.me2j_popup = None
        st.session_state.me2j_popup_df = None

    st.markdown('<hr class="styled-divider">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Procurement Performance Insights</div>', unsafe_allow_html=True)

    chart_popup_title = None
    chart_popup_df    = None
    active_chart      = st.session_state.get("me2j_active_chart")

    r1c1,r1c2 = st.columns(2)
    with r1c1:
        st.markdown("### PO Count by Plant")
        pc = (fdf.groupby("Plant",dropna=True)["PurchDoc"].nunique()
              .reset_index(name="PO Count").sort_values("PO Count",ascending=False).head(20)
              if has_plant else pd.DataFrame(columns=["Plant","PO Count"]))
        fig = px.bar(pc, x="Plant", y="PO Count", text="PO Count",
                     color_discrete_sequence=[CHART_COLORS["plant"]])
        fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        fig.update_layout(xaxis_tickangle=-35)
        ev = chart_event(clean_chart(fig,520), "ch_plant")
        if active_chart=="ch_plant":
            s = get_val(ev,"x")
            if s and has_plant: chart_popup_title=f"Plant: {s}"; chart_popup_df=fdf[fdf["Plant"].astype(str)==str(s)]

    with r1c2:
        st.markdown("### Top Vendors by PO Value")
        vc2 = (fdf.groupby("Vendor Name",dropna=True)
               .agg(PO_Count=("PurchDoc","nunique"), PO_Value=(pv_col,"sum"))
               .reset_index().sort_values("PO_Value",ascending=False).head(15)
               if has_vendor else pd.DataFrame(columns=["Vendor Name","PO_Count","PO_Value"]))
        fig = px.bar(vc2, x="PO_Value", y="Vendor Name", orientation="h",
                     text="PO_Value", custom_data=["PO_Count"],
                     color_discrete_sequence=[CHART_COLORS["vendor"]])
        fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside",
                          hovertemplate="<b>%{y}</b><br>PO Value: %{x:,.2f}<br>POs: %{customdata[0]}<extra></extra>")
        fig.update_layout(yaxis={"automargin":True})
        ev = chart_event(clean_chart(fig,520), "ch_vendor")
        if active_chart=="ch_vendor":
            s = get_val(ev,"y")
            if s and has_vendor: chart_popup_title=f"Vendor: {s}"; chart_popup_df=fdf[fdf["Vendor Name"].astype(str)==str(s)]

    r2c1,r2c2 = st.columns(2)
    with r2c1:
        st.markdown("### PO Quantity by UOM")
        fig = px.bar(qty_uom.rename(columns={uom_col:"UOM","Q":"Total Qty"}),
                     x="UOM", y="Total Qty", text="Total Qty",
                     color_discrete_sequence=[CHART_COLORS["material"]])
        fig.update_traces(texttemplate="%{text:,.3f}", textposition="outside")
        ev = chart_event(clean_chart(fig,480), "ch_qty_uom")
        if active_chart=="ch_qty_uom":
            s = get_val(ev,"x")
            if s: chart_popup_title=f"UOM: {s}"; chart_popup_df=fdf[fdf[uom_col].astype(str)==str(s)]

    with r2c2:
        st.markdown("### PO Value by Currency")
        fig = px.bar(cur_sum.rename(columns={cur_col:"Currency","V":"Total Value"}),
                     x="Currency", y="Total Value", text="Total Value", color="Currency",
                     color_discrete_sequence=[CHART_COLORS["vendor"],CHART_COLORS["material"],CHART_COLORS["doc_type"]])
        fig.update_traces(texttemplate="%{text:,.2f}", textposition="outside")
        fig.update_layout(showlegend=False)
        ev = chart_event(clean_chart(fig,480), "ch_currency")
        if active_chart=="ch_currency":
            s = get_val(ev,"x")
            if s: chart_popup_title=f"Currency: {s}"; chart_popup_df=fdf[fdf[cur_col].astype(str)==str(s)]

    r3c1,r3c2 = st.columns(2)
    with r3c1:
        st.markdown("### GR Quantity by UOM")
        fig = px.bar(gr_uom.rename(columns={uom_col:"UOM","G":"GR Qty"}),
                     x="UOM", y="GR Qty", text="GR Qty",
                     color_discrete_sequence=[CHART_COLORS["trend"]])
        fig.update_traces(texttemplate="%{text:,.3f}", textposition="outside")
        ev = chart_event(clean_chart(fig,480), "ch_gr_uom")
        if active_chart=="ch_gr_uom":
            s = get_val(ev,"x")
            if s: chart_popup_title=f"GR UOM: {s}"; chart_popup_df=fdf[(fdf[uom_col].astype(str)==str(s))&(fdf["GR Qty"]>0)]

    with r3c2:
        st.markdown("### Release Status")
        fig = px.bar(rel_sum, x="Rel Bucket", y="PO Count", text="PO Count", color="Rel Bucket",
                     color_discrete_map={"Released":CHART_COLORS["trend"],"Not Released":CHART_COLORS["delivery"],"N/A":"#94a3b8"})
        fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        fig.update_layout(showlegend=False, xaxis_title="Status")
        ev = chart_event(clean_chart(fig,480), "ch_release")
        if active_chart=="ch_release":
            s = get_val(ev,"x")
            if s: chart_popup_title=f"Release: {s}"; chart_popup_df=rel_df[rel_df["Rel Bucket"].astype(str)==str(s)]

    r4c1,r4c2 = st.columns(2)
    with r4c1:
        st.markdown("### Project Summary")
        if has_proj:
            ps = (fdf[fdf[proj_col].astype(str).str.strip()!=""]
                  .groupby(proj_col,dropna=True)["PurchDoc"].nunique()
                  .reset_index(name="PO Count").sort_values("PO Count",ascending=False).head(15))
        else: ps = pd.DataFrame(columns=["Project","PO Count"])
        fig = px.bar(ps, x="PO Count", y=proj_col if has_proj else "Project", orientation="h",
                     text="PO Count", color_discrete_sequence=[CHART_COLORS["ai_bar"]])
        fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        fig.update_layout(yaxis={"automargin":True}, yaxis_title="")
        ev = chart_event(clean_chart(fig,520), "ch_project")
        if active_chart=="ch_project":
            s = get_val(ev,"y")
            if s and has_proj: chart_popup_title=f"Projects Drilldown"; chart_popup_df=fdf[fdf[proj_col].astype(str)==str(s)]

    with r4c2:
        st.markdown("### Material Group Summary")
        ms = (fdf.groupby("Matl Group",dropna=True)["PurchDoc"].nunique()
              .reset_index(name="PO Count").sort_values("PO Count",ascending=False).head(15)
              if has_matl else pd.DataFrame(columns=["Matl Group","PO Count"]))
        fig = px.bar(ms, x="PO Count", y="Matl Group", orientation="h",
                     text="PO Count", color_discrete_sequence=[CHART_COLORS["matl_group"]])
        fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        fig.update_layout(yaxis={"automargin":True}, yaxis_title="")
        ev = chart_event(clean_chart(fig,520), "ch_matl")
        if active_chart=="ch_matl":
            s = get_val(ev,"y")
            if s and has_matl: chart_popup_title=f"Material Group: {s}"; chart_popup_df=fdf[fdf["Matl Group"].astype(str)==str(s)]

    if chart_popup_title and chart_popup_df is not None:
        show_popup(chart_popup_title, chart_popup_df)

    st.markdown('<hr class="styled-divider">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Detailed Data Preview</div>', unsafe_allow_html=True)
    detail_table(fdf, rows=25)
    csv = fdf.to_csv(index=False).encode("utf-8")
    st.download_button("⬇ Download Filtered Data", csv, "ME2J_FILTERED.csv", "text/csv",
                       use_container_width=True, key="dl_main")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 – DATA EXPLORER  (with global text search)
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Filter & Explore Data")
    df2 = load_data()
    hv2 = "Vendor Name"  in df2.columns
    hp2 = "Plant"        in df2.columns
    hd2 = "Doc Type"     in df2.columns
    hm2 = "Matl Group"   in df2.columns

    # Global text search — Short Text + Material Description
    search_txt = st.text_input("🔍 Search material / description", placeholder="e.g. plate, cement, cable…", key="t2_search")

    e1,e2,e3,e4 = st.columns(4)
    with e1:
        v2 = ["All"]+(sorted(df2["Vendor Name"].dropna().unique().tolist()) if hv2 else [])
        sv2 = st.selectbox("Vendor", v2, key="e_v")
    with e2:
        p2 = ["All"]+(sorted(df2["Plant"].dropna().unique().tolist()) if hp2 else [])
        sp2 = st.selectbox("Plant", p2, key="e_p")
    with e3:
        d2 = ["All"]+(sorted(df2["Doc Type"].dropna().unique().tolist()) if hd2 else [])
        sd2 = st.selectbox("Doc Type", d2, key="e_d")
    with e4:
        m2 = ["All"]+(sorted(df2["Matl Group"].dropna().unique().tolist()) if hm2 else [])
        sm2 = st.selectbox("Material Group", m2, key="e_m")

    f2 = df2.copy()
    if hv2 and sv2 != "All": f2 = f2[f2["Vendor Name"]==sv2]
    if hp2 and sp2 != "All": f2 = f2[f2["Plant"]==sp2]
    if hd2 and sd2 != "All": f2 = f2[f2["Doc Type"]==sd2]
    if hm2 and sm2 != "All": f2 = f2[f2["Matl Group"]==sm2]

    # FIX: Global search across Short Text + Material Description
    if search_txt.strip():
        kw = search_txt.strip().lower()
        mask = pd.Series(False, index=f2.index)
        for col in ["Short Text","Material Description","Material Code","Vendor Name","Project"]:
            if col in f2.columns:
                mask = mask | f2[col].astype(str).str.lower().str.contains(kw, na=False)
        f2 = f2[mask]

    st.caption(f"Showing {len(f2):,} of {len(df2):,} records")

    # Excel-style filterable table
    # Format quantity columns to 3 decimal
    f2_display = f2.copy()
    for qc in ["PO Quantity","GR Qty","Still to be del.","Still to be inv.","To be inv."]:
        if qc in f2_display.columns:
            f2_display[qc] = pd.to_numeric(f2_display[qc], errors="coerce").round(3)
    for vc in ["PO Value","Net Price"]:
        if vc in f2_display.columns:
            f2_display[vc] = pd.to_numeric(f2_display[vc], errors="coerce").round(2)
    for dc in ["PO Date","Del Date"]:
        if dc in f2_display.columns:
            p1 = pd.to_datetime(f2_display[dc], errors="coerce", dayfirst=True)
            p2 = pd.to_datetime(f2_display[dc], errors="coerce")
            parsed = p1.fillna(p2)
            f2_display[dc] = parsed.dt.strftime("%d-%m-%Y").where(parsed.notna(), f2_display[dc].astype(str))

    # Excel-style table with filters directly in column headers
    # Users can click the filter icon / type in the header filter box for each column.
    if AgGrid is not None:
        gb = GridOptionsBuilder.from_dataframe(f2_display)
        gb.configure_default_column(
            sortable=True,
            filter=True,
            resizable=True,
            floatingFilter=True,
            editable=False,
            wrapText=False,
            autoHeight=False,
        )
        for nc in ["PO Value", "Net Price", "PO Quantity", "GR Qty", "Still to be del.", "Still to be inv.", "To be inv."]:
            if nc in f2_display.columns:
                gb.configure_column(nc, type=["numericColumn"], filter="agNumberColumnFilter")
        grid_options = gb.build()
        grid_options["pagination"] = True
        grid_options["paginationPageSize"] = 100
        grid_options["enableCellTextSelection"] = True
        grid_options["sideBar"] = {
            "toolPanels": ["columns", "filters"],
            "defaultToolPanel": ""
        }
        AgGrid(
            f2_display,
            gridOptions=grid_options,
            height=560,
            width="100%",
            fit_columns_on_grid_load=False,
            allow_unsafe_jscode=True,
            enable_enterprise_modules=False,
            update_mode=GridUpdateMode.NO_UPDATE,
            theme="alpine",
        )
    else:
        st.warning("Excel-style column filters need the streamlit-aggrid package. Add streamlit-aggrid to requirements.txt and redeploy. Showing normal table for now.")
        st.dataframe(
            f2_display,
            use_container_width=True,
            height=520,
            hide_index=True,
            column_config={
                "PO Value":        st.column_config.NumberColumn("PO Value",        format="%.2f"),
                "Net Price":       st.column_config.NumberColumn("Net Price",        format="%.2f"),
                "PO Quantity":     st.column_config.NumberColumn("PO Quantity",      format="%.3f"),
                "GR Qty":          st.column_config.NumberColumn("GR Qty",           format="%.3f"),
                "Still to be del.":st.column_config.NumberColumn("Still to be del.", format="%.3f"),
                "Still to be inv.":st.column_config.NumberColumn("Still to be inv.", format="%.3f"),
                "To be inv.":      st.column_config.NumberColumn("To be inv.",       format="%.3f"),
            }
        )
    csv2 = f2.to_csv(index=False).encode("utf-8")
    st.download_button("⬇ Download CSV", csv2, "ME2J_EXPLORER.csv", "text/csv", key="dl_exp")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 – AI ASSISTANT
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    AGENT_FQN = "SNOWFLAKE_POC.ME2J_SCHEMA.BGRE_ME2J_PROCUREMENT_AGENT"
    st.session_state.me2j_active_chart = None

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#003893,#001f5b);border-radius:12px;padding:16px 22px;margin-bottom:16px;display:flex;align-items:center;gap:14px;">
        {BGR_LOGO_SVG}
        <div>
            <div style="color:#fff;font-size:18px;font-weight:700;">ME2J Procurement AI Assistant</div>
            <div style="color:rgba(255,255,255,0.6);font-size:12px;margin-top:2px;">Powered by Snowflake Cortex Analyst · ME2J_PURCHASE_ORDER_REPORT</div>
            <div style="color:rgba(255,255,255,0.5);font-size:11px;margin-top:3px;">Ask about purchase orders, vendors, materials, projects, delivery, price trends</div>
        </div>
    </div>""", unsafe_allow_html=True)

    STRICT_RULES = """You are a procurement data analyst for BGR Energy Systems.
Answer ONLY from SNOWFLAKE_POC.ME2J_SCHEMA.ME2J_FINAL_REPORT.
Do not guess, assume, or use outside knowledge.

AVAILABLE COLUMNS (29 total — use ONLY these):
| Column               | Meaning                                          |
|----------------------|--------------------------------------------------|
| PurchDoc             | Purchase Order number                            |
| Item                 | Line item number within a PO                     |
| PO Date              | PO creation date (format DD-MM-YYYY)             |
| Vendor/Supplying plant | Vendor code / SAP vendor number               |
| Vendor Name          | Full vendor company name                         |
| Short Text           | Short line item description                      |
| Material Code        | SAP material number                              |
| Material Description | Full material name                               |
| PO Quantity          | Ordered quantity                                 |
| Order Unit           | Unit of measure (KG, PC, L, BAG, M2, MT, NOS…)  |
| GR Qty               | Goods Receipt quantity — actually received       |
| Still to be del.     | SAP pending delivery qty (negative = complete)   |
| Crcy                 | Currency code (INR, USD)                         |
| PO Value             | TOTAL line item value in Crcy — USE FOR SPEND    |
| Net Price            | Per-unit price only — NOT total value            |
| Per                  | Pricing unit basis for Net Price                 |
| Plant                | Delivery plant / project site code               |
| Matl Group           | Material category / commodity group              |
| POrg                 | Purchase Organization (1100, 1130, 1140…)        |
| PGr                  | Purchase Group                                   |
| Doc Type             | PO document type (NB, ZNB…)                      |
| Del Date             | Scheduled delivery date                          |
| Del Date Raw         | Raw delivery date string from SAP                |
| Profit Center        | Profit Center code                               |
| Release Status       | R = Released/Approved; blank = Not Released      |
| Project              | Project code linked to PO                        |
| Vald Element         | WBS / Validation element                         |
| To be inv.           | Quantity to be invoiced                          |
| Still to be inv.     | Quantity still pending invoice                   |

BUSINESS RULES — always follow:
R1  PO count           = COUNT(DISTINCT "PurchDoc")
R2  Vendor count       = COUNT(DISTINCT "Vendor/Supplying plant")
R3  Project count      = COUNT(DISTINCT "Project")
R4  Total PO value     = SUM("PO Value") — ALWAYS for spend/value questions
R5  Net Price          = per-unit price — NEVER use SUM("Net Price") for total spend
R6  Quantities         = always GROUP BY "Order Unit" — never sum across different UOMs
R7  Currency values    = always show "Crcy" alongside monetary amounts
R8  Month-wise dates   = TRY_TO_DATE("PO Date", 'DD-MM-YYYY') then DATE_TRUNC('MONTH',…)
R9  Pending delivery   = GREATEST("Still to be del.", 0) OR SUM(PO Qty) - SUM(GR Qty)
R10 Overdue POs        = TRY_TO_DATE("Del Date",'DD-MM-YYYY') < CURRENT_DATE() AND "Still to be del." > 0
R11 Released POs       = UPPER(TRIM("Release Status")) = 'R'
R12 Project-wise       = GROUP BY "Project"
R13 Price trend        = use "Net Price" per unit grouped by month and "Order Unit" — show as unit rate not total
R14 Material search    = use LIKE '%keyword%' on "Material Description" OR "Short Text"
R15 Plate material     = WHERE UPPER("Short Text") LIKE '%PLATE%' OR UPPER("Material Description") LIKE '%PLATE%'

KNOWN VALIDATION TOTALS:
- Total rows: 1,453
- Unique POs: 536
- Total PO Value INR: 450,380,671.69
- Total PO Value USD: 507,235.33
- Total Net Price: 316,246,109.04 (this is NOT procurement value)

PRICE TREND RULE (for questions like 'show plate price trend for project PVA-2025'):
- Use Net Price (per unit rate) grouped by month and Order Unit
- SQL example:
  SELECT TRY_TO_DATE("PO Date",'DD-MM-YYYY') AS PO_DATE,
         DATE_TRUNC('MONTH', TRY_TO_DATE("PO Date",'DD-MM-YYYY')) AS MONTH,
         "Order Unit" AS UOM,
         AVG("Net Price") AS Avg_Unit_Price,
         SUM("PO Quantity") AS Total_Qty,
         SUM("PO Value") AS Total_PO_Value,
         COUNT(DISTINCT "PurchDoc") AS PO_Count
  FROM ME2J_FINAL_REPORT
  WHERE "Project" = 'PVA-2025'
    AND (UPPER("Short Text") LIKE '%PLATE%' OR UPPER("Material Description") LIKE '%PLATE%')
  GROUP BY 1,2,3 ORDER BY 2,3;

MISSING FIELD RULE:
If asked about Project Manager, Project Head, Approver, Approved By, Payment Terms,
GST Number, Invoice Number, Invoice Date, Transporter, LR Number, GRN Number, Department:
Respond EXACTLY: "[FieldName] is not available in the ME2J_FINAL_REPORT dataset.
This field has not been captured in the current SAP extract."
DO NOT substitute with another column.

OFF-TOPIC RULE:
If question not about procurement data, say:
"This question is outside the scope of ME2J procurement data."
"""

    GUARD_MAP = {
        "project manager":"Project Manager","project head":"Project Head",
        "manager wise":"Project Manager","pm wise":"Project Manager",
        "project in charge":"Project In-charge",
        "approver":"Approver Name","approved by":"Approved By",
        "approval person":"Approver Name","who approved":"Approver Name",
        "payment term":"Payment Terms","payment terms":"Payment Terms",
        "gst":"GST Number","gst number":"GST Number","tax invoice":"Tax Invoice Number",
        "invoice number":"Invoice Number","invoice no":"Invoice Number",
        "invoice date":"Invoice Date","transporter":"Transporter Name",
        "lr number":"LR Number","lorry receipt":"LR Number",
        "grn number":"GRN Number","grn date":"GRN Date",
        "department":"Department","bank account":"Bank Account","pan number":"PAN Number",
    }

    def guard_check(q):
        ql = q.lower()
        for k,v in GUARD_MAP.items():
            if k in ql:
                return {"text":f"**{v}** is not available in the ME2J_FINAL_REPORT dataset.\n\nThis field has not been captured in the current SAP extract. Please contact the data team if this field needs to be added.",
                        "sql":None,"table":None,
                        "suggestions":["Show project-wise PO value","Show vendor-wise PO value",
                                       "Show plate material price trend month-wise for project PVA-2025",
                                       "Which vendor has highest pending delivery?"]}
        return None

    def run_agent(q):
        full_q = STRICT_RULES + "\n\nUser Question: " + q
        payload = json.dumps({"messages":[{"role":"user","content":[{"type":"text","text":full_q}]}]})
        safe    = payload.replace("$$","$ $")
        sql     = f"SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN('{AGENT_FQN}', $${safe}$$) AS RESP"
        df_r    = pd.read_sql(sql, conn)
        return df_r["RESP"].iloc[0]

    def parse_resp(raw):
        try: resp = json.loads(raw) if isinstance(raw,str) else raw
        except: return {"text":str(raw),"sql":None,"table":None,"suggestions":[]}
        texts,sql_f,table,suggs = [],[],None,[]
        for item in resp.get("content",[]):
            t = item.get("type")
            if t=="text" and item.get("text"): texts.append(item["text"])
            elif t=="suggested_queries":
                for sq in item.get("suggested_queries",[]):
                    if sq.get("query"): suggs.append(sq["query"])
            elif t=="tool_result":
                for c in item.get("tool_result",{}).get("content",[]):
                    if c.get("type")=="json":
                        j = c.get("json",{})
                        if j.get("text"): texts.append(j["text"])
                        if j.get("sql"):  sql_f = j["sql"]
                        rs = j.get("result_set")
                        if rs and rs.get("data"):
                            cols = [x["name"] for x in rs.get("resultSetMetaData",{}).get("rowType",[])]
                            table = pd.DataFrame(rs["data"], columns=cols if cols else None)
        return {"text":"\n\n".join(texts) if texts else "No response received.",
                "sql":sql_f,"table":table,"suggestions":suggs}

    def ai_chart(df, idx=0):
        if df is None or df.empty: return
        try:
            cdf = df.copy(); cdf.columns = [str(c) for c in cdf.columns]
            dcols = []
            for c in cdf.columns:
                if any(x in c.upper() for x in ["DATE","MONTH","YEAR","PERIOD"]):
                    conv = pd.to_datetime(cdf[c], errors="coerce")
                    if conv.notna().sum()>0: cdf[c]=conv; dcols.append(c)
            for c in cdf.columns:
                if c not in dcols:
                    cv = pd.to_numeric(cdf[c], errors="coerce")
                    if cv.notna().sum()>0: cdf[c]=cv
            nums  = cdf.select_dtypes(include=["number"]).columns.tolist()
            dates = cdf.select_dtypes(include=["datetime64[ns]"]).columns.tolist()
            texts = cdf.select_dtypes(include=["object"]).columns.tolist()
            if not nums and not texts: return
            st.markdown("#### 📊 Visual")
            if len(cdf)==1 and nums:
                cols_ui = st.columns(min(len(nums),4))
                for i,c in enumerate(nums[:4]):
                    with cols_ui[i]: st.metric(c.replace("_"," ").title(), f"{cdf[c].iloc[0]:,.3f}")
                return
            if dates and nums:
                uom_c = next((c for c in texts if "unit" in c.lower() or "uom" in c.lower()), None)
                if uom_c:
                    fig = px.line(cdf.sort_values(dates[0]), x=dates[0], y=nums[0], color=uom_c,
                                  markers=True, title=f"{nums[0]} Trend by Month per UOM",
                                  color_discrete_sequence=px.colors.qualitative.Bold)
                else:
                    fig = px.line(cdf[[dates[0],nums[0]]].dropna().sort_values(dates[0]),
                                  x=dates[0], y=nums[0], markers=True, text=nums[0],
                                  color_discrete_sequence=[CHART_COLORS["ai_line"]])
                    fig.update_traces(texttemplate="%{text:,.3f}", textposition="top center")
                fig.update_layout(height=480, font=dict(family="IBM Plex Sans"))
                st.plotly_chart(fig, use_container_width=True, key=f"ai_l{idx}")
                return
            if texts and nums:
                bdf = cdf[[texts[0],nums[0]]].dropna().sort_values(nums[0],ascending=False).head(20)
                fig = px.bar(bdf, x=nums[0], y=texts[0], orientation="h", text=nums[0],
                             color_discrete_sequence=[CHART_COLORS["ai_bar"]])
                fig.update_layout(height=max(400,len(bdf)*28), yaxis={"automargin":True},
                                  margin=dict(l=8,r=100,t=30,b=30), font=dict(family="IBM Plex Sans"))
                fig.update_traces(texttemplate="%{text:,.3f}", textposition="outside")
                st.plotly_chart(fig, use_container_width=True, key=f"ai_b{idx}")
                return
            if nums:
                fig = px.histogram(cdf, x=nums[0], color_discrete_sequence=[CHART_COLORS["ai_hist"]])
                fig.update_layout(height=400, font=dict(family="IBM Plex Sans"))
                st.plotly_chart(fig, use_container_width=True, key=f"ai_h{idx}")
        except: pass

    def render_result(parsed, idx=0):
        uncertain = any(p in parsed["text"].lower() for p in ["i don't know","i cannot","not sure","unable to"])
        if uncertain:
            st.warning("⚠️ Agent was uncertain. Check the SQL or rephrase.", icon="⚠️")
        st.markdown(parsed["text"])
        if parsed.get("sql"):
            with st.expander("🔍 View Generated SQL"):
                st.code(parsed["sql"], language="sql")
        if parsed.get("table") is not None and not parsed["table"].empty:
            st.markdown("##### Result Data")
            st.dataframe(parsed["table"], use_container_width=True, hide_index=True)
            ai_chart(parsed["table"], idx)
            csv = parsed["table"].to_csv(index=False).encode("utf-8")
            st.download_button("⬇ Download Result", csv, "AI_RESULT.csv", "text/csv",
                               use_container_width=True, key=f"dl_ai_{idx}")
        if parsed.get("suggestions"):
            st.markdown("##### 💬 Follow-up Questions")
            for sq in parsed["suggestions"][:4]:
                st.caption(f"→ {sq}")

    if "me2j_msgs" not in st.session_state:
        st.session_state.me2j_msgs = []

    for i, msg in enumerate(st.session_state.me2j_msgs):
        with st.chat_message(msg["role"], avatar="🧑" if msg["role"]=="user" else "🤖"):
            if msg["role"]=="assistant": render_result(msg["content"], idx=i)
            else: st.markdown(msg["content"])

    user_q = st.chat_input("Ask about ME2J procurement…  e.g. 'Show plate material price trend month-wise for PVA-2025'")

    if user_q:
        st.session_state.me2j_active_chart = None
        st.session_state.me2j_msgs.append({"role":"user","content":user_q})
        with st.chat_message("user", avatar="🧑"):
            st.markdown(user_q)
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Cortex Agent is analyzing…"):
                try:
                    guarded = guard_check(user_q)
                    parsed  = guarded if guarded else parse_resp(run_agent(user_q))
                    idx = len(st.session_state.me2j_msgs)
                    render_result(parsed, idx=idx)
                    st.session_state.me2j_msgs.append({"role":"assistant","content":parsed})
                except Exception as e:
                    st.warning(f"Could not get a response. Please rephrase.\n\n_{str(e)[:300]}_", icon="⚠️")
