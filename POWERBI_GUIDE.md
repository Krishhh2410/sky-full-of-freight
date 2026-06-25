# Power BI Dashboard Guide
## Sky Full of Freight — Air Cargo Analysis

This guide walks through building the full 3-page dashboard in Power BI Desktop.
The 3 CSV files to load are in the `data/` folder.

---

## Step 1 — Import the Data

1. Open **Power BI Desktop** → `Home → Get Data → Text/CSV`
2. Import all three files:
   - `monthly_cargo_powerbi.csv` → rename to `MonthlyData`
   - `airline_clusters.csv`      → rename to `AirlineClusters`
   - `cargo_master.csv`          → rename to `RawMaster` (optional, for drillthrough)

3. In Power Query for `MonthlyData`:
   - Confirm `Date` column is set to **Date** type
   - Confirm `Cargo_Tons` is **Decimal Number**
   - Confirm `Year`, `Month` are **Whole Number**
   - Click **Close & Apply**

---

## Step 2 — Create Relationships

Go to **Model view**:
- `MonthlyData[Operating Airline]` → `AirlineClusters[Operating Airline]`
- Cardinality: Many-to-One | Cross filter: Both

---

## Step 3 — Key DAX Measures

Create a new **Measures table** (Enter Data → blank table named `_Measures`).

Paste each of these:

```dax
Total Cargo Tons = SUM(MonthlyData[Cargo_Tons])

Avg Monthly Tons = AVERAGEX(
    VALUES(MonthlyData[Date]),
    CALCULATE(SUM(MonthlyData[Cargo_Tons]))
)

Freighter % = 
DIVIDE(
    CALCULATE(SUM(MonthlyData[Cargo_Tons]), MonthlyData[Cargo Aircraft Type] = "Freighter"),
    SUM(MonthlyData[Cargo_Tons])
) * 100

International % =
DIVIDE(
    CALCULATE(SUM(MonthlyData[Cargo_Tons]), MonthlyData[GEO Summary] = "International"),
    SUM(MonthlyData[Cargo_Tons])
) * 100

YoY Growth % = 
VAR CurrentYear = CALCULATE(SUM(MonthlyData[Cargo_Tons]), YEAR(MonthlyData[Date]) = MAX(YEAR(MonthlyData[Date])))
VAR PriorYear   = CALCULATE(SUM(MonthlyData[Cargo_Tons]), YEAR(MonthlyData[Date]) = MAX(YEAR(MonthlyData[Date])) - 1)
RETURN DIVIDE(CurrentYear - PriorYear, PriorYear) * 100

Airlines Count = DISTINCTCOUNT(MonthlyData[Operating Airline])
```

---

## Step 4 — Page 1: Executive Overview

**Canvas size**: 1280 × 720 (widescreen)  
**Theme**: Use the dark theme JSON file `powerbi_theme.json` via  
`View → Themes → Browse for themes`

### Layout:

```
┌──────────────────────────────────────────────────────────────────┐
│  [Title] Sky Full of Freight — SFO Air Cargo Intelligence        │
│  [Subtitle] 2000–2023 | 127 Airlines | 12.3M Metric Tons         │
├───────────┬───────────┬──────────────┬───────────────────────────┤
│ Total Tons│ Airlines  │ Freighter %  │ International %           │
│  KPI Card │  KPI Card │   KPI Card   │    KPI Card               │
├───────────┴───────────┴──────────────┴───────────────────────────┤
│                                                                  │
│  [Line Chart] Annual Cargo Volume (2000–2023) — full width       │
│                                                                  │
├──────────────────────────────┬───────────────────────────────────┤
│  [Bar Chart]                 │  [Donut Chart]                    │
│  Top 10 Airlines by Volume   │  Cargo by Type (Cargo/Mail/Expr)  │
└──────────────────────────────┴───────────────────────────────────┘
```

### Visuals:

**KPI Cards** (4 cards across top):
- `[Total Cargo Tons]` — label: "Total Cargo Handled"
- `[Airlines Count]` — label: "Airlines Analyzed"
- `[Freighter %]` format: 0.0% — label: "Freighter Share"
- `[International %]` format: 0.0% — label: "International Routes"

**Line Chart** — Annual Volume:
- X-axis: `Year` (from MonthlyData)
- Y-axis: `[Total Cargo Tons]`
- Add a constant line at 2009 (red, dashed, label "Financial Crisis")
- Add a constant line at 2020 (purple, dashed, label "COVID")
- Line color: `#F5A623` | Enable area shading

**Clustered Bar Chart** — Top Airlines:
- Y-axis: `Operating Airline`
- X-axis: `[Total Cargo Tons]`
- Filter: Top N = 10 by `[Total Cargo Tons]`
- Sort: Descending | Bar color: `#4A9EFF`

**Donut Chart** — Cargo Type:
- Legend: `Cargo Type Code`
- Values: `[Total Cargo Tons]`
- Colors: Cargo=#F5A623, Mail=#4A9EFF, Express=#52C41A

**Slicer** (top right): Year range (slider)

---

## Step 5 — Page 2: Route & Regional Deep Dive

