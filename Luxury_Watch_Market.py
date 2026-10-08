import streamlit as st

st.set_page_config(
    page_title="Luxury Watch Secondary Market Intelligence",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.title("Luxury Watch Secondary Market Intelligence")

st.header("Project objective")

st.markdown("""
How are market presence, public attention, and resale premiums
distributed across the luxury watch secondary market?

This project explores three connected questions:

1. How is the secondary market structured across brands,
   price segments, and public attention?
2. Which Rolex product characteristics are associated with
   higher resale premiums?
3. To what extent are exceptional premiums concentrated
   among selected Rolex sports and collector-oriented references?
""")

st.header("Analytical approach")

st.markdown("""
The analysis moves from the broader luxury watch market
to a focused Rolex case study.

Rolex provides a useful case for examining how product
configuration, reference identity, and market visibility
relate to resale pricing.

**Resale premium** is defined as the percentage difference
between an observed secondary-market listing price and
a reference retail price (RRP).

The project uses listing prices rather than confirmed
transaction prices. Its findings therefore describe
asking-price patterns and market presence, not realized
investment returns or proven causal relationships.
""")

st.header("Dashboard structure")

st.markdown("""
**Page 1 — Market Concentration**

Explores historical brand-level listing concentration,
price positioning, Google Trends attention, and
standardized eBay API retrieval saturation.

**Page 2 — Rolex Premium Formation**

Examines how material, dial color, complication,
and production period relate to resale premiums.
Historical daily listing observations are also used
to analyze listing visibility and persistence.

**Page 3 — Speculative References**

Investigates reference-level premium concentration,
including an exploratory comparison of selected
sports and collector-oriented Rolex references.
A current Chrono24 sample provides an additional
market cross-check.

**Page 4 — Data Pipeline**

Documents the data sources, Python preparation
processes, SQLite storage, FastAPI endpoints,
and Streamlit architecture.
""")
