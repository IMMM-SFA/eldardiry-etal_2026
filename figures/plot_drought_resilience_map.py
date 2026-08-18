#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 18 17:19:33 2025

@author: Hisham Eldardiry
"""

import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import os
from scipy.stats import gmean

# === Paths and setup ===
wd = 'PATH/TO/WORKING/DIRECTORY'
os.chdir(wd)


# Load shapefiles
states_shp = gpd.read_file('datasets/shapefiles/cb_2015_us_state_500k/cb_2015_us_state_500k.shp')
huc2_shp = gpd.read_file('datasets/huc2/HUC_2.shp')
selected_regions = ['03', '12', '14', '17', '18']
huc2_filtered = huc2_shp[huc2_shp['huc2'].isin(selected_regions)]

# Paths
grand_path = wd + '/datasets/GRanD/GRanD_dams_v1_1.shp'
grand_csv = wd + '/datasets/GRanD/GRanD_Dams_US.csv'

# Read shapefile & CSV
grand_shp = gpd.read_file(grand_path)
grand_df = pd.read_csv(grand_csv)
grand_coords = grand_df[['GRAND_ID', 'LONG_DD', 'LAT_DD']].drop_duplicates()

grand_df = grand_df[['GRAND_ID', 'LONG_DD', 'LAT_DD','DAM_NAME', 'CAP_MCM','MAIN_USE']]
grand_df['DAM_NAME'] = grand_df['DAM_NAME'].str.upper().str.strip()
grand_df['GRAND_ID'] = grand_df['GRAND_ID'].astype(int)


drought_threshold=20
recovery_threshold=50
scenario='rcp85_hot_far_DT%d_RT%d'%(drought_threshold,recovery_threshold)


# %% === Load historical metrics ===
hist_path = 'outputs/drought_signatures_timeseries/hist_DT%d_RT%d'%(drought_threshold,recovery_threshold)
hist_freq = pd.read_csv(f"{hist_path}/frequency_by_dam.csv").set_index('dam_id')['frequency']
hist_sev = pd.read_csv(f"{hist_path}/severity_by_dam.csv").T
hist_rec = pd.read_csv(f"{hist_path}/recovery_by_dam.csv").T
hist_dur = pd.read_csv(f"{hist_path}/drought_length_by_dam.csv").T

hist_sev.index = hist_sev.index.str.replace('dam_', '').astype(int)
hist_rec.index = hist_rec.index.str.replace('dam_', '').astype(int)
hist_dur.index = hist_dur.index.str.replace('dam_', '').astype(int)

hist_df = pd.DataFrame({
    'severity': hist_sev.mean(axis=1),
    'recovery': hist_rec.mean(axis=1),
    'duration': hist_dur.mean(axis=1),
    'frequency': hist_freq
})
hist_df['dam_id'] = hist_df.index

# Merge coordinates
hist_df = hist_df.rename(columns={'dam_id': 'GRAND_ID'})
hist_df = hist_df.merge(grand_df, on='GRAND_ID', how='left')
hist_df = hist_df.rename(columns={'LAT_DD': 'lat_hist', 'LONG_DD': 'lon_hist','CAP_MCM': 'cap_hist'})
hist_df = hist_df.rename(columns={'GRAND_ID': 'dam_id'})


# Save historical normalization ranges
sev_min, sev_max = hist_df['severity'].min(), hist_df['severity'].max()
rec_min, rec_max = hist_df['recovery'].min(), hist_df['recovery'].max()
dur_min, dur_max = hist_df['duration'].min(), hist_df['duration'].max()

# Normalize
hist_df['severity_norm'] = ((hist_df['severity'] - sev_min) / (sev_max - sev_min))
hist_df['recovery_norm'] = 1 - ((hist_df['recovery'] - rec_min) / (rec_max - rec_min))
hist_df['duration_norm'] = 1 - ((hist_df['duration'] - dur_min) / (dur_max - dur_min))
hist_df['frequency_norm'] = 1 - hist_df['frequency']


# Select normalized columns
norm_cols = ['frequency_norm', 'severity_norm', 'recovery_norm', 'duration_norm']

# Compute row-wise geometric mean excluding NaNs
hist_df['risk_score_hist'] = hist_df[norm_cols].apply(
    lambda row: gmean(row.dropna()) if row.notna().sum() > 0 else np.nan, axis=1
)

# %% === Load future metrics ===

fut_path = 'outputs/drought_signatures_timeseries/%s'%scenario
fut_freq = pd.read_csv(f"{fut_path}/frequency_by_dam.csv").set_index('dam_id')['frequency']
fut_sev = pd.read_csv(f"{fut_path}/severity_by_dam.csv").T
fut_rec = pd.read_csv(f"{fut_path}/recovery_by_dam.csv").T
fut_dur = pd.read_csv(f"{fut_path}/drought_length_by_dam.csv").T

fut_sev.index = fut_sev.index.str.replace('dam_', '').astype(int)
fut_rec.index = fut_rec.index.str.replace('dam_', '').astype(int)
fut_dur.index = fut_dur.index.str.replace('dam_', '').astype(int)

fut_df = pd.DataFrame({
    'severity': fut_sev.mean(axis=1),
    'recovery': fut_rec.mean(axis=1),
    'duration': fut_dur.mean(axis=1),
    'frequency': fut_freq
})
fut_df['dam_id'] = fut_df.index

# Filter dams to those with historical scores
fut_df = fut_df[fut_df['dam_id'].isin(hist_df['dam_id'])]

# Merge coordinates
fut_df = fut_df.rename(columns={'dam_id': 'GRAND_ID'})
fut_df = fut_df.merge(grand_df, on='GRAND_ID', how='left')
fut_df = fut_df.rename(columns={'LAT_DD': 'lat_fut', 'LONG_DD': 'lon_fut','CAP_MCM': 'cap_hist'})
fut_df = fut_df.rename(columns={'GRAND_ID': 'dam_id'})

# Normalize future using historical min/max
fut_df['severity_norm'] = ((fut_df['severity'] - sev_min) / (sev_max - sev_min))
fut_df['recovery_norm'] = 1 - ((fut_df['recovery'] - rec_min) / (rec_max - rec_min))
fut_df['duration_norm'] = 1 - ((fut_df['duration'] - dur_min) / (dur_max - dur_min))
fut_df['frequency_norm'] = 1 - fut_df['frequency']


# Select normalized columns
norm_cols = ['frequency_norm', 'severity_norm', 'recovery_norm', 'duration_norm']

# Compute row-wise geometric mean excluding NaNs
fut_df['risk_score_future'] = fut_df[norm_cols].apply(
    lambda row: gmean(row.dropna()) if row.notna().sum() > 0 else np.nan, axis=1
)

# %% === Join and calculate resilience change ===
joined = hist_df[['dam_id', 'risk_score_hist', 'lat_hist', 'lon_hist', 'cap_hist']] \
    .merge(fut_df[['dam_id', 'risk_score_future']], on='dam_id', how='left')
joined['resilience'] = joined['risk_score_future'] - joined['risk_score_hist']
# Remove duplicated columns
joined = joined.loc[:, ~joined.columns.duplicated()]

# === Make GeoDataFrame and plot ===
df_gdf = gpd.GeoDataFrame(joined, geometry=gpd.points_from_xy(joined['lon_hist'], joined['lat_hist']), crs=huc2_shp.crs)
df_gdf = df_gdf.to_crs(huc2_filtered.crs)
df_gdf = gpd.sjoin(df_gdf, huc2_filtered, how="inner", predicate='intersects')


selected_names = ['Hartwell Dam','Livingston Dam','Flaming Gorge','Grand Coulee','Shasta']
selected_id = [41, 198, 451, 1863]
selected_dams = df_gdf[df_gdf['dam_id'].isin(selected_id)].copy()


# Project everything to match map
df_gdf = df_gdf.to_crs("EPSG:2163")
huc2_filtered = huc2_filtered.to_crs("EPSG:2163")
states_shp = states_shp.to_crs("EPSG:2163")
selected_dams_web = selected_dams.to_crs(epsg=2163)

# %% === Plotting ===

color_map="PuOr"
fig = plt.figure(figsize=(8, 6), dpi=300)
ax = fig.add_subplot(111)


# HUC2 average
huc2_avg = df_gdf.groupby('huc2')['resilience'].mean().reset_index()



# Ensure capacity column is numeric
df_gdf['cap_hist'] = pd.to_numeric(df_gdf['cap_hist'], errors='coerce')

# Remove any rows with missing capacity or resilience
df_weighted = df_gdf.dropna(subset=['resilience', 'cap_hist'])

# Compute capacity-weighted average resilience per HUC2
huc2_avg = (
    df_weighted
    .groupby('huc2')
    .apply(lambda g: np.average(g['resilience'], weights=g['cap_hist']))
    .reset_index(name='resilience')
)

huc2_avg_df = huc2_filtered.merge(huc2_avg, on='huc2')

# Colormap and colorbar
norm = mcolors.Normalize(vmin=-0.25, vmax=0.25)
huc2_avg_df.plot(column='resilience', cmap=color_map, vmin=-0.25, vmax=0.25,
                 linewidth=0.5, edgecolor="gainsboro", facecolor="lightgray",
                 alpha=0.6, ax=ax)

states_shp.boundary.plot(ax=ax, color="gainsboro", linewidth=0.6, alpha=0.6)

scatter = ax.scatter(df_gdf.geometry.x, df_gdf.geometry.y, c=df_gdf['resilience'],
                     s=df_gdf['cap_hist'] / 50, cmap=color_map, norm=norm,
                     edgecolors="k", linewidth=0.4, alpha=0.8)

ax.set_xticks([]); ax.set_yticks([])
for spine in ax.spines.values(): spine.set_visible(False)

cax = fig.add_axes([ax.get_position().x1, ax.get_position().y0 + 0.03, 0.02, ax.get_position().height * 0.7])
cb = plt.colorbar(scatter, cax=cax, orientation='vertical')
cb.ax.tick_params(labelsize=10)

plt.tight_layout()
plt.show()


ax.scatter(
selected_dams_web.geometry.x, selected_dams_web.geometry.y,
marker='x',
s=50,                       # size of "x"
linewidth=0.5,
color='grey',
zorder=4,
alpha=0.75,
label='Selected Dams'
)


# %% # Create GeoDataFrame from joined table

joined = hist_df[['dam_id', 'risk_score_hist', 'lat_hist', 'lon_hist', 'cap_hist','MAIN_USE']] \
    .merge(fut_df[['dam_id', 'risk_score_future']], on='dam_id', how='left')
joined['resilience'] = joined['risk_score_future'] - joined['risk_score_hist']
# Remove duplicated columns
joined = joined.loc[:, ~joined.columns.duplicated()]

# Create GeoDataFrame from joined table
df_gdf = gpd.GeoDataFrame(
    joined, 
    geometry=gpd.points_from_xy(joined['lon_hist'], joined['lat_hist']),
    crs=huc2_shp.crs
)

# Spatial join to assign HUC2
df_gdf = gpd.sjoin(df_gdf, huc2_shp[['huc2', 'geometry']], how='left', predicate='intersects')

# Drop geometry and overwrite 'joined' if needed
joined = pd.DataFrame(df_gdf.drop(columns='geometry'))

# %% Pie chart
huc2_list = ['03', '12', '14', '17', '18']

# Ensure correct types
joined['huc2'] = joined['huc2'].astype(str)

# Classify dams by resilience direction
joined['resilience_class'] = np.where(joined['resilience'] < 0, 'At Risk', 'Resilient')


num_hucs = len(huc2_list)
fig, axes = plt.subplots(1, num_hucs, figsize=(3 * num_hucs, 3), dpi=200)



if num_hucs == 1:
    axes = [axes]

summary_list = []
for i, huc in enumerate(huc2_list):
    ax = axes[i]
    subset = joined[joined['huc2'] == huc]

    if subset.empty:
        ax.set_title(f'HUC2 {huc}\nNo Data', fontname='Times New Roman')
        ax.axis('off')
        continue

    counts = subset['resilience_class'].value_counts().reindex(['At Risk', 'Resilient'], fill_value=0)
    summary_list.append({'huc2': huc, 'At Risk': counts['At Risk'], 'Resilient': counts['Resilient']})

    sizes = counts.values
    labels = ['At Risk', 'Resilient']
    # colors = [(178/255, 34/255, 34/255), (25/255, 25/255, 112/255)]  # dark red, dark blue
    colors = ['#B35806', '#542788']  # dark orange, dark purple

    ax.pie(
        sizes,
        labels=None,
        autopct='%1.0f%%',
        colors=colors,
        textprops={'fontsize': 8, 'fontname': 'Times New Roman'},
        wedgeprops={'alpha': 0.70}
    )
    ax.set_title(f'HUC2 {huc}', fontname='Times New Roman', fontsize=10)

# plt.suptitle('Dams At Risk vs. Resilient by HUC2', fontname='Times New Roman', fontsize=12)
plt.tight_layout()
plt.subplots_adjust(top=0.85)
plt.show()

summary_df = pd.DataFrame(summary_list)
print(summary_df)
