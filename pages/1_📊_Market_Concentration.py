import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import requests
import numpy as np
import os
from dotenv import load_dotenv

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Market Concentration",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "processed"

API_BASE_URL = "http://127.0.0.1:8000"
load_dotenv(BASE_DIR / ".env")


# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_data():
    global_df = pd.read_csv(DATA_DIR / "global_watch_market.csv")
    trends_df = pd.read_csv(DATA_DIR / "google_trends_brand_attention.csv")

    ebay_attention_path = DATA_DIR / "ebay_google_attention_market.csv"

    if ebay_attention_path.exists():
        ebay_attention_df = pd.read_csv(ebay_attention_path)
    else:
        ebay_attention_df = pd.DataFrame()

    return global_df, trends_df, ebay_attention_df


global_df, trends_df, ebay_attention_df = load_data()


# =========================
# TITLE
# =========================
st.title("1. Market Concentration in Luxury Watch Resale")

st.markdown("""
This page provides the macro view of the luxury watch secondary market.

The objective is to understand whether listing activity, price and public attention
are evenly distributed across brands — or concentrated around a small number
of dominant names.
""")

st.info("""
The analysis has three scopes: a broad historical market overview (Top 15 brands),
a purposively selected eight-brand comparison, and a separate standardized eBay API sample.
The Top 15 chart reads FastAPI + SQLite when available and otherwise uses the same
full historical dataset from CSV. Only the selected-brand charts follow sidebar filters.
""")


# =========================
# CLEAN DATA
# =========================
global_df = global_df.copy()

global_df["price"] = pd.to_numeric(global_df["price"], errors="coerce")
global_df = global_df.dropna(subset=["brand", "price"]).copy()

global_df["brand"] = global_df["brand"].replace({
    "Audemars": "Audemars Piguet",
    "Audemars Piguet": "Audemars Piguet"
})

segment_map = {
    "TAG Heuer": "Accessible luxury",
    "Longines": "Accessible luxury",
    "Omega": "Broad premium",
    "Cartier": "Broad premium",
    "Rolex": "High prestige",
    "Patek Philippe": "Collector prestige",
    "Audemars Piguet": "Collector prestige",
    "Richard Mille": "Ultra prestige niche"
}

# Keep the complete historical dataset for the exploratory Top 15 chart.
# The selected-brand subset below is used for KPIs and comparative charts.
full_market_df = global_df.copy()
global_df["market_segment"] = global_df["brand"].map(segment_map)

global_df = global_df.dropna(subset=["market_segment"]).copy()


# =========================
# SIDEBAR FILTERS
# =========================
st.sidebar.header("Filters")

available_segments = sorted(global_df["market_segment"].dropna().unique())

selected_segments = st.sidebar.multiselect(
    "Market segment",
    options=available_segments,
    default=available_segments
)

available_brands = sorted(
    global_df[
        global_df["market_segment"].isin(selected_segments)
    ]["brand"]
    .dropna()
    .unique()
)

selected_brands = st.sidebar.multiselect(
    "Brand",
    options=available_brands,
    default=available_brands
)

price_min, price_max = st.sidebar.slider(
    "Price range",
    min_value=float(global_df["price"].quantile(0.01)),
    max_value=float(global_df["price"].quantile(0.99)),
    value=(
        float(global_df["price"].quantile(0.01)),
        float(global_df["price"].quantile(0.99))
    )
)

filtered_df = global_df[
    (global_df["market_segment"].isin(selected_segments)) &
    (global_df["brand"].isin(selected_brands)) &
    (global_df["price"].between(price_min, price_max))
].copy()


# =========================
# KPI
# =========================
st.subheader("Selected-brand comparative analysis — 8 brands")
st.caption(
    "The KPIs below use the eight selected brands and respond to sidebar filters "
    "(segment, brand and price). They do not describe the entire historical market."
)
brand_count = filtered_df["brand"].nunique()
listing_count = len(filtered_df)
median_price = filtered_df["price"].median()

rolex_share = (
    filtered_df["brand"].eq("Rolex").sum() / len(filtered_df) * 100
    if len(filtered_df) > 0 else 0
)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Listings", f"{listing_count:,}")
col2.metric("Brands", brand_count)
col3.metric("Median price", f"${median_price:,.0f}")
col4.metric("Rolex listing share", f"{rolex_share:.1f}%")

st.divider()


# =========================
# CHART 1: BRAND LISTING INTENSITY
# =========================
st.subheader("Exploratory market overview — Top 15 brands")
st.caption(
    "This chart covers the full historical dataset (top 15 brands by listing count), "
    "independently of the eight-brand sidebar filters and price range. "
    "It provides context before the selected-brand comparison."
)

