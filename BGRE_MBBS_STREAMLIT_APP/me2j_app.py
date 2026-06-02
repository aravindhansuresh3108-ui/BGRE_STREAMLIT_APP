import json
from datetime import date
import streamlit as st
import pandas as pd
import plotly.express as px
import snowflake.connector

st.set_page_config(
    page_title="ME2J Procurement Dashboard",
    page_icon="📊",
    layout="wide",
)

conn = snowflake.connector.connect(
    user="BGRE_CLIENT",
    password="BGRE@123456789a",
    account="TVSNEXT-TVSNEXT",
    warehouse="BGRE_WH",
    database="SNOWFLAKE_POC",
    schema="ME2J_SCHEMA"
)

BGR_LOGO_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 200" width="120" height="150">
  <circle cx="80" cy="52" r="38" fill="#003893"/>
  <circle cx="80" cy="52" r="26" fill="#ffffff"/>
  <circle cx="80" cy="52" r="11" fill="#E31937"/>
  <rect x="77" y="8" width="6" height="18" rx="3" fill="#E31937"/>
  <text x="80" y="130" text-anchor="middle" font-family="Arial Black, Impact, sans-serif" font-size="52" font-weight="900" fill="#003893">BGR</text>
  <text x="80" y="165" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="30" font-weight="700" fill="#E31937" letter-spacing="6">ENERGY</text>
