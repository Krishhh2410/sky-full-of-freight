"""
Sky Full of Freight — Air Cargo Analysis & Clustering
=====================================================
Author  : Krish Shah
Dataset : Air Traffic Cargo Statistics (SFO, 1999–2023)
Purpose : EDA + K-Means Clustering to segment airlines by cargo behaviour,
          export cleaned data for Power BI dashboard.

Run this script once — it generates:
  ../data/cargo_cleaned.csv
  ../data/cargo_master.csv
  ../data/monthly_cargo_powerbi.csv
  ../data/airline_clusters.csv
  ../outputs/01_cargo_trend.png  … 08_cluster_profiles.png
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import warnings
warnings.filterwarnings('ignore')

# ──────────────────────────────────────────────
# 0. Plot style
# ──────────────────────────────────────────────
plt.rcParams.update({
    'figure.facecolor': '#0f1117',
    'axes.facecolor':   '#1a1d2e',
    'axes.edgecolor':   '#2d3250',
    'axes.labelcolor':  '#c8ccd4',
    'xtick.color':      '#8b8fa8',
    'ytick.color':      '#8b8fa8',
    'text.color':       '#e0e3ed',
    'grid.color':       '#2d3250',
    'grid.linewidth':   0.6,
    'font.family':      'DejaVu Sans',
    'axes.titlesize':   13,
    'axes.labelsize':   11,
    'xtick.labelsize':  9,
    'ytick.labelsize':  9,
})

ACCENT  = '#f5a623'
BLUE    = '#4a9eff'
GREEN   = '#52c41a'
RED     = '#ff4757'
PURPLE  = '#a55eea'
PALETTE = [ACCENT, BLUE, GREEN, RED, PURPLE, '#26de81', '#fd9644', '#45aaf2']

OUT = '../outputs'
DATA = '../data'


# ──────────────────────────────────────────────
# 1. Load & Clean
# ──────────────────────────────────────────────
print("[1] Loading dataset …")
df = pd.read_csv('../data/cargo_cleaned.csv')
df['Activity Period Start Date'] = pd.to_datetime(df['Activity Period Start Date'])

print(f"    Rows: {len(df):,}  |  Airlines: {df['Operating Airline'].nunique()}"
      f"  |  Years: {df['Year'].min()}–{df['Year'].max()}")


# ──────────────────────────────────────────────
# 2. EDA — Chart 1: Yearly cargo trend
# ──────────────────────────────────────────────
print("[2] EDA charts …")

yearly = df.groupby('Year')['Cargo Metric TONS'].sum().reset_index()

fig, ax = plt.subplots(figsize=(14, 5))
ax.fill_between(yearly['Year'], yearly['Cargo Metric TONS'] / 1e6, alpha=0.18, color=ACCENT)
ax.plot(yearly['Year'], yearly['Cargo Metric TONS'] / 1e6,
        color=ACCENT, linewidth=2.5, marker='o', markersize=4)
ax.axvline(2009, color=RED,    linestyle='--', lw=1, alpha=0.7, label='2009 Financial Crisis')
ax.axvline(2020, color=PURPLE, linestyle='--', lw=1, alpha=0.7, label='COVID-19 Disruption')
ax.set_title('Total Air Cargo Volume — SFO (2000–2023)',
             pad=15, fontsize=14, fontweight='bold', color='white')
ax.set_xlabel('Year')
ax.set_ylabel('Cargo Volume (Million Metric Tons)')
ax.legend(framealpha=0.2, facecolor='#1a1d2e')
ax.yaxis.grid(True); ax.set_axisbelow(True)
plt.tight_layout()
plt.savefig(f'{OUT}/01_cargo_trend.png', dpi=150, bbox_inches='tight', facecolor='#0f1117')
plt.close()


# Chart 2: Top 15 airlines
top15 = df.groupby('Operating Airline')['Cargo Metric TONS'].sum().nlargest(15).sort_values()
colors = [ACCENT if x == top15.max() else BLUE for x in top15.values]

fig, ax = plt.subplots(figsize=(12, 7))
bars = ax.barh(top15.index, top15.values / 1e6, color=colors, edgecolor='none', height=0.7)
for bar, val in zip(bars, top15.values):
    ax.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height() / 2,
            f'{val/1e6:.1f}M', va='center', color='#8b8fa8', fontsize=8.5)
ax.set_title('Top 15 Airlines by Total Cargo Tonnage (2000–2023)',
             pad=15, fontsize=14, fontweight='bold', color='white')
ax.set_xlabel('Total Cargo (Million Metric Tons)')
ax.xaxis.grid(True); ax.set_axisbelow(True)
plt.tight_layout()
plt.savefig(f'{OUT}/02_top_airlines.png', dpi=150, bbox_inches='tight', facecolor='#0f1117')
plt.close()


# Chart 3: Cargo type pie + GEO bar
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
ct = df.groupby('Cargo Type Code')['Cargo Metric TONS'].sum()
wedge = dict(width=0.45, edgecolor='#0f1117', linewidth=2)
axes[0].pie(ct.values, labels=ct.index, colors=[ACCENT, BLUE, GREEN],
            autopct='%1.1f%%', wedgeprops=wedge, pctdistance=0.75,
            textprops={'color': 'white', 'fontsize': 10})
axes[0].set_title('Cargo Split by Type', fontsize=13, fontweight='bold', color='white')

geo = df.groupby('GEO Region')['Cargo Metric TONS'].sum().nlargest(8).sort_values()
axes[1].barh(geo.index, geo.values / 1e6,
             color=[PALETTE[i % len(PALETTE)] for i in range(len(geo))],
             height=0.6, edgecolor='none')
axes[1].set_title('Cargo Volume by Geographic Region', fontsize=13, fontweight='bold', color='white')
axes[1].set_xlabel('Total Cargo (Million Metric Tons)')
axes[1].xaxis.grid(True); axes[1].set_axisbelow(True)
plt.tight_layout()
plt.savefig(f'{OUT}/03_cargo_type_geo.png', dpi=150, bbox_inches='tight', facecolor='#0f1117')
plt.close()


# Chart 4: Seasonal heatmap
month_names = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
pivot = df[df['Year'] >= 2010].pivot_table(
    index='Month', columns='Year', values='Cargo Metric TONS', aggfunc='sum') / 1e3

fig, ax = plt.subplots(figsize=(16, 6))
sns.heatmap(pivot, ax=ax, cmap='YlOrRd', linewidths=0.3, linecolor='#0f1117',
            cbar_kws={'label': 'Cargo (1k Metric Tons)', 'shrink': 0.8},
            yticklabels=month_names)
ax.set_title('Monthly Cargo Volume Heatmap (2010–2023)',
             pad=15, fontsize=14, fontweight='bold', color='white')
ax.set_xlabel('Year'); ax.set_ylabel('Month')
ax.tick_params(axis='x', rotation=45)
plt.tight_layout()
plt.savefig(f'{OUT}/04_seasonal_heatmap.png', dpi=150, bbox_inches='tight', facecolor='#0f1117')
plt.close()


# Chart 5: Aircraft type trend
ac_yr = df.groupby(['Year', 'Cargo Aircraft Type'])['Cargo Metric TONS'].sum().reset_index()
fig, ax = plt.subplots(figsize=(14, 5))
for atype, color in zip(['Freighter', 'Passenger', 'Combi'], [ACCENT, BLUE, GREEN]):
    sub = ac_yr[ac_yr['Cargo Aircraft Type'] == atype]
    ax.plot(sub['Year'], sub['Cargo Metric TONS'] / 1e6,
            color=color, linewidth=2, label=atype, marker='o', markersize=3)
ax.set_title('Cargo Volume: Freighter vs Passenger Belly vs Combi',
             pad=15, fontsize=14, fontweight='bold', color='white')
ax.set_xlabel('Year'); ax.set_ylabel('Cargo Volume (Million Metric Tons)')
ax.legend(framealpha=0.2, facecolor='#1a1d2e')
ax.yaxis.grid(True); ax.set_axisbelow(True)
plt.tight_layout()
plt.savefig(f'{OUT}/05_freighter_vs_belly.png', dpi=150, bbox_inches='tight', facecolor='#0f1117')
plt.close()

print("    All 5 EDA charts saved.")


# ──────────────────────────────────────────────
# 3. Feature Engineering for Clustering
# ──────────────────────────────────────────────
print("[3] Building airline-level features …")

agg = df.groupby('Operating Airline').agg(
    Total_Tons          = ('Cargo Metric TONS', 'sum'),
    Avg_Monthly_Tons    = ('Cargo Metric TONS', 'mean'),
    Record_Count        = ('Cargo Metric TONS', 'count'),
    Freighter_Share     = ('Cargo Aircraft Type', lambda x: (x == 'Freighter').sum() / len(x)),
    Intl_Share          = ('GEO Summary', lambda x: (x == 'International').sum() / len(x)),
).reset_index()

enplaned = (df[df['Activity Type Code'] == 'Enplaned']
            .groupby('Operating Airline')['Cargo Metric TONS'].sum().rename('Enplaned'))
deplaned = (df[df['Activity Type Code'] == 'Deplaned']
            .groupby('Operating Airline')['Cargo Metric TONS'].sum().rename('Deplaned'))
bal = pd.concat([enplaned, deplaned], axis=1).fillna(0)
bal['Balance_Ratio'] = bal['Enplaned'] / (bal['Enplaned'] + bal['Deplaned'] + 1)
agg = agg.merge(bal[['Balance_Ratio']].reset_index().rename(columns={'index':'Operating Airline'}),
                on='Operating Airline', how='left')

# Keep only airlines with enough records to cluster meaningfully
agg = agg[agg['Record_Count'] >= 10].copy()
print(f"    Airlines eligible for clustering: {len(agg)}")


# ──────────────────────────────────────────────
# 4. K-Means Clustering
# ──────────────────────────────────────────────
print("[4] Running K-Means …")

FEATURES = ['Avg_Monthly_Tons', 'Freighter_Share', 'Intl_Share', 'Balance_Ratio']
X = agg[FEATURES].fillna(0)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Elbow + silhouette to justify K
wcss, sil = [], []
for k in range(2, 9):
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    km.fit(X_scaled)
    wcss.append(km.inertia_)
    sil.append(silhouette_score(X_scaled, km.labels_))

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
axes[0].plot(range(2,9), wcss, color=ACCENT, lw=2.5, marker='o', ms=6)
axes[0].axvline(4, color=RED, linestyle='--', lw=1.5, alpha=0.8, label='K=4 selected')
axes[0].set_title('WCSS Elbow Curve', fontsize=12, fontweight='bold', color='white')
axes[0].set_xlabel('Number of Clusters (K)'); axes[0].set_ylabel('WCSS (Inertia)')
axes[0].legend(framealpha=0.2, facecolor='#1a1d2e'); axes[0].grid(True)

axes[1].plot(range(2,9), sil, color=BLUE, lw=2.5, marker='s', ms=6)
axes[1].axvline(4, color=RED, linestyle='--', lw=1.5, alpha=0.8, label='K=4 selected')
axes[1].set_title('Silhouette Score by K', fontsize=12, fontweight='bold', color='white')
axes[1].set_xlabel('Number of Clusters (K)'); axes[1].set_ylabel('Silhouette Score')
axes[1].legend(framealpha=0.2, facecolor='#1a1d2e'); axes[1].grid(True)
plt.tight_layout()
plt.savefig(f'{OUT}/06_elbow_silhouette.png', dpi=150, bbox_inches='tight', facecolor='#0f1117')
plt.close()

# Final model: K=4
km4 = KMeans(n_clusters=4, random_state=42, n_init=10)
agg['Cluster'] = km4.fit_predict(X_scaled)

# Label clusters
profiles = agg.groupby('Cluster')[FEATURES + ['Total_Tons']].mean()
sorted_by_vol = profiles['Total_Tons'].sort_values()
rank = {c: i for i, c in enumerate(sorted_by_vol.index)}

labels_map = {}
for c in range(4):
    row = profiles.loc[c]
    if rank[c] == 3:
        labels_map[c] = 'Dominant Carriers'
    elif rank[c] == 2:
        labels_map[c] = 'High-Volume Regional'
    elif row['Freighter_Share'] > 0.4:
        labels_map[c] = 'Specialized Freighters'
    else:
        labels_map[c] = 'Niche / Seasonal Operators'

agg['Cluster_Label'] = agg['Cluster'].map(labels_map)

print("    Cluster distribution:")
for lbl, count in agg['Cluster_Label'].value_counts().items():
    print(f"      {lbl}: {count} airlines")


# Chart 7: Cluster scatter
cluster_colors = {v: PALETTE[i] for i, v in enumerate(labels_map.values())}

fig, ax = plt.subplots(figsize=(12, 7))
for label in agg['Cluster_Label'].unique():
    sub = agg[agg['Cluster_Label'] == label]
    ax.scatter(sub['Intl_Share'], sub['Avg_Monthly_Tons'],
               c=cluster_colors.get(label, '#888'), label=label,
               s=80, alpha=0.8, edgecolors='#0f1117', lw=0.5)
for _, row in agg[agg['Avg_Monthly_Tons'] > 1000].iterrows():
    short = row['Operating Airline'].split()[0]
    ax.annotate(short, (row['Intl_Share'], row['Avg_Monthly_Tons']),
                fontsize=7, color='#c8ccd4', xytext=(4, 4), textcoords='offset points')
ax.set_title('Airline Clusters: International Share vs Avg Monthly Cargo',
             pad=15, fontsize=14, fontweight='bold', color='white')
ax.set_xlabel('International Route Share'); ax.set_ylabel('Avg Monthly Cargo (Metric Tons)')
ax.legend(framealpha=0.2, facecolor='#1a1d2e', fontsize=9)
ax.yaxis.grid(True); ax.xaxis.grid(True); ax.set_axisbelow(True)
plt.tight_layout()
plt.savefig(f'{OUT}/07_cluster_scatter.png', dpi=150, bbox_inches='tight', facecolor='#0f1117')
plt.close()


# Chart 8: Cluster bar profiles
fig, ax = plt.subplots(figsize=(12, 5))
cluster_avg = agg.groupby('Cluster_Label')[FEATURES].mean()
x = np.arange(len(FEATURES))
width = 0.2
for i, (label, color) in enumerate(cluster_colors.items()):
    if label in cluster_avg.index:
        ax.bar(x + i*width, cluster_avg.loc[label].values, width,
               label=label, color=color, alpha=0.85, edgecolor='none')
ax.set_xticks(x + width*1.5)
ax.set_xticklabels(['Avg Monthly Tons\n(norm.)', 'Freighter Share', 'Intl Share', 'Balance Ratio'], fontsize=9)
ax.set_title('Cluster Feature Profiles — Average Values',
             pad=15, fontsize=14, fontweight='bold', color='white')
ax.legend(framealpha=0.2, facecolor='#1a1d2e', fontsize=9)
ax.yaxis.grid(True); ax.set_axisbelow(True)
plt.tight_layout()
plt.savefig(f'{OUT}/08_cluster_profiles.png', dpi=150, bbox_inches='tight', facecolor='#0f1117')
plt.close()

print("    Clustering charts saved.")


# ──────────────────────────────────────────────
# 5. Export for Power BI
# ──────────────────────────────────────────────
print("[5] Exporting Power BI datasets …")

agg.to_csv(f'{DATA}/airline_clusters.csv', index=False)

df_master = df.copy()
cluster_map = agg.set_index('Operating Airline')['Cluster_Label'].to_dict()
df_master['Cluster'] = df_master['Operating Airline'].map(cluster_map).fillna('Uncategorized')
df_master.to_csv(f'{DATA}/cargo_master.csv', index=False)

monthly = df_master.groupby([
    'Year', 'Month', 'Operating Airline', 'GEO Region', 'GEO Summary',
    'Cargo Aircraft Type', 'Cargo Type Code', 'Activity Type Code', 'Cluster'
]).agg(Cargo_Tons=('Cargo Metric TONS','sum'), Cargo_LBS=('Cargo Weight LBS','sum')).reset_index()
monthly['Date'] = pd.to_datetime(
    monthly['Year'].astype(str) + '-' + monthly['Month'].astype(str).str.zfill(2) + '-01')
monthly.to_csv(f'{DATA}/monthly_cargo_powerbi.csv', index=False)

print("    Exported:")
print(f"      airline_clusters.csv     → {len(agg)} rows")
print(f"      cargo_master.csv         → {len(df_master):,} rows")
print(f"      monthly_cargo_powerbi.csv → {len(monthly):,} rows")
print("\n[Done] All outputs ready.")
