import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Rolex Premium Formation",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "processed"

# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_premium_data():
    return pd.read_csv(
        DATA_DIR / "rolex_premium_analysis.csv",
        low_memory=False
    )

@st.cache_data
def load_visibility_data():
    listing_path = DATA_DIR / "rolex_listing_visibility.csv"
    collection_path = DATA_DIR / "rolex_visibility_by_collection.csv"

    listing_df = pd.read_csv(listing_path)
    collection_df = pd.read_csv(collection_path)

    return listing_df, collection_df


df = load_premium_data().copy()

# =========================
# CLEANING
# =========================
df["premium_pct"] = pd.to_numeric(df["premium_pct"], errors="coerce")
df["price"] = pd.to_numeric(df["price"], errors="coerce")
df["rrp_clean"] = pd.to_numeric(df["rrp_clean"], errors="coerce")

df = df.dropna(subset=["collection", "premium_pct"]).copy()

# Mainstream premium range
df = df[
    (df["premium_pct"] > -80) &
    (df["premium_pct"] < 300)
].copy()

df["material"] = df["material_clean"]
df["dial_color"] = df["dial_color_clean"]
df["watch_type"] = df["segment"]

# =========================
# TITLE
# =========================
st.title("2. Rolex Premium Formation")

st.markdown("""
This page uses Rolex as a case study to understand what drives resale premium.

The analysis focuses on whether Rolex resale premiums are mainly explained by material value,
or by desirability signals such as sports identity, dial color, modern production period,
and specific technical configurations.
""")

st.info("""
Methodological note: this page uses a historical daily Rolex listing dataset.
Because the same listing can appear across multiple days, the results should be interpreted as
visibility-weighted premium patterns, not as a count of unique watches.
""")

# =========================
# KPI
# =========================
sports_median = df.loc[df["watch_type"] == "Sports", "premium_pct"].median()
classic_median = df.loc[df["watch_type"] == "Classic", "premium_pct"].median()
overall_median = df["premium_pct"].median()

c1, c2, c3 = st.columns(3)

c1.metric("Visibility-weighted Median Premium", f"{overall_median:.1f}%")
c2.metric("Sports Median Premium", f"{sports_median:.1f}%")
c3.metric("Classic Median Premium", f"{classic_median:.1f}%")

st.divider()

# =========================
# 1. SPORTS VS CLASSIC
# =========================
st.header("Sports Identity Creates Stronger Premiums")

fig = px.box(
    df,
    x="watch_type",
    y="premium_pct",
    points="outliers",
    category_orders={"watch_type": ["Classic", "Sports"]},
    labels={
        "watch_type": "Rolex Segment",
        "premium_pct": "Resale Premium (%)"
    },
    title="Sports vs Classic Rolex Premium Distribution"
)

fig.update_layout(height=550)

st.plotly_chart(fig, use_container_width=True)

st.markdown("""
**Insight:** Sports-oriented Rolex watches show stronger and more dispersed resale
premiums than classic models.

This suggests that resale premium is associated not only with material characteristics,
but also with the market positioning and desirability of sports references.
""")

st.divider()

# =========================
# 2. MATERIAL
# =========================
st.header("Material Does Not Fully Explain Premium")

material_df = (
    df.dropna(subset=["material"])
    .groupby("material", as_index=False)
    .agg(
        median_premium=("premium_pct", "median"),
        listing_count=("premium_pct", "count")
    )
)

material_order = [
    "Steel",
    "Platinum",
    "Yellow Gold",
    "Two-tone",
    "Rose Gold",
    "White Gold"
]

material_df = material_df[material_df["listing_count"] >= 100].copy()
material_df["material"] = pd.Categorical(
    material_df["material"],
    categories=material_order,
    ordered=True
)
material_df = material_df.sort_values("material")

fig = px.bar(
    material_df,
    x="material",
    y="median_premium",
    text=material_df["median_premium"].round(1),
    labels={
        "material": "Material",
        "median_premium": "Median Premium (%)"
    },
    title="Median Resale Premium by Material"
)

fig.update_traces(textposition="outside")
fig.update_layout(height=520)

st.plotly_chart(fig, use_container_width=True)

st.markdown("""
**Insight:** Precious metals do not automatically generate stronger resale premiums.
Steel performs strongly in the observed market, while some precious-metal categories
show lower median premiums.

This suggests that material alone does not explain resale premium,
and that other product and market characteristics also contribute to premium formation.
""")

st.divider()

# =========================
# 3. DIAL COLOR
# =========================
st.header("Dial Color as a Desirability Signal")