</svg>"""

PLOTLY_CONFIG = {
    "displayModeBar": False,
    "displaylogo": False,
    "scrollZoom": False,
    "doubleClick": False,
    "responsive": True,
}

# ------------------------------------------------------------
# Chart colors - visual enhancement only
# ------------------------------------------------------------
CHART_COLORS = {
    "vendor": "#1E88E5",          # Blue
    "material": "#43A047",        # Green
    "plant": "#FB8C00",           # Orange
    "doc_type": "#8E24AA",        # Purple
    "delivery": "#E53935",        # Red
    "trend": "#00ACC1",           # Cyan
    "pending_vendor": "#6D4C41",  # Brown
    "pending_material": "#FDD835",# Gold
    "company": "#3949AB",         # Indigo
    "matl_group": "#00897B",      # Teal
    "vendor_count": "#D81B60",    # Pink
    "qty_compare": ["#1E88E5", "#43A047"],
    "ai_bar": "#5E35B1",
    "ai_line": "#00897B",
    "ai_hist": "#FB8C00",
}

@st.cache_data(ttl=300)
def load_data():
    return pd.read_sql("SELECT * FROM SNOWFLAKE_POC.ME2J_SCHEMA.ME2J_FINAL_REPORT", conn)

def clear_all_caches():
    st.cache_data.clear()

def money_fmt(v):
    try:
        return f"INR {float(v):,.2f}"
    except Exception:
        return "INR 0.00"

def num_fmt(v):
    try:
        return f"{float(v):,.0f}"
    except Exception:
        return "0"

def format_inr_compact(v):
    """Format INR in Cr/Lakh where suitable (UI only, not affecting calculations)."""
    try:
        v = float(v) if v is not None else 0.0
    except Exception:
        v = 0.0
    if v >= 1e7:
        return f"INR {v / 1e7:,.2f} Cr"
    if v >= 1e5:
        return f"INR {v / 1e5:,.2f} Lakh"
    return f"INR {v:,.2f}"

def format_usd_compact(v):
    """Format USD in Cr/Lakh where suitable (UI only, not affecting calculations)."""
    try:
        v = float(v) if v is not None else 0.0
    except Exception:
        v = 0.0
    if v >= 1e7:
        return f"USD {v / 1e7:,.2f} Cr"
    if v >= 1e5:
        return f"USD {v / 1e5:,.2f} Lakh"
    return f"USD {v:,.2f}"

def clean_numeric(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df

def kpi(title, value, is_amount=False):
    value_class = "kpi-value amount-value" if is_amount else "kpi-value"
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">{title}</div>
            <div class="{value_class}">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def mini_summary(df, title):
    st.markdown(f"#### {title}")
    a, b, c, d = st.columns(4)
    po_value_col = "PO Value" if "PO Value" in df.columns else "POH"
    with a:
        kpi("Records", num_fmt(len(df)))
    with b:
        kpi("PO Count", num_fmt(df["PurchDoc"].nunique() if "PurchDoc" in df.columns else 0))
    with c:
        if "Crcy" in df.columns and po_value_col in df.columns:
            value_by_currency = (
                df.groupby("Crcy", dropna=True)[po_value_col]
                .sum()
                .reset_index(name="Total Value")
                .sort_values("Total Value", ascending=False)
            )
            currency_text = "<br>".join(
                [f"{str(r['Crcy'])}: {float(r['Total Value']):,.2f}" for _, r in value_by_currency.head(4).iterrows()]
            ) if not value_by_currency.empty else "0"
            kpi("PO Value by Currency", currency_text, is_amount=True)
        else:
            kpi("PO Value", money_fmt(df[po_value_col].sum() if po_value_col in df.columns else 0), is_amount=True)
    with d:
        if "Order Unit" in df.columns and "Still to be del." in df.columns:
            pending_by_uom = (
                df.groupby("Order Unit", dropna=True)["Still to be del."]
                .sum()
                .clip(lower=0)
                .reset_index(name="Pending Qty")
                .sort_values("Pending Qty", ascending=False)
            )
            pending_text = "<br>".join(
                [f"{str(r['Order Unit'])}: {num_fmt(r['Pending Qty'])}" for _, r in pending_by_uom.head(4).iterrows()]
            ) if not pending_by_uom.empty else "0"
            kpi("Pending Qty by UOM", pending_text)
        else:
            pending = df["Still to be del."].clip(lower=0).sum() if "Still to be del." in df.columns else 0
            kpi("Pending Qty", num_fmt(pending))

def detail_table(df, rows=20):
    show_cols = [
        "PurchDoc",
        "Item",
        "PO Date",
        "Material Code",
        "Project",
        "Vendor/Supplying plant",
        "Vendor Name",
        "Short Text",
        "Material Description",
        "Order Unit",
        "PO Quantity",
        "GR Qty",
        "Still to be del.",
        "Crcy",
        "PO Value",
        "Plant",
        "Matl Group",
        "Release Status",
        "Del Date",
    ]
    available = [c for c in show_cols if c in df.columns]
    table_df = df[available].copy()
    for dcol in ["PO Date", "Del Date"]:
        if dcol in table_df.columns:
            raw_dates = table_df[dcol].copy()
            if dcol == "PO Date" and "Item Doc Date" in df.columns:
                raw_dates = raw_dates.fillna(df.loc[table_df.index, "Item Doc Date"])
            if dcol == "Del Date" and "Del Date Raw" in df.columns:
                raw_dates = raw_dates.fillna(df.loc[table_df.index, "Del Date Raw"])
            parsed_dayfirst = pd.to_datetime(raw_dates, errors="coerce", dayfirst=True)
            parsed_default = pd.to_datetime(raw_dates, errors="coerce")
            parsed_dates = parsed_dayfirst.fillna(parsed_default)
            formatted_dates = parsed_dates.dt.strftime("%d-%m-%Y")
            table_df[dcol] = formatted_dates.where(parsed_dates.notna(), raw_dates.astype(str))
            table_df[dcol] = table_df[dcol].replace({"NaT": "-", "None": "-", "nan": "-", "NaN": "-"}).fillna("-")
    for mcol in ["Material Code", "Material Description"]:
        if mcol in table_df.columns:
            table_df[mcol] = table_df[mcol].fillna("-").astype(str).str.strip()
            table_df.loc[table_df[mcol].isin(["", "None", "nan", "NaN"]), mcol] = "-"
    for pcol in ["Project"]:
        if pcol in table_df.columns:
            table_df[pcol] = table_df[pcol].fillna("-").astype(str).str.strip()
            table_df.loc[table_df[pcol].isin(["", "None", "nan", "NaN"]), pcol] = "-"
    st.dataframe(table_df.head(rows), use_container_width=True, hide_index=True, height=420)

def clean_chart(fig, height=520):
    fig.update_layout(
        height=height,
        dragmode=False,
        hovermode="closest",
        clickmode="event",
        margin=dict(l=10, r=80, t=25, b=60),
        font=dict(size=11),
    )
    # selected/unselected is not supported by pie traces; apply only where compatible
    for trace in fig.data:
        if getattr(trace, "type", None) != "pie":
            trace.update(
                selected=dict(marker=dict(opacity=1)),
                unselected=dict(marker=dict(opacity=0.95)),
            )
    return fig

def mark_active_chart(chart_key):
    st.session_state.me2j_active_chart = chart_key

def chart_event(fig, key):
    # Callback marks only the chart that was clicked, so old selections from other charts
    # will not keep opening the previous drilldown.
    return st.plotly_chart(
        fig,
        use_container_width=True,
        key=key,
        on_select=lambda chart_key=key: mark_active_chart(chart_key),
        config=PLOTLY_CONFIG,
    )

def pie_chart_event(fig, key):
    # Pie/donut charts need explicit point selection in some Streamlit/Plotly versions.
    return st.plotly_chart(
        fig,
        use_container_width=True,
        key=key,
        on_select=lambda chart_key=key: mark_active_chart(chart_key),
        selection_mode="points",
        config=PLOTLY_CONFIG,
    )

@st.dialog("Drilldown Details", width="large")
def show_popup(title, df):
    st.markdown(f"### {title}")
    mini_summary(df, title)
    if title == "Total POs Drilldown":
        # Division-wise / Purchase Organization-wise breakdown for distinct PO counts.
        div_col = "Division" if "Division" in df.columns else None
        po_org_col = "POrg" if "POrg" in df.columns else None
        if div_col or po_org_col:
            if div_col and po_org_col and div_col != po_org_col:
                colA, colB = st.columns(2)
                with colA:
                    breakdown_div = (
                        df.groupby(div_col, dropna=True)["PurchDoc"]
                        .nunique()
                        .reset_index(name="PO Count")
                        .sort_values("PO Count", ascending=False)
                    )
                    st.markdown("#### PO Count Breakdown (Division)")
                    st.dataframe(breakdown_div.head(25), use_container_width=True, hide_index=True)
                with colB:
                    breakdown_porg = (
                        df.groupby(po_org_col, dropna=True)["PurchDoc"]
                        .nunique()
                        .reset_index(name="PO Count")
                        .sort_values("PO Count", ascending=False)
                    )
                    st.markdown("#### PO Count Breakdown (Purchase Organization)")
                    st.dataframe(breakdown_porg.head(25), use_container_width=True, hide_index=True)
            elif div_col:
                breakdown = (
                    df.groupby(div_col, dropna=True)["PurchDoc"]
                    .nunique()
                    .reset_index(name="PO Count")
                    .sort_values("PO Count", ascending=False)
                )
                st.markdown("#### PO Count Breakdown (Division)")
                st.dataframe(breakdown.head(25), use_container_width=True, hide_index=True)
            elif po_org_col:
                breakdown = (
                    df.groupby(po_org_col, dropna=True)["PurchDoc"]
                    .nunique()
                    .reset_index(name="PO Count")
                    .sort_values("PO Count", ascending=False)
                )
                st.markdown("#### PO Count Breakdown (Purchase Organization)")
                st.dataframe(breakdown.head(25), use_container_width=True, hide_index=True)
    if title == "PO Quantity by UOM Drilldown" and "Order Unit" in df.columns:
        qty_col = "PO Quantity" if "PO Quantity" in df.columns else ("PO Quantity Sto" if "PO Quantity Sto" in df.columns else None)
        if qty_col:
            summary = (
                df.groupby("Order Unit", dropna=True)[qty_col]
                .sum()
                .reset_index(name="PO Quantity")
                .sort_values("PO Quantity", ascending=False)
            )
            st.markdown("#### All UOM Summary")
            st.dataframe(summary, use_container_width=True, hide_index=True)

    if title == "GR Quantity by UOM Drilldown" and "Order Unit" in df.columns and "GR Qty" in df.columns:
        summary = (
            df.groupby("Order Unit", dropna=True)["GR Qty"]
            .sum()
            .reset_index(name="GR Quantity")
            .sort_values("GR Quantity", ascending=False)
        )
        st.markdown("#### All UOM Summary")
        st.dataframe(summary, use_container_width=True, hide_index=True)

    if title == "Pending Delivery Quantity by UOM Drilldown" and "Order Unit" in df.columns and "Still to be del." in df.columns:
        summary = (
            df.groupby("Order Unit", dropna=True)["Still to be del."]
            .sum()
            .clip(lower=0)
            .reset_index(name="Pending Delivery Quantity")
            .sort_values("Pending Delivery Quantity", ascending=False)
        )
        st.markdown("#### All UOM Summary")
        st.dataframe(summary, use_container_width=True, hide_index=True)

    if title == "PO Value by Currency Drilldown" and "Crcy" in df.columns:
        value_col = "PO Value" if "PO Value" in df.columns else ("POH" if "POH" in df.columns else None)
        if value_col:
            summary = (
                df.groupby("Crcy", dropna=True)[value_col]
                .sum()
                .reset_index(name="PO Value")
                .sort_values("PO Value", ascending=False)
            )
            st.markdown("#### Currency Summary")
            st.dataframe(summary, use_container_width=True, hide_index=True)

    st.markdown("#### Detailed Records")
    detail_table(df, rows=50)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download Drilldown Data",
        csv,
        "ME2J_DRILLDOWN_DATA.csv",
        "text/csv",
        use_container_width=True
    )

def get_clicked_value(event, field):
    try:
        if event and event.selection.points:
            pt = event.selection.points[0]
            if field in pt and pt.get(field) is not None:
                return pt.get(field)
            # Pie charts sometimes expose the clicked slice under different keys.
            for alt in ["label", "theta", "legendgroup", "customdata", "point_name", "name"]:
                if alt in pt and pt.get(alt) is not None:
                    val = pt.get(alt)
                    if isinstance(val, (list, tuple)) and val:
                        return val[0]
                    return val
    except Exception:
        return None
    return None

with st.sidebar:
    st.markdown(BGR_LOGO_SVG, unsafe_allow_html=True)
    st.caption("ME2J Procurement Dashboard")
    st.button("🔄 Refresh data", on_click=clear_all_caches, use_container_width=True)

st.markdown(BGR_LOGO_SVG, unsafe_allow_html=True)
st.title("ME2J Procurement Dashboard")

tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🔍 Data Explorer", "🤖 AI Assistant"])

with tab1:
    st.markdown("""
    <style>
    .kpi-card {
        background: white;
        padding: 22px;
        border-radius: 18px;
        border: 1px solid #E5E7EB;
        box-shadow: 0 3px 12px rgba(0,0,0,0.08);
        min-height: 135px;
        width: 100%;
    }
    .kpi-title {
        font-size: 14px;
        color: #6B7280;
        margin-bottom: 10px;
        font-weight: 600;
    }
    .kpi-value {
        font-size: 25px;
        font-weight: 800;
        color: #111827;
        line-height: 1.25;
        white-space: normal;
        word-break: break-word;
    }
    .amount-value {
        font-size: 20px !important;
    }
    .section-title {
        font-size: 22px;
        font-weight: 800;
        margin-top: 20px;
        margin-bottom: 12px;
        color: #111827;
    }
    .stPlotlyChart,
    .stPlotlyChart *,
    .js-plotly-plot,
    .js-plotly-plot *,
    .plot-container,
    .plot-container *,
    .svg-container,
    .svg-container *,
    .main-svg,
    .main-svg *,
    .cartesianlayer,
    .cartesianlayer *,
    .pielayer,
    .pielayer *,
    .slice,
    .barlayer,
    .barlayer *,
    .scatterlayer,
    .scatterlayer *,
    .nsewdrag,
    .drag,
    .draglayer,
    .draglayer *,
    .zoomlayer,
    .cursor-crosshair,
    .cursor-move,
    .cursor-pointer,
    .cursor-ew-resize,
    .cursor-ns-resize {
        cursor: default !important;
    }
    .modebar {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">Executive Summary</div>', unsafe_allow_html=True)
    st.caption("Dashboard Period: Jan 2026 - Mar 2026")

    df_all = load_data()
    df_all = clean_numeric(df_all, ["POH", "PO Value", "PO Quantity Sto", "PO Quantity", "GR Qty", "Still to be del.", "Still to be inv."])

    po_value_col = "PO Value" if "PO Value" in df_all.columns else "POH"
    po_qty_col = "PO Quantity" if "PO Quantity" in df_all.columns else "PO Quantity Sto"
    uom_col = "Order Unit" if "Order Unit" in df_all.columns else "UOM"
    currency_col = "Crcy" if "Crcy" in df_all.columns else "Currency"
    po_date_col = "PO Date" if "PO Date" in df_all.columns else "Item Doc Date"
    # Project KPI/count must be based on the "Project" column only (no WBS/Vald Element fallbacks).
    project_col = "Project" if "Project" in df_all.columns else None

    if "Del Date" in df_all.columns:
        df_all["Del Date"] = pd.to_datetime(df_all["Del Date"], errors="coerce", dayfirst=True)
    if po_date_col in df_all.columns:
        df_all[po_date_col] = pd.to_datetime(df_all[po_date_col], errors="coerce", dayfirst=True)

    st.sidebar.subheader("Dashboard Filters")

    has_vendor_name = "Vendor Name" in df_all.columns
    has_plant = "Plant" in df_all.columns
    has_doc_type = "Doc Type" in df_all.columns
    has_matl_group = "Matl Group" in df_all.columns
    has_del_date = "Del Date" in df_all.columns
    has_release_status = "Release Status" in df_all.columns
    has_project = project_col is not None

    division_filter_col = "Division" if "Division" in df_all.columns else ("POrg" if "POrg" in df_all.columns else None)
    has_division_filter = division_filter_col is not None

    material_filter_col = "Material" if "Material" in df_all.columns else ("Material Code" if "Material Code" in df_all.columns else None)
    has_material_filter = material_filter_col is not None

    has_po_date_filter = po_date_col in df_all.columns

    vendor_list = ["All"] + sorted(df_all["Vendor Name"].dropna().astype(str).unique().tolist()) if has_vendor_name else ["All"]
    plant_list = ["All"] + sorted(df_all["Plant"].dropna().astype(str).unique().tolist()) if has_plant else ["All"]
    doc_type_list = ["All"] + sorted(df_all["Doc Type"].dropna().astype(str).unique().tolist()) if has_doc_type else ["All"]
    matl_group_list = ["All"] + sorted(df_all["Matl Group"].dropna().astype(str).unique().tolist()) if has_matl_group else ["All"]

    if has_division_filter:
        division_list = ["All"] + sorted(df_all[division_filter_col].dropna().astype(str).unique().tolist())
        selected_division = st.sidebar.selectbox("Division / Purchase Organization", division_list, key="dash_div_porg")
    else:
        selected_division = "All"

    if has_po_date_filter:
        po_min = df_all[po_date_col].min()
        po_max = df_all[po_date_col].max()
        if pd.notna(po_min) and pd.notna(po_max):
            default_range = (po_min.date(), po_max.date())
        else:
            default_range = (date(2026, 1, 1), date(2026, 3, 31))
        po_date_range = st.sidebar.date_input("PO Date", value=default_range, key="dash_po_date")
        if isinstance(po_date_range, tuple) and len(po_date_range) == 2:
            po_date_start, po_date_end = po_date_range
        else:
            po_date_start = po_date_end = po_date_range
    else:
        po_date_start = po_date_end = None

    if has_material_filter:
        material_list = ["All"] + sorted(df_all[material_filter_col].dropna().astype(str).unique().tolist())
        selected_material = st.sidebar.selectbox("Material", material_list, key="dash_material")
    else:
        selected_material = "All"

    if has_project:
        project_list = ["All"] + sorted(df_all[project_col].dropna().astype(str).unique().tolist())
        selected_project = st.sidebar.selectbox("Project", project_list, key="dash_project")
    else:
        selected_project = "All"

    selected_vendor = st.sidebar.selectbox("Vendor", vendor_list, key="dash_vendor")
    selected_plant = st.sidebar.selectbox("Plant", plant_list, key="dash_plant")
    selected_doc_type = st.sidebar.selectbox("Doc Type", doc_type_list, key="dash_doc_type")
    selected_matl_group = st.sidebar.selectbox("Material Group", matl_group_list, key="dash_matl_group")

    filtered_df = df_all.copy()
    if has_division_filter and selected_division != "All":
        filtered_df = filtered_df[filtered_df[division_filter_col].astype(str) == selected_division]
    if has_po_date_filter and po_date_start is not None and po_date_end is not None:
        filtered_df = filtered_df[
            (filtered_df[po_date_col] >= pd.Timestamp(po_date_start))
            & (filtered_df[po_date_col] <= pd.Timestamp(po_date_end))
        ]
    if has_material_filter and selected_material != "All":
        filtered_df = filtered_df[filtered_df[material_filter_col].astype(str) == selected_material]
    if has_project and selected_project != "All":
        filtered_df = filtered_df[filtered_df[project_col].astype(str) == selected_project]
    if has_vendor_name and selected_vendor != "All":
        filtered_df = filtered_df[filtered_df["Vendor Name"].astype(str) == selected_vendor]
    if has_plant and selected_plant != "All":
        filtered_df = filtered_df[filtered_df["Plant"].astype(str) == selected_plant]
    if has_doc_type and selected_doc_type != "All":
        filtered_df = filtered_df[filtered_df["Doc Type"].astype(str) == selected_doc_type]
    if has_matl_group and selected_matl_group != "All":
        filtered_df = filtered_df[filtered_df["Matl Group"].astype(str) == selected_matl_group]

    overdue_df = filtered_df[
        (filtered_df["Del Date"].notna())
        & (filtered_df["Del Date"].dt.date < date.today())
        & (filtered_df["Still to be del."] > 0)
    ] if has_del_date else filtered_df.iloc[0:0]

    quantity_uom = (
        filtered_df.groupby(uom_col, dropna=True)[po_qty_col]
        .sum()
        .reset_index(name="Total Quantity")
        .sort_values("Total Quantity", ascending=False)
    ) if uom_col in filtered_df.columns and po_qty_col in filtered_df.columns else pd.DataFrame(columns=[uom_col, "Total Quantity"])

    gr_uom = (
        filtered_df.groupby(uom_col, dropna=True)["GR Qty"]
        .sum()
        .reset_index(name="GR Quantity")
        .sort_values("GR Quantity", ascending=False)
    ) if uom_col in filtered_df.columns and "GR Qty" in filtered_df.columns else pd.DataFrame(columns=[uom_col, "GR Quantity"])

    pending_uom = (
        filtered_df.groupby(uom_col, dropna=True)["Still to be del."]
        .sum()
        .reset_index(name="Pending Delivery Quantity")
    ) if uom_col in filtered_df.columns and "Still to be del." in filtered_df.columns else pd.DataFrame(columns=[uom_col, "Pending Delivery Quantity"])
    if not pending_uom.empty:
        pending_uom["Pending Delivery Quantity"] = pending_uom["Pending Delivery Quantity"].clip(lower=0)
        pending_uom = pending_uom.sort_values("Pending Delivery Quantity", ascending=False)

    currency_summary = (
        filtered_df.groupby(currency_col, dropna=True)[po_value_col]
        .sum()
        .reset_index(name="Total Value")
        .sort_values("Total Value", ascending=False)
    ) if currency_col in filtered_df.columns and po_value_col in filtered_df.columns else pd.DataFrame(columns=[currency_col, "Total Value"])

    release_df = filtered_df.copy()
    if has_release_status:
        release_df["Release Bucket"] = release_df["Release Status"].astype(str).str.strip().str.upper().map(lambda x: "Released" if x == "R" else "Not Released")
    else:
        release_df["Release Bucket"] = "Not Available"
    release_summary = (
        release_df.groupby("Release Bucket", dropna=False)["PurchDoc"]
        .nunique()
        .reset_index(name="PO Count")
    )

    project_count = filtered_df[project_col].astype(str).str.strip().replace("", pd.NA).dropna().nunique() if has_project else 0
    matl_group_count = filtered_df["Matl Group"].astype(str).str.strip().replace("", pd.NA).dropna().nunique() if has_matl_group else 0

    popup_title = None
    popup_df = None
    summary_popup_clicked = False

    # Executive Summary: 3-column layout keeps UOM/currency values readable.
    if has_division_filter:
        po_breakdown = (
            filtered_df.groupby(division_filter_col, dropna=True)["PurchDoc"]
            .nunique()
            .reset_index(name="PO Count")
            .sort_values("PO Count", ascending=False)
        )
        po_breakdown_text = " | ".join(
            [f"{str(r[division_filter_col])}: {num_fmt(r['PO Count'])}" for _, r in po_breakdown.iterrows()]
        )
        total_po_value = f"{num_fmt(filtered_df['PurchDoc'].nunique())}<br><span style='font-size:14px;font-weight:600;color:#4B5563'>{po_breakdown_text}</span>" if po_breakdown_text else num_fmt(filtered_df["PurchDoc"].nunique())
    else:
        total_po_value = num_fmt(filtered_df["PurchDoc"].nunique())

    row1_col1, row1_col2, row1_col3 = st.columns(3)
    with row1_col1:
        kpi("Total POs", total_po_value)
        if st.button("View details", key="kpi_total_pos", use_container_width=True):
            summary_popup_clicked = True
            popup_title = "Total POs Drilldown"
            popup_df = filtered_df.copy()

    with row1_col2:
        vendor_count_col = "Vendor/Supplying plant" if "Vendor/Supplying plant" in filtered_df.columns else ("Vendor Name" if has_vendor_name else None)
        kpi("Total Vendors", num_fmt(filtered_df[vendor_count_col].nunique() if vendor_count_col else 0))
        if st.button("View details", key="kpi_total_vendors", use_container_width=True):
            summary_popup_clicked = True
            popup_title = "Total Vendors Drilldown"
            popup_df = filtered_df.copy()

    with row1_col3:
        po_uom_text = (
            " | ".join([f"{str(r[uom_col])}: {num_fmt(r['Total Quantity'])}" for _, r in quantity_uom.head(4).iterrows()])
            if not quantity_uom.empty
            else "0"
        )
        kpi("PO Quantity by UOM", po_uom_text)
        if st.button("View details", key="kpi_po_qty_uom", use_container_width=True):
            summary_popup_clicked = True
            popup_title = "PO Quantity by UOM Drilldown"
            popup_df = (
                filtered_df[filtered_df[po_qty_col] > 0].copy() if po_qty_col in filtered_df.columns else filtered_df.iloc[0:0]
            )

    row2_col1, row2_col2, row2_col3 = st.columns(3)
    with row2_col1:
        inr_total = currency_summary.loc[currency_summary[currency_col].astype(str).str.upper() == "INR", "Total Value"].sum() if not currency_summary.empty else 0
        usd_total = currency_summary.loc[currency_summary[currency_col].astype(str).str.upper() == "USD", "Total Value"].sum() if not currency_summary.empty else 0
        kpi(
            "PO Value by Currency",
            f"INR {inr_total:,.2f}<br>USD {usd_total:,.2f}",
            is_amount=True,
        )
        if st.button("View details", key="kpi_po_value_currency", use_container_width=True):
            summary_popup_clicked = True
            popup_title = "PO Value by Currency Drilldown"
            popup_df = (
                filtered_df[filtered_df[po_value_col] > 0].copy() if po_value_col in filtered_df.columns else filtered_df.iloc[0:0]
            )

    with row2_col2:
        gr_uom_text = (
            " | ".join([f"{str(r[uom_col])}: {num_fmt(r['GR Quantity'])}" for _, r in gr_uom.head(4).iterrows()])
            if not gr_uom.empty
            else "0"
        )
        kpi("GR Quantity by UOM", gr_uom_text)
        if st.button("View details", key="kpi_gr_uom", use_container_width=True):
            summary_popup_clicked = True
            popup_title = "GR Quantity by UOM Drilldown"
            popup_df = filtered_df[filtered_df["GR Qty"] > 0].copy() if "GR Qty" in filtered_df.columns else filtered_df.iloc[0:0]

    with row2_col3:
        pend_uom_text = (
            " | ".join([f"{str(r[uom_col])}: {num_fmt(r['Pending Delivery Quantity'])}" for _, r in pending_uom.head(4).iterrows()])
            if not pending_uom.empty
            else "0"
        )
        kpi("Pending Delivery Quantity by UOM", pend_uom_text)
        if st.button("View details", key="kpi_pending_uom", use_container_width=True):
            summary_popup_clicked = True
            popup_title = "Pending Delivery Quantity by UOM Drilldown"
            popup_df = (
                filtered_df[filtered_df["Still to be del."] > 0].copy()
                if "Still to be del." in filtered_df.columns
                else filtered_df.iloc[0:0]
            )

    row3_col1, row3_col2, row3_col3 = st.columns(3)
    with row3_col1:
        kpi("No. of Projects", num_fmt(project_count))
        if st.button("View details", key="kpi_projects", use_container_width=True):
            summary_popup_clicked = True
            popup_title = "Projects Drilldown"
            popup_df = (
                filtered_df[filtered_df[project_col].astype(str).str.strip() != ""]
                .drop_duplicates(subset=[project_col])
                .sort_values(project_col)
                .copy()
                if has_project else filtered_df.iloc[0:0]
            )

    with row3_col2:
        kpi("Material Groups", num_fmt(matl_group_count))
        if st.button("View details", key="kpi_matl_groups", use_container_width=True):
            summary_popup_clicked = True
            popup_title = "Material Groups Drilldown"
            popup_df = (
                filtered_df[filtered_df["Matl Group"].astype(str).str.strip() != ""].copy() if has_matl_group else filtered_df.iloc[0:0]
            )

    with row3_col3:
        released_count = release_summary.loc[release_summary["Release Bucket"] == "Released", "PO Count"].sum()
        not_released_count = release_summary.loc[release_summary["Release Bucket"] == "Not Released", "PO Count"].sum()
        kpi("Release Status", f"Released: {num_fmt(released_count)}<br>Not Released: {num_fmt(not_released_count)}")
        if st.button("View details", key="kpi_release_status", use_container_width=True):
            summary_popup_clicked = True
            popup_title = "Release Status Drilldown"
            popup_df = release_df.copy()

    st.caption(f"Filtered Records: {len(filtered_df):,}")

    st.divider()
    st.markdown('<div class="section-title">Procurement Performance Insights</div>', unsafe_allow_html=True)

    chart1, chart2 = st.columns(2)
    with chart1:
        st.markdown("### PO Count by Division/Plant")
        has_company_name = "Company Name" in filtered_df.columns
        division_col = "Company Name" if has_company_name else "Plant"
        if has_plant and has_company_name:
            plant_chart = (
                filtered_df.groupby(["Plant", "Company Name"], dropna=True)["PurchDoc"]
                .nunique()
                .reset_index(name="PO Count")
                .sort_values("PO Count", ascending=False)
                .head(20)
            )
        elif has_plant:
            plant_chart = (
                filtered_df.groupby("Plant", dropna=True)["PurchDoc"]
                .nunique()
                .reset_index(name="PO Count")
                .sort_values("PO Count", ascending=False)
                .head(20)
            )
        else:
            plant_chart = pd.DataFrame(columns=["Plant", "PO Count"])
        fig = px.bar(
            plant_chart,
            x="Plant",
            y="PO Count",
            color=division_col,
            text="PO Count",
            color_discrete_sequence=px.colors.qualitative.Bold,
            custom_data=[division_col] if division_col in plant_chart.columns else None,
        )
        fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        fig.update_layout(xaxis_tickangle=-35, xaxis_title="Plant", yaxis_title="PO Count")
        event = chart_event(clean_chart(fig, 560), "po_count_plant_click")
        selected = get_clicked_value(event, "x") if (not summary_popup_clicked and st.session_state.get("me2j_active_chart") == "po_count_plant_click") else None
        if selected and has_plant:
            popup_title = f"PO Count by Plant Drilldown: {selected}"
            popup_df = filtered_df[filtered_df["Plant"].astype(str) == str(selected)]

    with chart2:
        st.markdown("### Vendor Summary")
        vendor_chart = (
            filtered_df.groupby("Vendor Name", dropna=True)
            .agg(PO_Count=("PurchDoc", "nunique"), PO_Value=(po_value_col, "sum"))
            .reset_index()
            .sort_values("PO_Value", ascending=False)
            .head(15)
        ) if has_vendor_name else pd.DataFrame(columns=["Vendor Name", "PO_Count", "PO_Value"])
        fig = px.bar(
            vendor_chart,
            x="PO_Value",
            y="Vendor Name",
            orientation="h",
            text="PO_Value",
            custom_data=["PO_Count"],
            color_discrete_sequence=[CHART_COLORS["vendor"]],
        )
        fig.update_traces(texttemplate="%{text:,.2f}", textposition="outside", hovertemplate="<b>%{y}</b><br>PO Value: %{x:,.2f}<br>PO Count: %{customdata[0]:,.0f}<extra></extra>")
        fig.update_layout(yaxis={"automargin": True}, xaxis_title="PO Value", yaxis_title="Vendor Name")
        event = chart_event(clean_chart(fig, 560), "vendor_summary_click")
        selected = get_clicked_value(event, "y") if (not summary_popup_clicked and st.session_state.get("me2j_active_chart") == "vendor_summary_click") else None
        if selected and has_vendor_name:
            popup_title = f"Vendor Summary Drilldown: {selected}"
            popup_df = filtered_df[filtered_df["Vendor Name"].astype(str) == str(selected)]

    chart3, chart4 = st.columns(2)
    with chart3:
        st.markdown("### Quantity by UOM")
        fig = px.bar(
            quantity_uom.head(20),
            x=uom_col,
            y="Total Quantity",
            text="Total Quantity",
            color_discrete_sequence=[CHART_COLORS["material"]],
        )
        fig.update_traces(texttemplate="%{text:,.2f}", textposition="outside")
        fig.update_layout(xaxis_title="Order Unit / UOM", yaxis_title="PO Quantity")
        event = chart_event(clean_chart(fig, 520), "qty_uom_click")
        selected = get_clicked_value(event, "x") if (not summary_popup_clicked and st.session_state.get("me2j_active_chart") == "qty_uom_click") else None
        if selected:
            popup_title = f"Quantity by UOM Drilldown: {selected}"
            popup_df = filtered_df[filtered_df[uom_col].astype(str) == str(selected)]

    with chart4:
        st.markdown("### Value by Currency")
        fig = px.bar(
            currency_summary,
            x=currency_col,
            y="Total Value",
            text="Total Value",
            color=currency_col,
            color_discrete_sequence=[CHART_COLORS["company"], CHART_COLORS["plant"], CHART_COLORS["doc_type"]],
        )
        fig.update_traces(texttemplate="%{text:,.2f}", textposition="outside")
        fig.update_layout(xaxis_title="Currency", yaxis_title="PO Value")
        event = chart_event(clean_chart(fig, 520), "value_currency_click")
        selected = get_clicked_value(event, "x") if (not summary_popup_clicked and st.session_state.get("me2j_active_chart") == "value_currency_click") else None
        if selected:
            popup_title = f"Value by Currency Drilldown: {selected}"
            popup_df = filtered_df[filtered_df[currency_col].astype(str) == str(selected)]

    chart5, chart6 = st.columns(2)
    with chart5:
        st.markdown("### GR Quantity by UOM")
        fig = px.bar(
            gr_uom.head(20),
            x=uom_col,
            y="GR Quantity",
            text="GR Quantity",
            color_discrete_sequence=[CHART_COLORS["trend"]],
        )
        fig.update_traces(texttemplate="%{text:,.2f}", textposition="outside")
        fig.update_layout(xaxis_title="Order Unit / UOM", yaxis_title="GR Quantity")
        event = chart_event(clean_chart(fig, 520), "gr_uom_chart_click")
        selected = get_clicked_value(event, "x") if (not summary_popup_clicked and st.session_state.get("me2j_active_chart") == "gr_uom_chart_click") else None
        if selected and uom_col in filtered_df.columns:
            popup_title = f"GR Quantity by UOM Drilldown: {selected}"
            popup_df = filtered_df[(filtered_df[uom_col].astype(str) == str(selected)) & (filtered_df["GR Qty"] > 0)]

    with chart6:
        st.markdown("### Release Status Summary")
        fig = px.bar(
            release_summary,
            x="Release Bucket",
            y="PO Count",
            text="PO Count",
            color="Release Bucket",
            color_discrete_map={
                "Released": CHART_COLORS["trend"],
                "Not Released": CHART_COLORS["doc_type"],
                "Not Available": CHART_COLORS["delivery"],
            },
        )
        fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        fig.update_layout(xaxis_title="Release Status", yaxis_title="PO Count")
        event = chart_event(clean_chart(fig, 520), "release_status_click")
        selected = get_clicked_value(event, "x") if (not summary_popup_clicked and st.session_state.get("me2j_active_chart") == "release_status_click") else None
        if selected:
            popup_title = f"Release Status Drilldown: {selected}"
            popup_df = release_df[release_df["Release Bucket"].astype(str) == str(selected)]

    chart7, chart8 = st.columns(2)
    with chart7:
        st.markdown("### Project Summary")
        if has_project:
            project_summary = (
                filtered_df[filtered_df[project_col].astype(str).str.strip() != ""]
                .groupby(project_col, dropna=True)["PurchDoc"]
                .nunique()
                .reset_index(name="PO Count")
                .sort_values("PO Count", ascending=False)
                .head(15)
            )
        else:
            project_summary = pd.DataFrame(columns=["Project", "PO Count"])
        project_chart_col = project_col if has_project else "Project"
        fig = px.bar(
            project_summary,
            x="PO Count",
            y=project_chart_col,
            orientation="h",
            text="PO Count",
            color_discrete_sequence=[CHART_COLORS["ai_bar"]],
        )
        fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        fig.update_layout(yaxis={"automargin": True}, xaxis_title="PO Count", yaxis_title="Project")
        event = chart_event(clean_chart(fig, 560), "project_summary_click")
        selected = get_clicked_value(event, "y") if (not summary_popup_clicked and st.session_state.get("me2j_active_chart") == "project_summary_click") else None
        if selected and has_project:
            popup_title = f"Project Drilldown: {selected}"
            popup_df = filtered_df[filtered_df[project_col].astype(str) == str(selected)]

    with chart8:
        st.markdown("### Material Group Summary")
        matl_summary = (
            filtered_df.groupby("Matl Group", dropna=True)["PurchDoc"]
            .nunique()
            .reset_index(name="PO Count")
            .sort_values("PO Count", ascending=False)
            .head(15)
        ) if has_matl_group else pd.DataFrame(columns=["Matl Group", "PO Count"])
        fig = px.bar(
            matl_summary,
            x="PO Count",
            y="Matl Group",
            orientation="h",
            text="PO Count",
            color_discrete_sequence=[CHART_COLORS["matl_group"]],
        )
        fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        fig.update_layout(yaxis={"automargin": True}, xaxis_title="PO Count", yaxis_title="Material Group")
        event = chart_event(clean_chart(fig, 560), "matl_summary_click")
        selected = get_clicked_value(event, "y") if (not summary_popup_clicked and st.session_state.get("me2j_active_chart") == "matl_summary_click") else None
        if selected and has_matl_group:
            popup_title = f"Material Group Drilldown: {selected}"
            popup_df = filtered_df[filtered_df["Matl Group"].astype(str) == str(selected)]

    if popup_title and popup_df is not None:
        show_popup(popup_title, popup_df)
        st.session_state.me2j_active_chart = None

    st.divider()
    st.markdown('<div class="section-title">Detailed Data Preview</div>', unsafe_allow_html=True)
    detail_table(filtered_df, rows=25)

    csv = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download Filtered Data",
        csv,
        "ME2J_FILTERED_DATA.csv",
        "text/csv",
        use_container_width=True
    )

