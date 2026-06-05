import json
from datetime import date, datetime
import streamlit as st
import pandas as pd
import plotly.express as px
import snowflake.connector

st.set_page_config(
    page_title="ME2J Procurement Dashboard",
    page_icon="📊",
    layout="wide",
)

# ── Snowflake connection ──────────────────────────────────────────────────────
conn = snowflake.connector.connect(
    user="BGRE_CLIENT",
    password="BGRE@123456789a",
    account="TVSNEXT-TVSNEXT",
    warehouse="BGRE_WH",
    database="SNOWFLAKE_POC",
    schema="ME2J_SCHEMA"
)

BGR_LOGO_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 320" width="100" height="110">
  <rect width="300" height="320" fill="#ffffff"/>
  <circle cx="150" cy="115" r="100" fill="#00308F"/>
  <circle cx="150" cy="115" r="78"  fill="#5B9BD5"/>
  <circle cx="150" cy="115" r="52"  fill="#ffffff"/>
  <circle cx="150" cy="115" r="36"  fill="#D0112B"/>
  <circle cx="150" cy="115" r="16"  fill="#ffffff"/>
  <circle cx="150" cy="115" r="8"   fill="#D0112B"/>
  <text x="150" y="248" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="72" font-weight="900" fill="#00308F" letter-spacing="-1">BGR</text>
  <text x="150" y="292" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-size="26" font-weight="700" fill="#D0112B" letter-spacing="9">ENERGY</text>
</svg>"""

PLOTLY_CONFIG = {"displayModeBar": False, "displaylogo": False, "scrollZoom": False, "doubleClick": False, "responsive": True}

CHART_COLORS = {
    "vendor": "#1565C0", "material": "#2E7D32", "plant": "#E65100",
    "doc_type": "#6A1B9A", "delivery": "#C62828", "trend": "#00838F",
    "matl_group": "#00695C", "ai_bar": "#4527A0", "ai_line": "#00695C", "ai_hist": "#E65100",
}

# ── Global CSS ────────────────────────────────────────────────────────────────
GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif !important; }

/* ── KPI Card ── */
.kpi-card {
    background: #ffffff;
    border: 1px solid #e0e7f0;
    border-radius: 12px;
    padding: 18px 20px 14px;
    min-height: 120px;
    box-shadow: 0 1px 4px rgba(0,56,147,0.07);
    position: relative;
    overflow: hidden;
}
.kpi-card::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #003893, #E31937);
    border-radius: 0 0 12px 12px;
}
.kpi-title {
    font-size: 11px;
    font-weight: 600;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 8px;
}
.kpi-value {
    font-size: 22px;
    font-weight: 700;
    color: #0f172a;
    line-height: 1.3;
    word-break: break-word;
}
.kpi-value-sm {
    font-size: 13px;
    font-weight: 600;
    color: #1e3a5f;
    line-height: 1.7;
    font-family: 'IBM Plex Mono', monospace;
}
.kpi-amount {
    font-size: 17px !important;
    color: #003893 !important;
    font-family: 'IBM Plex Mono', monospace;
}
.kpi-badge {
    display: inline-block;
    background: #EFF6FF;
    color: #1D4ED8;
    font-size: 10px;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 20px;
    margin-top: 4px;
}

/* ── Section Title ── */
.section-title {
    font-size: 16px;
    font-weight: 700;
    color: #003893;
    border-left: 4px solid #E31937;
    padding-left: 10px;
    margin: 20px 0 12px;
    letter-spacing: -0.2px;
}

/* ── Header Banner ── */
.dash-header {
    background: linear-gradient(135deg, #003893 0%, #001f5b 100%);
    border-radius: 14px;
    padding: 20px 28px;
    display: flex;
    align-items: center;
    gap: 18px;
    margin-bottom: 16px;
    box-shadow: 0 4px 16px rgba(0,56,147,0.2);
}
.dash-header-text { flex: 1; }
.dash-header-title { color: #fff; font-size: 22px; font-weight: 700; margin: 0; letter-spacing: -0.3px; }
.dash-header-sub { color: rgba(255,255,255,0.65); font-size: 12px; margin-top: 3px; }
.dash-period { background: #E31937; color: #fff; font-size: 11px; font-weight: 700; padding: 3px 12px; border-radius: 20px; display: inline-block; margin-top: 6px; }
.dash-refresh-info { color: rgba(255,255,255,0.5); font-size: 11px; margin-top: 4px; font-family: 'IBM Plex Mono', monospace; }

/* ── Divider ── */
.styled-divider { height: 1px; background: linear-gradient(90deg, #003893 0%, #E31937 50%, transparent 100%); border: none; margin: 20px 0; }

/* ── Charts/Plotly ── */
.stPlotlyChart *, .js-plotly-plot *, .plot-container *, .svg-container *,
.main-svg *, .cartesianlayer *, .pielayer *, .barlayer *, .scatterlayer *,
.nsewdrag, .drag, .draglayer *, .cursor-crosshair, .cursor-move,
.cursor-pointer, .cursor-ew-resize, .cursor-ns-resize { cursor: default !important; }
.modebar { display: none !important; }

/* ── Buttons ── */
div[data-testid="stButton"] button {
    font-size: 11px !important; font-weight: 600 !important;
    border-radius: 6px !important; padding: 5px 0 !important;
    border: 1px solid #d1daf0 !important;
    background: #f8faff !important; color: #003893 !important;
    transition: all 0.15s !important;
}
div[data-testid="stButton"] button:hover {
    background: #003893 !important; color: #fff !important; border-color: #003893 !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] { background: #f0f4ff !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stDateInput label,
[data-testid="stSidebar"] h3 {
    font-size: 11px !important; font-weight: 700 !important;
    color: #334155 !important; text-transform: uppercase; letter-spacing: 0.06em;
}
.sidebar-refresh-box {
    background: #fff; border: 1px solid #dbeafe; border-radius: 10px;
    padding: 10px 12px; margin-bottom: 12px;
}
.sidebar-refresh-label { font-size: 10px; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; }
.sidebar-refresh-value { font-size: 12px; color: #003893; font-weight: 700; font-family: 'IBM Plex Mono', monospace; margin-top: 2px; }

/* ── Chat / AI tab ── */
.stChatMessage { border-radius: 12px !important; }

/* Chat messages area — scrollable fixed height so input stays visible */
[data-testid="stChatMessageContainer"] {
    max-height: 58vh !important;
    overflow-y: auto !important;
    padding-bottom: 8px !important;
}

/* Chat input — always pinned at bottom, never scrolls away */
[data-testid="stBottom"] {
    position: sticky !important;
    bottom: 0 !important;
    background: white !important;
    z-index: 999 !important;
    padding-top: 8px !important;
    border-top: 2px solid #003893 !important;
}
[data-testid="stChatInput"] textarea {
    border-radius: 24px !important; border: 2px solid #d1daf0 !important;
    font-family: 'IBM Plex Sans', sans-serif !important; font-size: 14px !important;
}
[data-testid="stChatInput"] textarea:focus { border-color: #003893 !important; box-shadow: 0 0 0 3px rgba(0,56,147,0.1) !important; }

/* ── Metric card ── */
div[data-testid="stMetric"] {
    background: #f8faff; border-radius: 10px; padding: 12px;
    border: 1px solid #e0e7f0;
}
</style>
"""

