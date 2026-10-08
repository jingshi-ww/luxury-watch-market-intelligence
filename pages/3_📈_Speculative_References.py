import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Speculative References",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "processed"

# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_data():
    hist = pd.read_csv(DATA_DIR / "rolex_historical_market.csv")
    live = pd.read_csv(DATA_DIR / "rolex_live_market.csv")
    return hist, live


hist_df, live_df = load_data()

# =========================
# TITLE
# =========================
st.title("3. Rolex Reference-Level Premium Concentration")

st.markdown("""
This page moves from feature-level premium mechanics to reference-level concentration.

The objective is to examine how resale premiums are distributed
across Rolex references, and whether particularly high premiums
are concentrated among a selected group of recognizable sports
and collector-oriented configurations.
""")

st.info("""
Methodological note: this page uses the historical marketplace-level Rolex dataset.
It is kept separate from the daily visibility dataset used in Page 2 because reference-level
speculative analysis requires a cleaner comparison across references.
""")

# =========================
# CLEAN HISTORICAL DATA
# =========================
hist_df = hist_df.copy()

hist_df["premium_pct"] = pd.to_numeric(hist_df["premium_pct"], errors="coerce")
hist_df["price"] = pd.to_numeric(hist_df["price"], errors="coerce")

hist_df = hist_df.dropna(
    subset=["reference", "collection", "premium_pct", "price"]
).copy()

hist_df["reference"] = hist_df["reference"].astype(str).str.strip()
hist_df["collection"] = hist_df["collection"].astype(str).str.strip()

# Mainstream premium range to avoid extreme distortions
hist_df = hist_df[
    (hist_df["premium_pct"] > -80) &
    (hist_df["premium_pct"] < 300)
].copy()

# =========================
# REFERENCE METRICS
# =========================
reference_metrics = (
    hist_df
    .groupby(["reference", "collection"], as_index=False)
    .agg(
        listing_count=("premium_pct", "count"),
        median_premium=("premium_pct", "median"),
        median_price=("price", "median")
    )
)

reference_metrics = reference_metrics[
    reference_metrics["listing_count"] >= 100
].copy()

# Identify key hype references
hype_keywords = [
    "126710BLRO",  # GMT-Master II Pepsi
    "116610LV",    # Submariner Hulk
    "116500LN",    # Cosmograph Daytona ceramic
    "126710BLNR",  # GMT-Master II Batman / Batgirl
    "116710BLNR",  # GMT-Master II Batman (previous generation)
    "116710LN",    # GMT-Master II black bezel
    "116508",      # Cosmograph Daytona Yellow Gold
    "326934",      # Sky-Dweller Steel / White Gold
]

# Readable names for the references highlighted in the charts.
# This mapping affects presentation only, not segmentation or premium values.
reference_names = {
    "116500LN": "Daytona - Ceramic Bezel",
    "116610LV": "Submariner Date - Hulk",
    "126710BLRO": "GMT-Master II - Pepsi",
    "126710BLNR": "GMT-Master II - Blue/Black Bezel",
    "116710BLNR": "GMT-Master II - Blue/Black (Previous Gen.)",
    "116710LN": "GMT-Master II - Black Bezel",
    "116508": "Daytona - Yellow Gold",
    "326934": "Sky-Dweller - Steel/White Gold",
    "114300": "Oyster Perpetual 39",
    "116506": "Daytona - Platinum",
    "116400GV": "Milgauss - Green Crystal",
    "114060": "Submariner - No Date",
}

reference_metrics["model_description"] = (
    reference_metrics["reference"]
    .map(reference_names)
    .fillna(reference_metrics["collection"])
)

reference_metrics["is_hype_reference"] = reference_metrics["reference"].apply(
    lambda x: any(keyword in str(x) for keyword in hype_keywords)
)

reference_metrics["segment"] = reference_metrics["is_hype_reference"].map({
    True: "Key sports / hype references",
    False: "Other references"
})

# =========================
# KPI
# =========================
if reference_metrics.empty:
    st.warning("No reference-level data available after filtering.")
    st.stop()

top_ref = reference_metrics.sort_values(
    "median_premium",
    ascending=False
).iloc[0]

hype_ref_count = reference_metrics["is_hype_reference"].sum()
hype_ref_share = reference_metrics["is_hype_reference"].mean() * 100
overall_median = reference_metrics["median_premium"].median()

col1, col2, col3, col4 = st.columns(4)

col1.metric("References analyzed", f"{len(reference_metrics):,}")
col2.metric("Top premium reference", top_ref["reference"])
col3.metric("Top reference premium", f"{top_ref['median_premium']:.1f}%")
col4.metric("Hype reference share", f"{hype_ref_share:.1f}%")

st.divider()

# =========================
# Introduction
# =========================