```
┌──────────────────────────────────────────────────────────────────┐
│  Slicers: [Year Range] [GEO Region] [Aircraft Type] [Cargo Type] │
├──────────────────────────────┬───────────────────────────────────┤
│  [Stacked Area Chart]        │  [Bar Chart]                      │
│  Monthly trend by Aircraft   │  Cargo by GEO Region             │
│  Type (Freighter/PAX/Combi)  │                                   │
├──────────────────────────────┴───────────────────────────────────┤
│  [Clustered Bar]                  │  [Matrix Table]              │
│  Enplaned vs Deplaned by Region   │  Airline × Year pivot        │
└───────────────────────────────────┴──────────────────────────────┘
```

**Stacked Area Chart** — Monthly trend:
- X-axis: `Date`
- Y-axis: `[Total Cargo Tons]`
- Legend: `Cargo Aircraft Type`
- Colors: Freighter=#F5A623, Passenger=#4A9EFF, Combi=#52C41A

**Clustered Bar** — GEO Region:
- X-axis: `GEO Region`
- Y-axis: `[Total Cargo Tons]`
- Sort descending

**Clustered Bar** — Enplaned vs Deplaned:
- X-axis: `GEO Summary`
- Y-axis: `[Total Cargo Tons]`
- Legend: `Activity Type Code`
- Colors: Enplaned=#F5A623, Deplaned=#4A9EFF

**Matrix Table**:
- Rows: `Operating Airline`
- Columns: `Year`
- Values: `[Total Cargo Tons]`
- Conditional formatting: color scale (white → amber)
- Filter: Top 20 airlines by total

---

## Step 6 — Page 3: Cluster Intelligence

```
┌──────────────────────────────────────────────────────────────────┐
│  [Cluster Slicer]  Select cluster to filter all visuals          │
├──────────────────────────────┬───────────────────────────────────┤
│  [Donut]                     │  [Card] Count of airlines         │
│  Airlines per Cluster        │  in selected cluster              │
├──────────────────────────────┴───────────────────────────────────┤
│  [Scatter Plot]                                                  │
│  X: Intl_Share  Y: Avg_Monthly_Tons  Color: Cluster_Label        │
│  Size: Total_Tons                                                │
├──────────────────────────────────────────────────────────────────┤
│  [Clustered Bar] Avg metrics per cluster (4 features side-by-    │
│   side: Freighter Share / Intl Share / Balance Ratio / Avg Tons) │
├──────────────────────────────────────────────────────────────────┤
│  [Text Box] Business Interpretation per cluster (static text)   │
└──────────────────────────────────────────────────────────────────┘
```

**Donut Chart** — Cluster distribution:
- Legend: `Cluster_Label` (from AirlineClusters)
- Values: Count of `Operating Airline`

**Scatter Plot**:
- X-axis: `Intl_Share` (from AirlineClusters)
- Y-axis: `Avg_Monthly_Tons`
- Size: `Total_Tons`
- Color legend: `Cluster_Label`
- Enable data labels → airline name (abbreviate)

**Clustered Bar** — Feature comparison across clusters:
- Create 4 separate bar charts (one per feature) arranged in a 2×2 grid
- Each chart: X-axis = `Cluster_Label`, Y-axis = the feature column

**Text Box** — paste this business interpretation:

> **Dominant Carriers** — United, FedEx, UPS: high total volume, mixed domestic/international.
> Consistently high capacity utilization. Priority: maintain efficiency, monitor route saturation.
>
> **High-Volume Regional** — Strong domestic presence, moderate tonnage.
> Opportunity to expand international belly cargo partnerships.
>
> **Specialized Freighters** — Nearly 100% freighter aircraft, often international-focused.
> Niche but critical for time-sensitive freight. Watch for capacity constraints in peak months.
>
> **Niche / Seasonal Operators** — Low average volume, inconsistent activity periods.
> Candidates for capacity partnerships or route consolidation review.

---

## Step 7 — Formatting Tips (makes it look pro)

1. **Background**: Set page background to `#0F1117` (hex) — `View → Page background`
2. **All visual backgrounds**: `#1A1D2E`, border: `#2D3250`, rounded corners: 4px
3. **Title font**: Segoe UI Semibold, 16pt, `#FFFFFF`
4. **Data labels**: `#C8CCD4`, 9pt
5. **Grid lines**: `#2D3250`, 0.5pt
6. **Remove all visual headers** (the "..." button) for screenshots
7. Use the **Selection pane** to name every visual — easier to manage

---

## Step 8 — Publishing

1. `File → Publish → Publish to Power BI`
2. Sign in with your Microsoft account (free tier works)
3. Copy the shareable link
4. Add link to GitHub README under "Dashboard"
5. Take 3 screenshots of the dashboard pages and put them in `assets/` folder

---

## Files Reference

| File | Use in Power BI | Rows |
|------|----------------|------|
| `monthly_cargo_powerbi.csv` | Main fact table for all charts | 52,521 |
| `airline_clusters.csv` | Cluster dimension table | 104 |
| `cargo_master.csv` | Optional — detailed drillthrough | 52,557 |