with tab2:
    st.subheader("Filter & Explore Data")
    df = load_data()

    has_vendor_name_tab2 = "Vendor Name" in df.columns
    has_plant_tab2 = "Plant" in df.columns
    has_doc_type_tab2 = "Doc Type" in df.columns
    has_matl_group_tab2 = "Matl Group" in df.columns

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        vendors = ["All"] + sorted(df["Vendor Name"].dropna().unique().tolist()) if has_vendor_name_tab2 else ["All"]
        sel_vendor = st.selectbox("Vendor", vendors)

    with col2:
        plants = ["All"] + sorted(df["Plant"].dropna().unique().tolist()) if has_plant_tab2 else ["All"]
        sel_plant = st.selectbox("Plant", plants)

    with col3:
        doc_types = ["All"] + sorted(df["Doc Type"].dropna().unique().tolist()) if has_doc_type_tab2 else ["All"]
        sel_doc_type = st.selectbox("Doc Type", doc_types)

    with col4:
        matl_groups = ["All"] + sorted(df["Matl Group"].dropna().unique().tolist()) if has_matl_group_tab2 else ["All"]
        sel_matl = st.selectbox("Material Group", matl_groups)

    filtered = df.copy()

    if has_vendor_name_tab2 and sel_vendor != "All":
        filtered = filtered[filtered["Vendor Name"] == sel_vendor]
    if has_plant_tab2 and sel_plant != "All":
        filtered = filtered[filtered["Plant"] == sel_plant]
    if has_doc_type_tab2 and sel_doc_type != "All":
        filtered = filtered[filtered["Doc Type"] == sel_doc_type]
    if has_matl_group_tab2 and sel_matl != "All":
        filtered = filtered[filtered["Matl Group"] == sel_matl]

    st.caption(f"Showing {len(filtered):,} of {len(df):,} records")
    st.dataframe(filtered, use_container_width=True, height=500, hide_index=True)

    csv = filtered.to_csv(index=False).encode("utf-8")
    st.download_button("Download Filtered CSV", csv, "ME2J_FILTERED_REPORT.csv", "text/csv")