with st.expander("Reference selection and segmentation methodology"):
    st.markdown("""
    **Reference identification**

    Rolex watches are grouped by their reference numbers.
    Each reference is analyzed using its historical listing
    count and median resale premium.

    **Selection of key sports / hype references**

    Eight recognizable sports and collector-oriented Rolex
    references were selected for exploratory comparison.
    The selection includes configurations from the Daytona,
    GMT-Master II, Submariner, and Sky-Dweller collections.

    These references were chosen as illustrative cases of
    recognizable configurations and patterns observed
    during initial market exploration.

    **Interpretation**

    The selected group is compared with all other eligible
    references to examine the concentration of resale premiums.

    This is a researcher-defined exploratory segmentation,
    not an official Rolex classification, an exhaustive list
    of collectible models, or an independently validated
    measure of market hype.

    References outside the selected group may also have
    strong collector demand or high resale premiums.
    """)


# =========================
# CHART 1: PREMIUM CONCENTRATION
# =========================
st.header("Premium Concentration Around Key Sports References")

fig = px.scatter(
    reference_metrics,
    x="listing_count",
    y="median_premium",
    size="median_price",
    color="segment",
    custom_data=[
        "reference", "model_description", "collection",
        "listing_count", "median_premium", "median_price"
    ],
    log_x=True,
    title="Premium Concentration Around Key Rolex Sports References",
    labels={
        "listing_count": "Listing count, log scale",
        "median_premium": "Median resale premium (%)",
        "segment": ""
    }
)

fig.update_traces(
    hovertemplate=(
        "<b>%{customdata[0]} — %{customdata[1]}</b>"
        "<br>Collection: %{customdata[2]}"
        "<br>Historical listings: %{customdata[3]:,.0f}"
        "<br>Median resale premium: %{customdata[4]:.1f}%"
        "<br>Median listing price: %{customdata[5]:,.0f}"
        "<extra></extra>"
    )
)

fig.add_hline(
    y=50,
    line_dash="dash",
    annotation_text="High premium zone",
    annotation_position="top left"
)

fig.update_layout(height=650)

st.plotly_chart(fig, use_container_width=True)

st.caption(
    "**Interpretation note:** The 50% premium threshold is an illustrative "
    "benchmark used to highlight references with particularly elevated "
    "asking-price premiums. It is not an industry-standard definition "
    "of speculative behavior."
)

st.markdown("""
**Insight:** A small number of predefined key sports / hype references sit clearly above the broader reference market in resale premium. 
However, these references span very different listing volumes, suggesting that extreme premium is concentrated in specific reference identities rather than simply in the most frequently listed watches.
""")

st.divider()

# =========================
# CHART 2: TOP PREMIUM REFERENCES
# =========================
st.header("Extreme Premium References")

top_refs = (
    reference_metrics
    .sort_values("median_premium", ascending=False)
    .head(12)
    .copy()
)

top_refs["reference"] = top_refs["reference"].astype(str)
plot_top_refs = top_refs.sort_values("median_premium", ascending=True).copy()
reference_order = plot_top_refs["reference"].tolist()

fig = px.bar(
    plot_top_refs,
    x="median_premium",
    y="reference",
    color="segment",
    orientation="h",
    text="median_premium",
    title="Top Rolex References by Median Resale Premium",
    labels={
        "median_premium": "Median premium (%)",
        "reference": "Reference",
        "model_description": "Rolex model",
        "segment": ""
    },
    hover_data={
        "model_description": True,
        "collection": True,
        "listing_count": True,
        "median_price": ":,.0f",
        "median_premium": ":.1f",
        "reference": False
    },
    category_orders={"reference": reference_order}
)

fig.update_traces(texttemplate="%{x:.1f}", textposition="outside")
fig.update_layout(
    height=650,
    yaxis=dict(type="category", categoryorder="array", categoryarray=reference_order)
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("""
**Insight:** The highest resale premiums are strongly represented among the predefined key sports / hype references, including Daytona, GMT-Master II and Submariner models. 
However, several other references also reach relatively high premiums, showing that the distinction is one of concentration rather than an absolute separation between hype and non-hype references.
""")

# Visible reference-to-model guide for presentation and PDF export.
with st.expander("Rolex reference guide", expanded=True):
    reference_guide = top_refs[
        ["reference", "model_description", "segment", "median_premium"]
    ].rename(columns={
        "reference": "Reference",
        "model_description": "Model / Configuration",
        "segment": "Segment",
        "median_premium": "Median Premium (%)"
    })
    st.dataframe(
        reference_guide,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Median Premium (%)": st.column_config.NumberColumn(
                "Median Premium (%)", format="%.1f"
            )
        }
    )


# =========================
# CHART 3: Collection Market Presence vs Premium
# =========================
st.header("Collection Market Presence vs Premium")

collection_metrics = (
    hist_df
    .groupby("collection", as_index=False)
    .agg(
        listing_count=("premium_pct", "count"),
        median_premium=("premium_pct", "median"),
        median_price=("price", "median")
    )
)