dial_df = (
    df.dropna(subset=["dial_color"])
    .groupby("dial_color", as_index=False)
    .agg(
        median_premium=("premium_pct", "median"),
        listing_count=("premium_pct", "count")
    )
)

dial_df = (
    dial_df[dial_df["listing_count"] >= 300]
    .sort_values("median_premium", ascending=False)
)

fig = px.bar(
    dial_df,
    x="dial_color",
    y="median_premium",
    text=dial_df["median_premium"].round(1),
    labels={
        "dial_color": "Dial Color",
        "median_premium": "Median Premium (%)"
    },
    title="Median Resale Premium by Dial Color"
)

fig.update_traces(textposition="outside")
fig.update_layout(height=520)

st.plotly_chart(fig, use_container_width=True)

st.markdown("""
**Insight:** Dial color is associated with meaningful differences in resale premium.
Green dials stand out with the highest median premium in the dataset, well above
the other major color categories.

This suggests that visual configuration and product desirability can contribute to
premium formation beyond material characteristics alone.
""")

st.divider()

# =========================
# 4. MATERIAL × PRODUCTION PERIOD
# =========================
st.header("Material × Production Period")

year_order = [
    "Before 2000",
    "2000–2004",
    "2005–2009",
    "2010–2014",
    "2015–2019",
    "2020+"
]

period_df = df.dropna(subset=["material", "year_bucket"]).copy()

period_grouped = (
    period_df
    .groupby(["material", "year_bucket"], as_index=False)
    .agg(
        median_premium=("premium_pct", "median"),
        listing_count=("premium_pct", "count")
    )
)

period_grouped = period_grouped[period_grouped["listing_count"] >= 100]

fig = px.density_heatmap(
    period_grouped,
    x="year_bucket",
    y="material",
    z="median_premium",
    text_auto=".0f",
    category_orders={
        "year_bucket": year_order,
        "material": material_order
    },
    color_continuous_scale="RdYlGn",
    labels={
        "year_bucket": "Production Period",
        "material": "Material",
        "median_premium": "Median Premium (%)"
    },
    title="Median Resale Premium by Material and Production Period"
)

fig.update_layout(height=620)

st.plotly_chart(fig, use_container_width=True)

st.markdown("""
**Insight:** Premium expansion is concentrated in more recent production periods,
particularly after 2015, with the pattern appearing across several material categories.

Together with the reference-level concentration examined in the next section of the project,
this suggests that modern Rolex references — particularly highly recognizable sports models —
can display scarcity- and speculation-like pricing patterns.
""")

st.divider()

# =========================
# 5. MATERIAL × COMPLICATION
# =========================
st.header("Configuration Effects: Material × Complication")

config_df = df.dropna(subset=["material", "complication_type"]).copy()

config_grouped = (
    config_df
    .groupby(["material", "complication_type"], as_index=False)
    .agg(
        median_premium=("premium_pct", "median"),
        listing_count=("premium_pct", "count")
    )
)

config_grouped = config_grouped[config_grouped["listing_count"] >= 1000]

complication_order = [
    "Annual Calendar",
    "Chronograph",
    "Date",
    "Diver",
    "GMT",
    "Simple Time"
]

fig = px.density_heatmap(
    config_grouped,
    x="complication_type",
    y="material",
    z="median_premium",
    text_auto=".0f",
    category_orders={
        "complication_type": complication_order,
        "material": material_order
    },
    color_continuous_scale="RdYlGn",
    labels={
        "complication_type": "Complication Type",
        "material": "Material",
        "median_premium": "Median Premium (%)"
    },
    title="Median Resale Premium by Material and Complication Type"
)

fig.update_layout(height=650)

st.plotly_chart(fig, use_container_width=True)

st.markdown("""
**Insight:** Premium formation is configuration-driven rather than purely material-driven.
The strongest premiums appear in steel chronograph and steel GMT configurations,
two combinations closely associated with highly recognizable Rolex sports references.

Together with the reference-level analysis, this supports the idea that iconic,
high-demand configurations can command stronger premiums than material value alone would suggest.
""")

st.divider()

# =========================
# 6. LISTING VISIBILITY
# =========================
st.header("Listing Visibility and Market Persistence")

st.markdown("""
The daily Rolex dataset contains repeated listings because active listings remain visible across several days.
Instead of treating this only as duplication, this section uses listing URL as an identifier
to measure market visibility persistence.

This should not be interpreted as confirmed time-to-sale. It is a proxy for how long listings remain visible
in the secondary market.
""")

listing_df, visibility_df = load_visibility_data()