with tab3:
    AGENT_FQN = "SNOWFLAKE_POC.ME2J_SCHEMA.BGRE_ME2J_PROCUREMENT_AGENT"

    st.subheader("AI Assistant")
    st.caption("Connected to Cortex Agent: BGRE_ME2J_PROCUREMENT_AGENT")

    def run_agent(question):
        payload = json.dumps({
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": question}]
                }
            ]
        })

        safe_payload = payload.replace("$$", "$ $")

        agent_sql = f"""
            SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
                '{AGENT_FQN}',
                $${safe_payload}$$
            ) AS RESP
        """

        result_df = pd.read_sql(agent_sql, conn)
        return result_df["RESP"].iloc[0]

    def parse_agent_response(raw_resp):
        try:
            if isinstance(raw_resp, str):
                resp = json.loads(raw_resp)
            else:
                resp = raw_resp
        except Exception:
            return {
                "text": str(raw_resp),
                "sql": None,
                "table": None,
                "suggestions": []
            }

        final_text = []
        final_sql = None
        final_table = None
        suggestions = []

        for item in resp.get("content", []):
            item_type = item.get("type")

            if item_type == "text":
                text = item.get("text", "")
                if text:
                    final_text.append(text)

            elif item_type == "suggested_queries":
                for q in item.get("suggested_queries", []):
                    if q.get("query"):
                        suggestions.append(q["query"])

            elif item_type == "tool_result":
                for content in item.get("tool_result", {}).get("content", []):
                    if content.get("type") == "json":
                        j = content.get("json", {})

                        if j.get("text"):
                            final_text.append(j["text"])

                        if j.get("sql"):
                            final_sql = j["sql"]

                        rs = j.get("result_set")
                        if rs and rs.get("data"):
                            cols = [
                                c["name"]
                                for c in rs.get("resultSetMetaData", {}).get("rowType", [])
                            ]
                            final_table = pd.DataFrame(rs["data"], columns=cols if cols else None)

        return {
            "text": "\n\n".join(final_text) if final_text else "No detailed response received from agent.",
            "sql": final_sql,
            "table": final_table,
            "suggestions": suggestions
        }

    def make_ai_chart(df):
        if df is None or df.empty:
            return

        try:
            chart_df = df.copy()
            chart_df.columns = [str(c) for c in chart_df.columns]

            date_cols = []
            for col in chart_df.columns:
                if any(x in col.upper() for x in ["DATE", "MONTH", "YEAR", "PERIOD"]):
                    converted = pd.to_datetime(chart_df[col], errors="coerce")
                    if converted.notna().sum() > 0:
                        chart_df[col] = converted
                        date_cols.append(col)

            for col in chart_df.columns:
                if col not in date_cols:
                    converted_num = pd.to_numeric(chart_df[col], errors="coerce")
                    if converted_num.notna().sum() > 0:
                        chart_df[col] = converted_num

            num_cols = chart_df.select_dtypes(include=["number"]).columns.tolist()
            date_cols = chart_df.select_dtypes(include=["datetime64[ns]"]).columns.tolist()
            text_cols = chart_df.select_dtypes(include=["object"]).columns.tolist()

            if not num_cols and not text_cols:
                return

            st.markdown("### Visual Insight")

            if len(chart_df) == 1 and num_cols:
                cols = st.columns(min(len(num_cols), 4))
                for i, col in enumerate(num_cols[:4]):
                    with cols[i]:
                        st.metric(col.replace("_", " ").title(), f"{chart_df[col].iloc[0]:,.2f}")
                return

            if date_cols and num_cols:
                x_col = date_cols[0]
                y_col = num_cols[0]

                trend_df = chart_df[[x_col, y_col]].dropna().sort_values(x_col)

                fig = px.line(
                    trend_df,
                    x=x_col,
                    y=y_col,
                    markers=True,
                    text=y_col,
                    title=f"{y_col} Trend by {x_col}",
                    color_discrete_sequence=[CHART_COLORS["ai_line"]],
                )
                fig.update_traces(texttemplate="%{text:,.2f}", textposition="top center")
                fig.update_layout(height=600)
                st.plotly_chart(fig, use_container_width=True)
                return

            if text_cols and num_cols:
                label_col = text_cols[0]
                value_col = num_cols[0]

                bar_df = (
                    chart_df[[label_col, value_col]]
                    .dropna()
                    .sort_values(value_col, ascending=False)
                    .head(20)
                )

                fig = px.bar(
                    bar_df,
                    x=value_col,
                    y=label_col,
                    orientation="h",
                    text=value_col,
                    title=f"{value_col} by {label_col}",
                    color_discrete_sequence=[CHART_COLORS["ai_bar"]],
                )
                fig.update_layout(
                    height=700,
                    yaxis={"automargin": True},
                    margin=dict(l=10, r=100, t=60, b=40)
                )
                fig.update_traces(texttemplate="%{text:,.2f}", textposition="outside")
                st.plotly_chart(fig, use_container_width=True)
                return

            if len(num_cols) >= 2:
                st.line_chart(chart_df[num_cols].head(50))
                return

            if len(num_cols) == 1:
                value_col = num_cols[0]
                fig = px.histogram(
                    chart_df,
                    x=value_col,
                    title=f"Distribution of {value_col}",
                    color_discrete_sequence=[CHART_COLORS["ai_hist"]],
                )
                fig.update_layout(height=550)
                st.plotly_chart(fig, use_container_width=True)
                return

            if text_cols:
                label_col = text_cols[0]
                count_df = (
                    chart_df[label_col]
                    .astype(str)
                    .value_counts()
                    .reset_index()
                )
                count_df.columns = [label_col, "Count"]

                fig = px.bar(
                    count_df.head(20),
                    x="Count",
                    y=label_col,
                    orientation="h",
                    text="Count",
                    title=f"Count by {label_col}",
                    color_discrete_sequence=[CHART_COLORS["ai_bar"]],
                )
                fig.update_layout(height=650, yaxis={"automargin": True})
                fig.update_traces(textposition="outside")
                st.plotly_chart(fig, use_container_width=True)
                return

        except Exception:
            st.info("Chart could not be generated for this result format, but the answer and data are available above.")

    def render_agent_result(parsed):
        st.markdown("### Answer")
        st.markdown(parsed["text"])

        if parsed.get("sql"):
            with st.expander("Generated SQL"):
                st.code(parsed["sql"], language="sql")

        if parsed.get("table") is not None and not parsed["table"].empty:
            st.markdown("### Result Data")
            st.dataframe(parsed["table"], use_container_width=True, hide_index=True)

            make_ai_chart(parsed["table"])

            csv = parsed["table"].to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download AI Result",
                csv,
                "AI_RESULT.csv",
                "text/csv",
                use_container_width=True
            )

        if parsed.get("suggestions"):
            st.markdown("### Suggested Follow-up Questions")
            for q in parsed["suggestions"][:5]:
                st.write(f"- {q}")

    if "me2j_agent_messages" not in st.session_state:
        st.session_state.me2j_agent_messages = []

    for msg in st.session_state.me2j_agent_messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                render_agent_result(msg["content"])
            else:
                st.markdown(msg["content"])

    def clear_me2j_chart_state():
        st.session_state.me2j_active_chart = None

    user_question = st.chat_input(
        "Ask about ME2J procurement data...",
        on_submit=clear_me2j_chart_state
    )

    if user_question:
        st.session_state.me2j_active_chart = None
        st.session_state.me2j_agent_messages.append({
            "role": "user",
            "content": user_question
        })

        with st.chat_message("user"):
            st.markdown(user_question)

        with st.chat_message("assistant"):
            with st.spinner("Cortex Agent is analyzing..."):
                try:
                    raw_response = run_agent(user_question)
                    parsed = parse_agent_response(raw_response)
                    render_agent_result(parsed)

                    st.session_state.me2j_agent_messages.append({
                        "role": "assistant",
                        "content": parsed
                    })

                except Exception:
                    st.info("AI response could not be generated for this question. Please try rephrasing the question.")