# ── Helpers ───────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_data():
    df = pd.read_sql("SELECT * FROM SNOWFLAKE_POC.ME2J_SCHEMA.ME2J_FINAL_REPORT", conn)
    df._load_time = datetime.now().strftime("%d %b %Y, %I:%M %p")
    return df

def clear_all_caches():
    st.cache_data.clear()

def num_fmt(v):
    try: return f"{float(v):,.0f}"
    except: return "0"

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

def kpi_card(title, main_value, sub_lines=None, badge=None, is_amount=False):
    val_cls = "kpi-amount" if is_amount else "kpi-value"
    sub_html = ""
    if sub_lines:
        sub_html = "<div class='kpi-value-sm'>" + "<br>".join(sub_lines) + "</div>"
    badge_html = f"<div class='kpi-badge'>{badge}</div>" if badge else ""
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">{title}</div>
        <div class="{val_cls}">{main_value}</div>
        {sub_html}
        {badge_html}
    </div>""", unsafe_allow_html=True)

def detail_table(df, rows=25):
    show_cols = ["PurchDoc","Item","PO Date","Material Code","Project",
                 "Vendor/Supplying plant","Vendor Name","Short Text",
                 "Material Description","Order Unit","PO Quantity","GR Qty",
                 "Still to be del.","Crcy","PO Value","Plant","Matl Group",
                 "Release Status","Del Date"]
    available = [c for c in show_cols if c in df.columns]
    tdf = df[available].copy()
    for dcol in ["PO Date", "Del Date"]:
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
            tdf.loc[tdf[c].isin(["","None","nan","NaN"]), c] = "-"
    st.dataframe(tdf.head(rows), use_container_width=True, hide_index=True, height=400)

def mini_summary(df):
    a, b, c, d = st.columns(4)
    pv = "PO Value" if "PO Value" in df.columns else "POH"
    uu = "Order Unit" if "Order Unit" in df.columns else "UOM"
    with a: kpi_card("Records", num_fmt(len(df)))
    with b: kpi_card("Unique POs", num_fmt(df["PurchDoc"].nunique() if "PurchDoc" in df.columns else 0))
    with c:
        if "Crcy" in df.columns and pv in df.columns:
            rows = df.groupby("Crcy",dropna=True)[pv].sum().reset_index(name="V").sort_values("V",ascending=False)
            lines = [f"{r['Crcy']}: {r['V']:,.2f}" for _,r in rows.head(4).iterrows()]
            kpi_card("PO Value by Currency", lines[0] if lines else "0", sub_lines=lines[1:], is_amount=True)
        else:
            kpi_card("PO Value", "0", is_amount=True)
    with d:
        if uu in df.columns and "Still to be del." in df.columns:
            rows = df.groupby(uu,dropna=True)["Still to be del."].sum().clip(lower=0).reset_index(name="Q").sort_values("Q",ascending=False)
            lines = [f"{r[uu]}: {num_fmt(r['Q'])}" for _,r in rows.head(4).iterrows()]
            kpi_card("Pending Qty by UOM", lines[0] if lines else "0", sub_lines=lines[1:])
        else:
            kpi_card("Pending Qty", "0")

def clean_chart(fig, height=500):
    fig.update_layout(
        height=height, dragmode=False, hovermode="closest", clickmode="event",
        margin=dict(l=8, r=90, t=28, b=55),
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
    mini_summary(df)
    pv = "PO Value" if "PO Value" in df.columns else "POH"
    uu = "Order Unit" if "Order Unit" in df.columns else "UOM"

    if "Total POs" in title and "POrg" in df.columns:
        bd = df.groupby("POrg",dropna=True)["PurchDoc"].nunique().reset_index(name="PO Count").sort_values("PO Count",ascending=False)
        st.markdown("#### By Purchase Org"); st.dataframe(bd.head(30), use_container_width=True, hide_index=True)

    if "PO Quantity" in title and uu in df.columns:
        qc = "PO Quantity" if "PO Quantity" in df.columns else None
        if qc:
            s = df.groupby(uu,dropna=True)[qc].sum().reset_index(name="PO Qty").sort_values("PO Qty",ascending=False)
            st.markdown("#### All UOM Breakdown"); st.dataframe(s, use_container_width=True, hide_index=True)

    if "GR Quantity" in title and uu in df.columns and "GR Qty" in df.columns:
        s = df.groupby(uu,dropna=True)["GR Qty"].sum().reset_index(name="GR Qty").sort_values("GR Qty",ascending=False)
        st.markdown("#### GR by UOM"); st.dataframe(s, use_container_width=True, hide_index=True)

    if "Pending Delivery" in title and uu in df.columns and "Still to be del." in df.columns:
        s = df.groupby(uu,dropna=True)["Still to be del."].sum().clip(lower=0).reset_index(name="Pending Qty").sort_values("Pending Qty",ascending=False)
        st.markdown("#### Pending by UOM"); st.dataframe(s, use_container_width=True, hide_index=True)

    if "PO Value" in title and "Crcy" in df.columns:
        s = df.groupby("Crcy",dropna=True)[pv].sum().reset_index(name="PO Value").sort_values("PO Value",ascending=False)
        st.markdown("#### By Currency"); st.dataframe(s, use_container_width=True, hide_index=True)

    if "Project" in title and "Project" in df.columns:
        s = df[df["Project"].astype(str).str.strip().replace("",pd.NA).notna()].groupby("Project",dropna=True)["PurchDoc"].nunique().reset_index(name="PO Count").sort_values("PO Count",ascending=False)
        st.markdown("#### Projects"); st.dataframe(s, use_container_width=True, hide_index=True)

    st.markdown("#### All Records")
    detail_table(df, rows=100)
    csv = df.to_csv(index=False).encode("utf-8")
    safe = title[:15].replace(" ","_")
    st.download_button(f"⬇ Download", csv, f"ME2J_{safe}.csv", "text/csv",
                       use_container_width=True, key=f"dl_pop_{safe}_{len(df)}")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(BGR_LOGO_SVG, unsafe_allow_html=True)
    st.markdown("**ME2J Procurement Dashboard**")
    st.markdown("---")

    # Always show current time — not cached time
    now_ts = datetime.now().strftime("%d %b %Y, %I:%M %p")
    st.markdown(f"""
    <div class="sidebar-refresh-box">
        <div class="sidebar-refresh-label">Last Refreshed</div>
        <div class="sidebar-refresh-value">{now_ts}</div>
    </div>""", unsafe_allow_html=True)

    st.button("🔄 Refresh Data", on_click=clear_all_caches, use_container_width=True)
    st.markdown("---")

# ── Main layout ───────────────────────────────────────────────────────────────
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🔍 Data Explorer", "🤖 AI Assistant"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 – DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:

    df_all = load_data()
    df_all = clean_numeric(df_all, ["PO Value","PO Quantity","GR Qty","Still to be del.","Still to be inv.","Net Price"])

    pv_col  = "PO Value" if "PO Value" in df_all.columns else "POH"
    qty_col = "PO Quantity" if "PO Quantity" in df_all.columns else "PO Quantity Sto"
    uom_col = "Order Unit" if "Order Unit" in df_all.columns else "UOM"
    cur_col = "Crcy" if "Crcy" in df_all.columns else "Currency"
    po_date_col = "PO Date" if "PO Date" in df_all.columns else "Item Doc Date"
    proj_col = "Project" if "Project" in df_all.columns else None

    if "Del Date" in df_all.columns:
        df_all["Del Date"] = pd.to_datetime(df_all["Del Date"], errors="coerce", dayfirst=True)
    if po_date_col in df_all.columns:
        df_all[po_date_col] = pd.to_datetime(df_all[po_date_col], errors="coerce", dayfirst=True)

    # ── Sidebar filters ───────────────────────────────────────────────────────
    st.sidebar.subheader("Filters")

    has_plant  = "Plant" in df_all.columns
    has_vendor = "Vendor Name" in df_all.columns
    has_doc    = "Doc Type" in df_all.columns
    has_matl   = "Matl Group" in df_all.columns
    has_rel    = "Release Status" in df_all.columns
    has_proj   = proj_col is not None
    has_mat_code = "Material Code" in df_all.columns
    div_col    = "POrg" if "POrg" in df_all.columns else None
    has_div    = div_col is not None
    has_date   = po_date_col in df_all.columns

    if has_div:
        div_list = ["All"] + sorted(df_all[div_col].dropna().astype(str).unique().tolist())
        sel_div  = st.sidebar.selectbox("Purchase Org", div_list, key="f_div")
    else: sel_div = "All"

    if has_date:
        mn = df_all[po_date_col].min(); mx = df_all[po_date_col].max()
        default_r = (mn.date() if pd.notna(mn) else date(2026,1,1),
                     mx.date() if pd.notna(mx) else date(2026,3,31))
        dr = st.sidebar.date_input("PO Date Range", value=default_r, key="f_date")
        ds, de = (dr if isinstance(dr,tuple) and len(dr)==2 else (dr,dr))
    else: ds = de = None

    if has_proj:
        pl = ["All"] + sorted(df_all[proj_col].dropna().astype(str).unique().tolist())
        sel_proj = st.sidebar.selectbox("Project", pl, key="f_proj")
    else: sel_proj = "All"

    vl = ["All"] + sorted(df_all["Vendor Name"].dropna().astype(str).unique().tolist()) if has_vendor else ["All"]
    sel_vendor = st.sidebar.selectbox("Vendor", vl, key="f_vendor")

    pl2 = ["All"] + sorted(df_all["Plant"].dropna().astype(str).unique().tolist()) if has_plant else ["All"]
    sel_plant = st.sidebar.selectbox("Plant", pl2, key="f_plant")

    dl = ["All"] + sorted(df_all["Doc Type"].dropna().astype(str).unique().tolist()) if has_doc else ["All"]
    sel_doc = st.sidebar.selectbox("Doc Type", dl, key="f_doc")

    ml = ["All"] + sorted(df_all["Matl Group"].dropna().astype(str).unique().tolist()) if has_matl else ["All"]
    sel_matl = st.sidebar.selectbox("Material Group", ml, key="f_matl")

    if has_mat_code:
        mc_list = ["All"] + sorted(df_all["Material Code"].dropna().astype(str).unique().tolist())
        sel_mc = st.sidebar.selectbox("Material Code", mc_list, key="f_mc")
    else: sel_mc = "All"

    # ── Apply filters ─────────────────────────────────────────────────────────
    fdf = df_all.copy()
    if has_div and sel_div != "All":    fdf = fdf[fdf[div_col].astype(str)==sel_div]
    if has_date and ds and de:
        fdf = fdf[(fdf[po_date_col]>=pd.Timestamp(ds))&(fdf[po_date_col]<=pd.Timestamp(de))]
    if has_proj and sel_proj != "All": fdf = fdf[fdf[proj_col].astype(str)==sel_proj]
    if has_vendor and sel_vendor != "All": fdf = fdf[fdf["Vendor Name"].astype(str)==sel_vendor]
    if has_plant and sel_plant != "All":   fdf = fdf[fdf["Plant"].astype(str)==sel_plant]
    if has_doc and sel_doc != "All":       fdf = fdf[fdf["Doc Type"].astype(str)==sel_doc]
    if has_matl and sel_matl != "All":     fdf = fdf[fdf["Matl Group"].astype(str)==sel_matl]
    if has_mat_code and sel_mc != "All":   fdf = fdf[fdf["Material Code"].astype(str)==sel_mc]

    # ── Header banner ─────────────────────────────────────────────────────────
    load_ts2 = getattr(df_all, "_load_time", datetime.now().strftime("%d %b %Y, %I:%M %p"))
    st.markdown(f"""
    <div class="dash-header">
        {BGR_LOGO_SVG}
        <div class="dash-header-text">
            <div class="dash-header-title">ME2J Procurement Dashboard</div>
            <div class="dash-header-sub">BGR Energy Systems · SAP Purchase Order Analytics</div>
            <span class="dash-period">📅 Jan 2026 – Mar 2026</span>
            <div class="dash-refresh-info">Data as of {load_ts2} &nbsp;·&nbsp; {len(fdf):,} records filtered</div>
        </div>
    </div>""", unsafe_allow_html=True)

    # ── Aggregations ──────────────────────────────────────────────────────────
    qty_uom = (fdf.groupby(uom_col,dropna=True)[qty_col].sum().reset_index(name="Q").sort_values("Q",ascending=False)
               if uom_col in fdf.columns and qty_col in fdf.columns else pd.DataFrame(columns=[uom_col,"Q"]))
    gr_uom  = (fdf.groupby(uom_col,dropna=True)["GR Qty"].sum().reset_index(name="G").sort_values("G",ascending=False)
               if uom_col in fdf.columns and "GR Qty" in fdf.columns else pd.DataFrame(columns=[uom_col,"G"]))
    pend_uom = (fdf.groupby(uom_col,dropna=True)["Still to be del."].sum().clip(lower=0).reset_index(name="P").sort_values("P",ascending=False)
                if uom_col in fdf.columns and "Still to be del." in fdf.columns else pd.DataFrame(columns=[uom_col,"P"]))
    cur_sum  = (fdf.groupby(cur_col,dropna=True)[pv_col].sum().reset_index(name="V").sort_values("V",ascending=False)
                if cur_col in fdf.columns and pv_col in fdf.columns else pd.DataFrame(columns=[cur_col,"V"]))

    rel_df = fdf.copy()
    rel_df["Rel Bucket"] = (rel_df["Release Status"].astype(str).str.strip().str.upper().map(lambda x: "Released" if x=="R" else "Not Released")
                            if has_rel else "N/A")
    rel_sum = rel_df.groupby("Rel Bucket",dropna=False)["PurchDoc"].nunique().reset_index(name="PO Count")

    inr_val = cur_sum.loc[cur_sum[cur_col].astype(str).str.upper()=="INR","V"].sum() if not cur_sum.empty else 0
    usd_val = cur_sum.loc[cur_sum[cur_col].astype(str).str.upper()=="USD","V"].sum() if not cur_sum.empty else 0
    rel_ok  = rel_sum.loc[rel_sum["Rel Bucket"]=="Released","PO Count"].sum()
    rel_no  = rel_sum.loc[rel_sum["Rel Bucket"]=="Not Released","PO Count"].sum()
    proj_ct = fdf[proj_col].astype(str).str.strip().replace("",pd.NA).dropna().nunique() if has_proj else 0
    matl_ct = fdf["Matl Group"].astype(str).str.strip().replace("",pd.NA).dropna().nunique() if has_matl else 0
    vc_col  = "Vendor/Supplying plant" if "Vendor/Supplying plant" in fdf.columns else ("Vendor Name" if has_vendor else None)

    # ── Popup state ───────────────────────────────────────────────────────────
    if "me2j_popup" not in st.session_state:
        st.session_state.me2j_popup = None
        st.session_state.me2j_popup_df = None
    if "me2j_active_chart" not in st.session_state:
        st.session_state.me2j_active_chart = None

    def tpopup(title, df):
        st.session_state.me2j_popup = title
        st.session_state.me2j_popup_df = df

    # ── Section: Executive Summary ────────────────────────────────────────────
    st.markdown('<div class="section-title">Executive Summary</div>', unsafe_allow_html=True)

    # PO breakdown by POrg
    if has_div:
        pob = fdf.groupby(div_col,dropna=True)["PurchDoc"].nunique().reset_index(name="C").sort_values("C",ascending=False)
        pob_lines = [f"{r[div_col]}: {num_fmt(r['C'])}" for _,r in pob.iterrows()]
        total_po_main = num_fmt(fdf["PurchDoc"].nunique())
        total_po_sub  = pob_lines
    else:
        total_po_main = num_fmt(fdf["PurchDoc"].nunique())
        total_po_sub  = None

    # PO Qty — ALL uoms, no truncation
    qty_lines = [f"{r[uom_col]}: {num_fmt(r['Q'])}" for _,r in qty_uom.iterrows()] if not qty_uom.empty else ["0"]
    gr_lines  = [f"{r[uom_col]}: {num_fmt(r['G'])}" for _,r in gr_uom.iterrows()]   if not gr_uom.empty  else ["0"]
    pend_lines= [f"{r[uom_col]}: {num_fmt(r['P'])}" for _,r in pend_uom.iterrows()] if not pend_uom.empty else ["0"]

    # ── ROW 1 ─────────────────────────────────────────────────────────────────
    c1,c2,c3 = st.columns(3)
    with c1:
        kpi_card("Total POs", total_po_main, sub_lines=total_po_sub)
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
            tpopup("PO Quantity by UOM Drilldown", fdf[fdf[qty_col]>0].copy() if qty_col in fdf.columns else fdf.iloc[0:0])

    # ── ROW 2 ─────────────────────────────────────────────────────────────────
    c4,c5,c6 = st.columns(3)
    with c4:
        kpi_card("PO Value by Currency",
                 f"{compact_inr(inr_val)}  ({inr_val:,.0f})",
                 sub_lines=[f"{compact_usd(usd_val)}  ({usd_val:,.0f})"] if usd_val>0 else None,
                 is_amount=True)
        if st.button("View Details", key="b_val", use_container_width=True):
            tpopup("PO Value by Currency Drilldown", fdf[fdf[pv_col]>0].copy() if pv_col in fdf.columns else fdf.iloc[0:0])
    with c5:
        kpi_card("GR Quantity by UOM",
                 gr_lines[0] if gr_lines else "0",
                 sub_lines=gr_lines[1:] if len(gr_lines)>1 else None)
        if st.button("View Details", key="b_gr", use_container_width=True):
            tpopup("GR Quantity by UOM Drilldown", fdf[fdf["GR Qty"]>0].copy() if "GR Qty" in fdf.columns else fdf.iloc[0:0])
    with c6:
        kpi_card("Pending Delivery by UOM",
                 pend_lines[0] if pend_lines else "0",
                 sub_lines=pend_lines[1:] if len(pend_lines)>1 else None)
        if st.button("View Details", key="b_pend", use_container_width=True):
            tpopup("Pending Delivery Quantity by UOM Drilldown", fdf[fdf["Still to be del."]>0].copy() if "Still to be del." in fdf.columns else fdf.iloc[0:0])

    # ── ROW 3 ─────────────────────────────────────────────────────────────────
    c7,c8,c9 = st.columns(3)
    with c7:
        kpi_card("No. of Projects", num_fmt(proj_ct))
        if st.button("View Details", key="b_proj", use_container_width=True):
            pj_df = fdf[fdf[proj_col].astype(str).str.strip().replace("",pd.NA).notna()].copy() if has_proj else fdf.iloc[0:0]
            tpopup("Projects Drilldown", pj_df)
    with c8:
        kpi_card("Material Groups", num_fmt(matl_ct))
        if st.button("View Details", key="b_matl", use_container_width=True):
            tpopup("Material Groups Drilldown", fdf[fdf["Matl Group"].astype(str).str.strip()!=""].copy() if has_matl else fdf.iloc[0:0])
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

    # ── Charts ────────────────────────────────────────────────────────────────
    st.markdown('<hr class="styled-divider">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Procurement Performance Insights</div>', unsafe_allow_html=True)

    chart_popup_title = None
    chart_popup_df    = None
    active_chart      = st.session_state.get("me2j_active_chart")

    r1c1, r1c2 = st.columns(2)
    with r1c1:
        st.markdown("### PO Count by Plant")
        pc = (fdf.groupby("Plant",dropna=True)["PurchDoc"].nunique().reset_index(name="PO Count").sort_values("PO Count",ascending=False).head(20)
              if has_plant else pd.DataFrame(columns=["Plant","PO Count"]))
        fig = px.bar(pc, x="Plant", y="PO Count", text="PO Count", color_discrete_sequence=[CHART_COLORS["plant"]])
        fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        fig.update_layout(xaxis_tickangle=-35)
        ev = chart_event(clean_chart(fig,520), "ch_plant")
        if active_chart=="ch_plant":
            s = get_val(ev,"x")
            if s and has_plant: chart_popup_title=f"Plant: {s}"; chart_popup_df=fdf[fdf["Plant"].astype(str)==str(s)]

    with r1c2:
        st.markdown("### Top Vendors by PO Value")
        vc = (fdf.groupby("Vendor Name",dropna=True).agg(PO_Count=("PurchDoc","nunique"),PO_Value=(pv_col,"sum")).reset_index().sort_values("PO_Value",ascending=False).head(15)
              if has_vendor else pd.DataFrame(columns=["Vendor Name","PO_Count","PO_Value"]))
        fig = px.bar(vc, x="PO_Value", y="Vendor Name", orientation="h", text="PO_Value", custom_data=["PO_Count"],
                     color_discrete_sequence=[CHART_COLORS["vendor"]])
        fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside",
                          hovertemplate="<b>%{y}</b><br>PO Value: %{x:,.2f}<br>POs: %{customdata[0]}<extra></extra>")
        fig.update_layout(yaxis={"automargin":True})
        ev = chart_event(clean_chart(fig,520), "ch_vendor")
        if active_chart=="ch_vendor":
            s = get_val(ev,"y")
            if s and has_vendor: chart_popup_title=f"Vendor: {s}"; chart_popup_df=fdf[fdf["Vendor Name"].astype(str)==str(s)]

    r2c1, r2c2 = st.columns(2)
    with r2c1:
        st.markdown("### PO Quantity by UOM")
        fig = px.bar(qty_uom.rename(columns={uom_col:"UOM","Q":"Total Qty"}),
                     x="UOM", y="Total Qty", text="Total Qty", color_discrete_sequence=[CHART_COLORS["material"]])
        fig.update_traces(texttemplate="%{text:,.2f}", textposition="outside")
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

    r3c1, r3c2 = st.columns(2)
    with r3c1:
        st.markdown("### GR Quantity by UOM")
        fig = px.bar(gr_uom.rename(columns={uom_col:"UOM","G":"GR Qty"}),
                     x="UOM", y="GR Qty", text="GR Qty", color_discrete_sequence=[CHART_COLORS["trend"]])
        fig.update_traces(texttemplate="%{text:,.2f}", textposition="outside")
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

    r4c1, r4c2 = st.columns(2)
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
            if s and has_proj: chart_popup_title=f"Project: {s}"; chart_popup_df=fdf[fdf[proj_col].astype(str)==str(s)]

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
# TAB 2 – DATA EXPLORER
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Filter & Explore Data")
    df2 = load_data()
    hv2 = "Vendor Name" in df2.columns
    hp2 = "Plant" in df2.columns
    hd2 = "Doc Type" in df2.columns
    hm2 = "Matl Group" in df2.columns

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
    if hv2 and sv2!="All": f2 = f2[f2["Vendor Name"]==sv2]
    if hp2 and sp2!="All": f2 = f2[f2["Plant"]==sp2]
    if hd2 and sd2!="All": f2 = f2[f2["Doc Type"]==sd2]
    if hm2 and sm2!="All": f2 = f2[f2["Matl Group"]==sm2]

    st.caption(f"Showing {len(f2):,} of {len(df2):,} records")
    st.dataframe(f2, use_container_width=True, height=500, hide_index=True)
    csv2 = f2.to_csv(index=False).encode("utf-8")
    st.download_button("⬇ Download CSV", csv2, "ME2J_EXPLORER.csv", "text/csv", key="dl_exp")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 – AI ASSISTANT
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    AGENT_FQN = "SNOWFLAKE_POC.ME2J_SCHEMA.BGRE_ME2J_PROCUREMENT_AGENT"

    # Reset chart state when AI tab is active
    st.session_state.me2j_active_chart = None

    # ── Page layout ───────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#003893,#001f5b);border-radius:12px;padding:16px 22px;margin-bottom:16px;display:flex;align-items:center;gap:14px;">
        {BGR_LOGO_SVG}
        <div>
            <div style="color:#fff;font-size:18px;font-weight:700;">ME2J Procurement AI Assistant</div>
            <div style="color:rgba(255,255,255,0.6);font-size:12px;margin-top:2px;">Powered by Snowflake Cortex Analyst · ME2J_PURCHASE_ORDER_REPORT</div>
            <div style="color:rgba(255,255,255,0.5);font-size:11px;margin-top:3px;">Ask any question about purchase orders, vendors, materials, projects, or delivery status</div>
        </div>
    </div>""", unsafe_allow_html=True)

    # ── Agent rules ───────────────────────────────────────────────────────────
    STRICT_RULES = """You are answering questions for the BGRE ME2J procurement dashboard.

Use ONLY SNOWFLAKE_POC.ME2J_SCHEMA.ME2J_FINAL_REPORT.
Available columns: Vald Element, PurchDoc, Item, PO Date, Vendor/Supplying plant, Vendor Name,
Short Text, Material Code, Material Description, PO Quantity, Order Unit, GR Qty,
Still to be del., Crcy, Plant, PO Value, To be inv., Still to be inv., Net Price, Per,
Matl Group, POrg, PGr, Doc Type, Del Date, Del Date Raw, Profit Center, Release Status, Project.

RULES — always follow:
1. PO count = COUNT(DISTINCT "PurchDoc").
2. Procurement value / PO value / spend / order value = SUM("PO Value"). Never use Net Price for totals.
3. Net Price = per-unit price only.
4. Always show Crcy with monetary values.
5. Always show Order Unit with quantity values.
6. Month-wise: use TRY_TO_DATE("PO Date",'DD-MM-YYYY').
7. Pending delivery = GREATEST("Still to be del.", 0).
8. Overdue = TRY_TO_DATE("Del Date",'DD-MM-YYYY') < CURRENT_DATE() AND "Still to be del." > 0.
9. Project-wise = use "Project" column.
10. Known totals: Total PO Value INR = 450,380,671.69 | Total POs = 536 | Rows = 1453.

MISSING FIELD RULE:
If asked about Project Manager, Approver, Payment Terms, GST Number, Invoice Number,
Invoice Date, Transporter, LR Number, GRN Number, Department — clearly state these
fields are NOT available in ME2J_FINAL_REPORT. Do not substitute with other columns.

OFF-TOPIC RULE:
If the question is not related to procurement data in this table, say:
"This question is outside the scope of ME2J procurement data. Please ask about purchase orders, vendors, materials, projects, or delivery status."
"""

    GUARD_MAP = {
        "project manager":"Project Manager","project head":"Project Head",
        "manager wise":"Project Manager","pm wise":"Project Manager",
        "approver":"Approver Name","approved by":"Approved By",
        "approval person":"Approver Name","payment term":"Payment Terms",
        "gst":"GST Number","invoice number":"Invoice Number",
        "invoice no":"Invoice Number","invoice date":"Invoice Date",
        "transporter":"Transporter","lr number":"LR Number",
        "grn number":"GRN Number","department":"Department",
    }

    def guard_check(q):
        ql = q.lower()
        for k,v in GUARD_MAP.items():
            if k in ql:
                return {"text":f"**{v}** is not available in the ME2J_FINAL_REPORT dataset.\n\nThis field does not exist in the current data. Please request the data team to add the required mapping if this breakdown is needed.",
                        "sql":None,"table":None,
                        "suggestions":["Show project-wise PO value","Show vendor-wise PO value","Which vendor has highest pending delivery?"]}
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
                cols = st.columns(min(len(nums),4))
                for i,c in enumerate(nums[:4]):
                    with cols[i]: st.metric(c.replace("_"," ").title(), f"{cdf[c].iloc[0]:,.2f}")
                return
            if dates and nums:
                fig = px.line(cdf[[dates[0],nums[0]]].dropna().sort_values(dates[0]),
                              x=dates[0],y=nums[0],markers=True,text=nums[0],
                              color_discrete_sequence=[CHART_COLORS["ai_line"]])
                fig.update_traces(texttemplate="%{text:,.2f}",textposition="top center")
                fig.update_layout(height=480,font=dict(family="IBM Plex Sans"))
                st.plotly_chart(fig,use_container_width=True,key=f"ai_l{idx}")
                return
            if texts and nums:
                bdf = cdf[[texts[0],nums[0]]].dropna().sort_values(nums[0],ascending=False).head(20)
                fig = px.bar(bdf,x=nums[0],y=texts[0],orientation="h",text=nums[0],
                             color_discrete_sequence=[CHART_COLORS["ai_bar"]])
                fig.update_layout(height=max(400,len(bdf)*28),yaxis={"automargin":True},
                                  margin=dict(l=8,r=100,t=30,b=30),font=dict(family="IBM Plex Sans"))
                fig.update_traces(texttemplate="%{text:,.2f}",textposition="outside")
                st.plotly_chart(fig,use_container_width=True,key=f"ai_b{idx}")
                return
            if nums:
                fig = px.histogram(cdf,x=nums[0],color_discrete_sequence=[CHART_COLORS["ai_hist"]])
                fig.update_layout(height=400,font=dict(family="IBM Plex Sans"))
                st.plotly_chart(fig,use_container_width=True,key=f"ai_h{idx}")
        except: pass

    def render_result(parsed, idx=0):
        answer = parsed["text"]
        # Warn if uncertain
        uncertain = any(p in answer.lower() for p in ["i don't know","i cannot","not sure","unable to"])
        if uncertain:
            st.warning("⚠️ The agent was uncertain. Check the SQL or rephrase.", icon="⚠️")
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

    # ── Chat history ──────────────────────────────────────────────────────────
    if "me2j_msgs" not in st.session_state:
        st.session_state.me2j_msgs = []

    # Render previous messages
    for i, msg in enumerate(st.session_state.me2j_msgs):
        with st.chat_message(msg["role"], avatar="🧑" if msg["role"]=="user" else "🤖"):
            if msg["role"]=="assistant": render_result(msg["content"], idx=i)
            else: st.markdown(msg["content"])

    # ── Chat input — always at bottom ─────────────────────────────────────────
    user_q = st.chat_input("Ask about ME2J procurement data…  e.g. 'Show cement procurement month-wise'")

    if user_q:
        st.session_state.me2j_active_chart = None
        st.session_state.me2j_msgs.append({"role":"user","content":user_q})
        with st.chat_message("user", avatar="🧑"):
            st.markdown(user_q)
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Cortex Agent is analyzing…"):
                try:
                    guarded = guard_check(user_q)
                    if guarded:
                        parsed = guarded
                    else:
                        raw = run_agent(user_q)
                        parsed = parse_resp(raw)
                    idx = len(st.session_state.me2j_msgs)
                    render_result(parsed, idx=idx)
                    st.session_state.me2j_msgs.append({"role":"assistant","content":parsed})
                except Exception as e:
                    st.warning(f"Could not get a response. Please rephrase.\n\n_{str(e)[:300]}_", icon="⚠️")