# -------------------------
# 6.1 Average visibility by collection
# -------------------------
st.subheader("Average Visibility Duration by Collection")

plot_visibility_df = visibility_df.sort_values(
    "avg_visibility_days",
    ascending=True
).copy()

fig = px.bar(
    plot_visibility_df,
    x="avg_visibility_days",
    y="collection",
    orientation="h",
    text=plot_visibility_df["avg_visibility_days"].round(1),
    title="Average Listing Visibility Duration by Collection",
    labels={
        "avg_visibility_days": "Average visibility days",
        "collection": "Collection"
    }
)

fig.update_traces(textposition="outside")
fig.update_layout(height=550)

st.plotly_chart(fig, use_container_width=True)

st.markdown("""
**Insight:** Average visibility duration is relatively similar across major Rolex collections.
This suggests that the daily dataset is broadly visibility-weighted across the whole Rolex market,
rather than only one isolated collection.
""")

with st.expander("Collection-level visibility data"):
    st.dataframe(visibility_df, use_container_width=True)

st.divider()

# -------------------------
# 6.2 Visibility distribution
# -------------------------
st.subheader("Distribution of Listing Visibility Duration")

listing_df["visibility_days"] = pd.to_numeric(
    listing_df["visibility_days"],
    errors="coerce"
)

listing_df = listing_df.dropna(subset=["visibility_days"]).copy()

listing_df["visibility_bucket"] = pd.cut(
    listing_df["visibility_days"],
    bins=[0, 1, 3, 7, 14, float("inf")],
    labels=[
        "1 day",
        "2–3 days",
        "4–7 days",
        "8–14 days",
        "15+ days"
    ],
    include_lowest=True
)

bucket_order = [
    "1 day",
    "2–3 days",
    "4–7 days",
    "8–14 days",
    "15+ days"
]

bucket_df = (
    listing_df
    .groupby("visibility_bucket", observed=False)
    .size()
    .reset_index(name="listing_count")
)

bucket_df["visibility_bucket"] = pd.Categorical(
    bucket_df["visibility_bucket"],
    categories=bucket_order,
    ordered=True
)

bucket_df = bucket_df.sort_values("visibility_bucket")

fig = px.bar(
    bucket_df,
    x="visibility_bucket",
    y="listing_count",
    text="listing_count",
    title="Distribution of Listing Visibility Duration",
    labels={
        "visibility_bucket": "Visibility duration",
        "listing_count": "Number of unique listings"
    }
)

fig.update_traces(textposition="outside")
fig.update_layout(height=500)

st.plotly_chart(fig, use_container_width=True)

st.markdown("""
**Insight:** A large share of Rolex listings remain visible for more than one week,
showing substantial persistence in the observed secondary-market inventory.

This does not represent confirmed time-to-sale, but persistent visibility may be
consistent with slower market absorption, relisting behavior, seller price expectations,
or speculative inventory.
""")

st.divider()

# -------------------------
# 6.3 Visibility duration vs premium
# -------------------------
st.subheader("Visibility Duration vs Premium")

listing_df["median_premium"] = pd.to_numeric(
    listing_df["median_premium"],
    errors="coerce"
)

premium_visibility_df = (
    listing_df
    .dropna(subset=["visibility_bucket", "median_premium"])
    .groupby("visibility_bucket", observed=False)
    .agg(
        median_premium=("median_premium", "median"),
        listing_count=("url", "nunique")
    )
    .reset_index()
)

premium_visibility_df["visibility_bucket"] = pd.Categorical(
    premium_visibility_df["visibility_bucket"],
    categories=bucket_order,
    ordered=True
)

premium_visibility_df = premium_visibility_df.sort_values("visibility_bucket")

fig = px.bar(
    premium_visibility_df,
    x="visibility_bucket",
    y="median_premium",
    text=premium_visibility_df["median_premium"].round(1),
    title="Median Premium by Listing Visibility Duration",
    labels={
        "visibility_bucket": "Visibility duration",
        "median_premium": "Median resale premium (%)"
    }
)

fig.update_traces(textposition="outside")
fig.update_layout(height=500)

st.plotly_chart(fig, use_container_width=True)

st.markdown("""
**Insight:** Listings visible for more than one week show higher median premiums
than those observed for seven days or less.

This suggests that higher premiums do not necessarily coincide with rapid disappearance
from the observed market. While visibility is not confirmed time-to-sale, the pattern
is consistent with slower absorption or more persistent seller pricing among
higher-premium listings.
""")

with st.expander("Visibility duration × premium data"):
    st.dataframe(premium_visibility_df, use_container_width=True)