try:
    response = requests.get(
        f"{API_BASE_URL}/market-concentration",
        params={"limit": 15},
        timeout=3
    )

    response.raise_for_status()

    brand_volume = pd.DataFrame(response.json())
    api_status = "FastAPI + SQLite"

except Exception:
    brand_volume = (
        full_market_df
        .groupby("brand", as_index=False)
        .agg(listing_count=("brand", "count"))
        .sort_values("listing_count", ascending=False)
        .head(15)
    )

    api_status = "CSV fallback"

brand_volume = brand_volume.sort_values(
    "listing_count",
    ascending=True
)

fig = px.bar(
    brand_volume,
    x="listing_count",
    y="brand",
    orientation="h",
    title="Full Historical Dataset — Top 15 Brands by Listing Volume",
    labels={
        "listing_count": "Number of listings",
        "brand": "Brand"
    }
)

fig.update_layout(height=600)

st.plotly_chart(fig, use_container_width=True)

st.markdown("""
**Insight:** Secondary-market listing volume is highly concentrated. Rolex
stands out as the most visible brand in the historical dataset, which makes it
a useful case study for deeper analysis of resale premium formation.
""")

st.caption(
    f"Data source for this chart: {api_status}. "
    "If FastAPI is running, the chart queries the SQLite analytical database dynamically. "
    "Otherwise, it uses the processed CSV dataset."
)

st.divider()


# =========================
# CHART 2: MARKET POSITIONING
# =========================
st.subheader("Selected-brand comparison — Market Positioning")
st.caption(
    "Eight brands were purposively selected to compare different market positions: "
    "TAG Heuer and Longines (accessible luxury); Omega and Cartier (broad premium); "
    "Rolex (high prestige); Patek Philippe and Audemars Piguet (collector prestige); "
    "Richard Mille (ultra-prestige niche). These are project-defined analytical "
    "segments, not official industry categories. The charts below follow the sidebar filters."
)

brand_metrics = (
    filtered_df
    .groupby(["brand", "market_segment"], as_index=False)
    .agg(
        listing_count=("brand", "count"),
        median_price=("price", "median"),
        avg_price=("price", "mean")
    )
)

fig = px.scatter(
    brand_metrics,
    x="listing_count",
    y="median_price",
    size="listing_count",
    color="market_segment",
    hover_name="brand",
    text="brand",
    log_y=True,
    title="Luxury Watch Market Positioning: Volume vs Median Price",
    labels={
        "listing_count": "Listing volume",
        "median_price": "Median price, log scale",
        "market_segment": "Market segment"
    }
)

fig.update_traces(textposition="top center")
fig.update_layout(height=650)

st.plotly_chart(fig, use_container_width=True)

st.markdown("""
**Insight:** The luxury watch resale market separates into distinct market roles.
Rolex combines high visibility with prestige pricing, while brands such as Richard Mille
occupy an ultra-premium niche with much lower listing volume.
""")

st.divider()


# =========================
# CHART 3: GOOGLE ATTENTION VS PRICE
# =========================
st.subheader("Google Attention vs Average Secondary-Market Price")

attention_df = trends_df[[
    "brand",
    "relative_attention_score"
]].drop_duplicates()

attention_metrics = brand_metrics.merge(
    attention_df,
    on="brand",
    how="inner"
).copy()

attention_metrics["bubble_size"] = np.sqrt(
    attention_metrics["listing_count"]
)

fig = px.scatter(
    attention_metrics,
    x="avg_price",
    y="relative_attention_score",
    size="bubble_size",
    color="market_segment",
    hover_name="brand",
    text="brand",
    log_x=True,
    size_max=60,
    title="Public Attention vs Average Secondary-Market Price",
    labels={
        "avg_price": "Average price, log scale",
        "relative_attention_score": "Relative Google Trends attention",
        "market_segment": "Market segment",
        "bubble_size": "Listing volume"
    },
    hover_data={
        "bubble_size": False,
        "listing_count": True,
        "avg_price": ":,.0f",
        "relative_attention_score": ":.2f"
    }
)

fig.update_traces(
    textposition="top center",
    textfont_size=15,
    marker=dict(
        opacity=0.65,
        line=dict(width=1, color="white")
    )
)