collection_metrics = collection_metrics[
    collection_metrics["listing_count"] >= 100
].copy()

fig = px.scatter(
    collection_metrics,
    x="listing_count",
    y="median_premium",
    size="median_price",
    hover_name="collection",
    text="collection",
    log_x=True,
    title="Rolex Collection Listing Volume vs Resale Premium",
    labels={
        "listing_count": "Listing volume, log scale",
        "median_premium": "Median premium (%)",
        "median_price": "Median price"
    }
)

fig.update_traces(textposition="top center")
fig.update_layout(height=650)

st.plotly_chart(fig, use_container_width=True)

st.markdown("""
**Insight:** Listing volume and resale premium do not necessarily move together at the collection level. 
Highly represented collections such as Datejust and Day-Date do not show the strongest premiums, while GMT-Master II and Submariner achieve substantially higher premiums at lower listing volumes. 
This suggests that market presence alone does not explain premium formation.
""")

st.divider()

# =========================
# CHART 4: HYPE REFERENCES VS OTHERS
# =========================
st.header("Hype References vs Other References")

st.caption(
    "**Reference selection:** Eight recognizable Rolex sports and "
    "collector-oriented references were selected for exploratory comparison, "
    "informed by recognizable configurations and initial market exploration. "
    "This is a researcher-defined group, not an exhaustive or independently "
    "validated classification of market hype."
)

segment_summary = (
    reference_metrics
    .groupby("segment", as_index=False)
    .agg(
        reference_count=("reference", "nunique"),
        median_premium=("median_premium", "median"),
        median_listing_count=("listing_count", "median"),
        median_price=("median_price", "median")
    )
)

fig = px.bar(
    segment_summary,
    x="segment",
    y="median_premium",
    text=segment_summary["median_premium"].round(1),
    title="Median Premium: Hype References vs Other References",
    labels={
        "segment": "",
        "median_premium": "Median premium (%)"
    }
)

fig.update_traces(textposition="outside")
fig.update_layout(height=500)

st.plotly_chart(fig, use_container_width=True)

st.markdown("""
**Insight:** The predefined key sports / hype references show substantially higher
median resale premiums than the rest of the reference universe (108.5% vs 24.8%).
This suggests that resale premium is concentrated around a limited set of
specific sports references.
""")

with st.expander("Hype reference summary"):
    st.dataframe(segment_summary, use_container_width=True)

st.divider()

# =========================
# LIVE MARKET VALIDATION
# =========================
st.header("Current Market Cross-Check from Chrono24 Scraping")

live_df = live_df.copy()

live_df["premium_pct"] = pd.to_numeric(live_df["premium_pct"], errors="coerce")
live_df["price"] = pd.to_numeric(live_df["price"], errors="coerce")

# Choose best available collection column
if "detected_collection" in live_df.columns:
    live_collection_col = "detected_collection"
elif "collection" in live_df.columns:
    live_collection_col = "collection"
else:
    live_collection_col = None

if live_collection_col is not None:
    live_clean = live_df.dropna(
        subset=[live_collection_col, "premium_pct", "price"]
    ).copy()

    live_clean = live_clean[
        (live_clean["premium_pct"] > -80) &
        (live_clean["premium_pct"] < 300)
    ].copy()

    if not live_clean.empty:
        live_collection_metrics = (
            live_clean
            .groupby(live_collection_col, as_index=False)
            .agg(
                listing_count=("premium_pct", "count"),
                median_premium=("premium_pct", "median"),
                median_price=("price", "median")
            )
            .sort_values("listing_count", ascending=False)
        )

        fig = px.bar(
            live_collection_metrics.sort_values("median_premium", ascending=True),
            x="median_premium",
            y=live_collection_col,
            orientation="h",
            text=live_collection_metrics.sort_values("median_premium", ascending=True)["median_premium"].round(1),
            title="Live Chrono24 Rolex Premium by Collection",
            labels={
                "median_premium": "Median premium (%)",
                live_collection_col: "Collection"
            }
        )

        fig.update_traces(textposition="outside")
        fig.update_layout(height=550)

        st.plotly_chart(fig, use_container_width=True)

        st.markdown("""
        **Insight:** The live Chrono24 sample provides a current-market cross-check rather
        than a direct replication of the historical analysis. Some higher-premium patterns
        remain visible, particularly for GMT-Master II and Submariner, while the magnitude
        and ranking of premiums differ across collections.
        """)

        with st.expander("Live collection-level data"):
            st.dataframe(live_collection_metrics, use_container_width=True)
    else:
        st.warning("Live Rolex dataset is empty after premium filtering.")
else:
    st.warning("No collection column found in the live Rolex dataset.")

st.divider()

# =========================
# DATA TABLE
# =========================
with st.expander("Reference-level data"):
    st.dataframe(
        reference_metrics.sort_values("median_premium", ascending=False),
        use_container_width=True
    )