fig.update_layout(
    height=650,
    legend_title_text="Market segment",
    font=dict(size=15),
    margin=dict(l=40, r=40, t=80, b=40)
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("""
**Insight:** Public attention does not simply follow price hierarchy.
Rolex combines strong public attention with prestige pricing, while some
ultra-prestige brands remain expensive but much more niche in public search behavior.
""")

st.divider()


# =========================
# CHART 4: SEGMENT CONCENTRATION
# =========================
st.subheader("Listing Concentration by Market Segment")

segment_volume = (
    filtered_df
    .groupby("market_segment", as_index=False)
    .agg(listing_count=("brand", "count"))
    .sort_values("listing_count", ascending=True)
)

fig = px.bar(
    segment_volume,
    x="listing_count",
    y="market_segment",
    orientation="h",
    title="Secondary-Market Listing Concentration by Segment",
    labels={
        "listing_count": "Number of listings",
        "market_segment": "Market segment"
    }
)

fig.update_layout(height=500)

st.plotly_chart(fig, use_container_width=True)

st.markdown("""
**Insight:** Listing activity is unevenly distributed across market segments.
Broad premium and accessible-luxury brands contribute substantial listing volume,
while the high-prestige segment is strongly shaped by Rolex's large secondary-market presence.
""")

st.divider()


# =========================
# EBAY API RETRIEVAL SATURATION
# =========================

st.subheader("Live API Retrieval Saturation: eBay Market Sample")

st.markdown("""
This section uses the eBay Browse API as a live searchable-inventory signal.

Unlike the historical Kaggle dataset, the eBay API layer can be refreshed programmatically.
Here, the API is used to compare how quickly different brands saturate a standardized retrieval window.
""")

col_refresh, col_note = st.columns([1, 3])

with col_refresh:
    refresh_clicked = st.button("Refresh eBay API data")

with col_note:
    st.caption(
        "This button calls FastAPI, runs the eBay collection script, "
        "rebuilds the eBay × Google Trends processed dataset, and reloads SQLite."
    )

if refresh_clicked:
    try:
        refresh_key = os.getenv("WATCH_API_KEY", "")
        if not refresh_key:
            st.error("WATCH_API_KEY is missing from your local .env file.")
            st.stop()
        response = requests.post(
            f"{API_BASE_URL}/refresh-ebay-market",
            headers={"X-API-Key": refresh_key},
            timeout=120
        )
        response.raise_for_status()
        refresh_result = response.json()

        st.success(
            f"eBay API data refreshed successfully at {refresh_result.get('refreshed_at')}"
        )

        st.cache_data.clear()

    except Exception as e:
        st.error(
            "Could not refresh eBay API data. "
            "Make sure FastAPI is running and your eBay credentials are correctly configured."
        )
        st.exception(e)

# -------------------------
# Load eBay inventory data
# -------------------------
try:
    response = requests.get(
        f"{API_BASE_URL}/ebay-inventory",
        timeout=5
    )
    response.raise_for_status()

    ebay_inventory = pd.DataFrame(response.json())
    ebay_source = "FastAPI + SQLite"

except Exception:
    if not ebay_attention_df.empty:
        ebay_inventory = ebay_attention_df.copy()
        ebay_source = "CSV fallback"
    else:
        ebay_inventory = pd.DataFrame()
        ebay_source = "Unavailable"

if ebay_inventory.empty:
    st.warning("""
    No eBay inventory dataset is available yet.
    Run `python src/collect_ebay.py`, `python src/prepare_ebay_attention.py`,
    then `python src/store.py`.
    """)

else:
    # -------------------------
    # Cleaning
    # -------------------------
    ebay_inventory["ebay_listing_count"] = pd.to_numeric(
        ebay_inventory["ebay_listing_count"],
        errors="coerce"
    )

    ebay_inventory["ebay_median_price"] = pd.to_numeric(
        ebay_inventory["ebay_median_price"],
        errors="coerce"
    )

    ebay_inventory["relative_attention_score"] = pd.to_numeric(
        ebay_inventory["relative_attention_score"],
        errors="coerce"
    )

    ebay_inventory = ebay_inventory.dropna(
        subset=[
            "brand",
            "ebay_listing_count",
            "ebay_median_price",
            "relative_attention_score"
        ]
    ).copy()

    # -------------------------
    # API retrieval saturation
    # -------------------------
    API_CAP = 200

    ebay_inventory["retrieval_saturation"] = (
        ebay_inventory["ebay_listing_count"] / API_CAP
    )

    def classify_saturation(x):
        if x >= 0.9:
            return "High saturation"
        elif x >= 0.6:
            return "Medium saturation"
        else:
            return "Low saturation"

    ebay_inventory["market_depth_signal"] = (
        ebay_inventory["retrieval_saturation"]
        .apply(classify_saturation)
    )

    # -------------------------
    # Attention / inventory mismatch index
    # -------------------------
    ebay_inventory["inventory_share"] = (
        ebay_inventory["ebay_listing_count"]
        / ebay_inventory["ebay_listing_count"].sum()
    )

    ebay_inventory["attention_share"] = (
        ebay_inventory["relative_attention_score"]
        / ebay_inventory["relative_attention_score"].sum()
    )

    ebay_inventory["attention_inventory_index"] = (
        ebay_inventory["attention_share"]
        / ebay_inventory["inventory_share"]
    )

    ebay_inventory["market_signal"] = pd.cut(
        ebay_inventory["attention_inventory_index"],
        bins=[0, 0.75, 1.25, float("inf")],
        labels=[
            "Inventory-heavy",
            "Balanced",
            "Attention-heavy"
        ]
    )

    # -------------------------
    # KPI
    # -------------------------
    total_api_samples = int(ebay_inventory["ebay_listing_count"].sum())

    top_saturation_brand = (
        ebay_inventory
        .sort_values("retrieval_saturation", ascending=False)
        .iloc[0]["brand"]
    )

    top_attention_gap_brand = (
        ebay_inventory
        .sort_values("attention_inventory_index", ascending=False)
        .iloc[0]["brand"]
    )

    k1, k2, k3 = st.columns(3)

    k1.metric("Retrieved API samples", f"{total_api_samples:,}")
    k2.metric("Highest retrieval saturation", top_saturation_brand)
    k3.metric("Highest attention / inventory gap", top_attention_gap_brand)

    # -------------------------
    # Chart 1: API retrieval saturation
    # -------------------------
    st.subheader("API Retrieval Saturation by Brand")

    saturation_df = ebay_inventory.sort_values(
        "retrieval_saturation",
        ascending=True
    ).copy()

    fig = px.bar(
        saturation_df,
        x="retrieval_saturation",
        y="brand",
        color="market_depth_signal",
        orientation="h",
        text=saturation_df["retrieval_saturation"].apply(lambda x: f"{x:.0%}"),
        title="API Retrieval Saturation by Brand",
        labels={
            "retrieval_saturation": "Retrieval saturation ratio",
            "brand": "Brand",
            "market_depth_signal": "Retrieval saturation"
        },
        hover_data={
            "ebay_listing_count": True,
            "ebay_median_price": ":,.0f",
            "relative_attention_score": ":.2f"
        }
    )

    fig.add_vline(
        x=1,
        line_dash="dash",
        annotation_text="API cap",
        annotation_position="top"
    )

    fig.update_traces(textposition="outside")
    fig.update_layout(
        height=550,
        xaxis_tickformat=".0%",
        xaxis_range=[0, 1.1]
    )

    st.plotly_chart(fig, use_container_width=True)

    st.caption("""
    Methodological note:
    The eBay API results shown here are based on a standardized retrieval sample.
    For each brand, the collection process uses a controlled API query limit
    currently capped at 200 retrievable listings per brand query.

    As a result, retrieval saturation should not be interpreted as total eBay market share.
    Instead, it indicates how quickly each brand fills the standardized API retrieval window.
    """)

    top_api_brand = ebay_inventory.loc[
    ebay_inventory["retrieval_saturation"].idxmax(), "brand"
    ]

    st.markdown(f"""
    **Insight:** The live eBay sample shows a different brand hierarchy from the
    historical marketplace data. While Rolex dominates historical listing volume,
    **{top_api_brand}** currently records the highest retrieval saturation in the
    standardized eBay sample.

    This contrast shows that secondary-market presence can vary across platforms
    and over time. The eBay API therefore provides a complementary live-market signal
    rather than a direct proxy for the broader resale market.
    """)

    # -------------------------
    # Chart 2: Attention / inventory mismatch
    # -------------------------
    st.subheader("Attention vs API Inventory Mismatch")

    mismatch_df = ebay_inventory.sort_values(
        "attention_inventory_index",
        ascending=True
    ).copy()

    fig = px.bar(
        mismatch_df,
        x="attention_inventory_index",
        y="brand",
        color="market_signal",
        orientation="h",
        text=mismatch_df["attention_inventory_index"].round(2),
        title="Attention-to-Inventory Index by Brand",
        labels={
            "attention_inventory_index": "Attention-to-inventory index",
            "brand": "Brand",
            "market_signal": "Market signal"
        },
        hover_data={
            "attention_share": ":.2%",
            "inventory_share": ":.2%",
            "relative_attention_score": ":.2f",
            "ebay_listing_count": True
        }
    )

    fig.add_vline(
        x=1,
        line_dash="dash",
        annotation_text="Balanced attention / inventory",
        annotation_position="top"
    )

    fig.update_traces(textposition="outside")
    fig.update_layout(height=550)

    st.plotly_chart(fig, use_container_width=True)
    
    top_attention_brand = ebay_inventory.loc[
    ebay_inventory["attention_inventory_index"].idxmax(), "brand"
    ]

    top_attention_index = ebay_inventory[
        "attention_inventory_index"
    ].max()

    lowest_attention_brand = ebay_inventory.loc[
        ebay_inventory["attention_inventory_index"].idxmin(), "brand"
    ]

    lowest_attention_index = ebay_inventory[
        "attention_inventory_index"
    ].min()

    st.markdown(f"""
    **Insight:** Public attention and retrieved eBay inventory are not proportional
    across brands. In the current API sample, **{top_attention_brand}** shows the
    strongest attention-to-inventory mismatch, with an index of
    **{top_attention_index:.2f}**, while **{lowest_attention_brand}** records the
    lowest relative attention at **{lowest_attention_index:.2f}**.

    The live results therefore show that searchable inventory presence and public
    attention capture different dimensions of the secondary market. Because the API
    sample can change when refreshed, these results are interpreted as a current
    market signal rather than a fixed ranking of brands.
    """)

    # =========================================================
# Brand Interpretation
# =========================================================

st.subheader("Brand Interpretation")

with st.expander("Metric definitions"):

    st.markdown("""

- **API saturation** = retrieved API listings ÷ API cap of 200

    Indicates how quickly a brand fills the standardized eBay API retrieval window.

- **Attention ratio** = Google attention share ÷ eBay API inventory share

    Above 1 → public attention is stronger than inventory share.

    Below 1 → searchable inventory is stronger than public attention.
""")
    
st.warning("""
Methodological limitations:

The eBay API layer is used here as a standardized retrieval signal rather than a complete representation of the global luxury watch market.

Several structural limitations should therefore be considered:

- Some ultra-high-end brands may be underrepresented in a standardized eBay retrieval sample relative to other secondary-market channels.

- Certain broad keyword searches may also capture non-core products,
accessories, or lower-priced subsegments. API retrieval results should therefore
be interpreted as standardized searchable samples rather than perfectly
comparable representations of each brand's core watch market.

- As a result, the API retrieval layer should be interpreted as a comparable visibility and searchability signal within the eBay ecosystem, not as an exact measurement of total global market inventory.
""")

# -------------------------
# Interpretation dataframe
# -------------------------

interpretation_df = ebay_inventory[[
    "brand",
    "market_segment",
    "ebay_listing_count",
    "retrieval_saturation",
    "market_depth_signal",
    "attention_inventory_index",
    "market_signal",
    "ebay_median_price"
]].copy()

interpretation_df = interpretation_df.rename(columns={
    "brand": "Brand",
    "market_segment": "Segment",
    "ebay_listing_count": "API sample",
    "retrieval_saturation": "API saturation",
    "market_depth_signal": "eBay saturation",
    "attention_inventory_index": "Attention ratio",
    "market_signal": "Signal",
    "ebay_median_price": "Median price"
})

# -------------------------
# Formatting
# -------------------------

interpretation_df = interpretation_df.sort_values(
    "API saturation",
    ascending=False
)

interpretation_df["API saturation"] = (
    interpretation_df["API saturation"] * 100
).round(1).astype(str) + "%"

interpretation_df["Attention ratio"] = (
    interpretation_df["Attention ratio"]
).round(2)

interpretation_df["Median price"] = (
    "$" + interpretation_df["Median price"].round(0).astype(int).astype(str)
)

# -------------------------
# Display table
# -------------------------

st.dataframe(
    interpretation_df,
    use_container_width=True,
    hide_index=True
)

# =========================================================
# Conclusion
# =========================================================

st.markdown("""
### Conclusion

The secondary luxury watch market is not structured equally across brands.

Historical marketplace data shows strong concentration in listing activity,
with Rolex holding the largest listing presence in the dataset. The live API
layer adds a complementary perspective: searchable inventory and public
attention can vary substantially across brands, platforms and collection times.

The historical market concentration therefore provides the basis for selecting
Rolex as the focused case study in the next pages, while the live API results
serve as a dynamic cross-check of current market signals.
""")

st.caption(f"Data source for this section: {ebay_source}")

# =========================================================
# Raw API table
# =========================================================

with st.expander("Raw eBay API inventory data"):

    st.dataframe(
        ebay_inventory,
        use_container_width=True
    )