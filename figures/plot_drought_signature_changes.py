#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 17 13:22:47 2025

@author: dardiry
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 24 14:12:51 2025
@author: dardiry
"""

import pandas as pd
import os
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.gridspec import GridSpec

# ---------------------- Data Processing Functions ---------------------- #
import numpy as np

def calculate_percent_change(df_hist, df_fut, metric):
    df_merged = pd.merge(df_hist, df_fut, on='reservoir', suffixes=('_hist', '_fut'))
    if metric == 'frequent_onset_month':
        df_merged[f'{metric}'] = df_merged[f'{metric}_fut'] - df_merged[f'{metric}_hist']
    else:
        df_merged[f'{metric}'] = 100 * ((df_merged[f'{metric}_fut'] - df_merged[f'{metric}_hist']) / df_merged[f'{metric}_hist'])
    return df_merged

def calculate_change(df_hist, df_fut, metric):
    """Normal (linear) difference."""
    df_merged = pd.merge(df_hist, df_fut, on='reservoir', suffixes=('_hist', '_fut'))
    df_merged[f'{metric}'] = df_merged[f'{metric}_fut'] - df_merged[f'{metric}_hist']
    return df_merged

def circular_diff(m1, m2):
    """Compute circular difference between two month values in range [-6, 6]."""
    diff = ((m2 - m1 + 6) % 12) - 6
    return diff

def calculate_circular_change(df_hist, df_fut, metric):
    """Special function for circular onset month changes."""
    df_merged = pd.merge(df_hist, df_fut, on='reservoir', suffixes=('_hist', '_fut'))
    df_merged[f'{metric}'] = df_merged.apply(
        lambda x: circular_diff(x[f'{metric}_hist'], x[f'{metric}_fut']),
        axis=1
    )
    return df_merged

# ---------------------- Spatial Plot Function ---------------------- #
def plot_map(df_gdf, metric, states_shp, huc2_filtered, ax, vmin, vmax, fig):
    # Reproject data to EPSG:2163 for consistency
    states_shp = states_shp.to_crs("EPSG:2163")
    huc2_filtered = huc2_filtered.to_crs("EPSG:2163")
    df_gdf = df_gdf.to_crs("EPSG:2163")

    # Compute average change per HUC2
    huc2_avg = df_gdf.groupby('huc2')[metric].mean().reset_index()
    huc2_avg_df = huc2_filtered.merge(huc2_avg, on='huc2')

    # Define colormap with smooth color scaling
    cmap_metric = {
        'resilience': 'RdBu', 'reliability': 'RdBu', 'vulnerability': 'RdBu_r',
        'frequent_onset_month': 'RdBu_r', 'avg_drought_length': 'RdBu_r', 'recovery_avg': 'RdBu_r',
        'frequency': 'RdBu_r', 'max_drought': 'RdBu_r','frequent_severity': 'RdBu_r'
    }
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)

    # Plot HUC2 regions with average values
    huc2_avg_df.plot(column=metric, cmap=cmap_metric.get(metric, 'RdBu'),
                      vmin=vmin, vmax=vmax, linewidth=0.5, edgecolor="gainsboro", 
                      facecolor="lightgray", alpha=0.6, ax=ax)

    # Plot state boundaries with subtle effect
    states_shp.boundary.plot(ax=ax, color="gainsboro", linewidth=0.6, alpha=0.6)

    # Scatter plot for reservoirs
    scatter = ax.scatter(df_gdf.geometry.x, df_gdf.geometry.y, c=df_gdf[metric], 
                          s=df_gdf['cap_hist'] / 50, cmap=cmap_metric.get(metric, 'RdBu'),
                          norm=norm, edgecolors="k", linewidth=0.4, alpha=0.8)
   
    # Remove axis labels & spines for a clean look
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Adjust the position of the color bar to make it shorter and within the boundaries
    # Add color bar with adjusted shorter height and position
    cax = fig.add_axes([ax.get_position().x1, ax.get_position().y0 + 0.03,    
                    0.02, ax.get_position().height * 0.7])  # Shorter color bar (30% height)

    cb = plt.colorbar(scatter, cax=cax, orientation='vertical')
    cb.ax.tick_params(labelsize=10)

# ---------------------- Main Figure Function ---------------------- #
def create_figure(historical_df, future_df, metrics, huc2_shp, states_shp, selected_regions):
    fig = plt.figure(figsize=(8, 6), dpi=300)
    ax = fig.add_subplot(111)

    huc2_filtered = huc2_shp[huc2_shp['huc2'].isin(selected_regions)]
    metric = metrics[0]  # Only one metric for single plot

    # --- Use circular change for onset, linear otherwise ---
    if metric == 'frequent_onset_month':
        df_change = calculate_circular_change(historical_df, future_df, metric)
        cmap = 'RdBu_r'
    else:
        df_change = calculate_change(historical_df, future_df, metric)
        cmap = 'RdBu'
        
    vmins = {'resilience': -0.25, 'reliability': -0.25, 'vulnerability': -0.25,
             'frequent_onset_month': -3, 'avg_drought_length': -6, 'recovery_avg': -10,
             'max_drought': -0.25, 'frequency': -0.25, 'frequent_severity': -3}
    vmaxs = {'resilience': 0.25, 'reliability': 0.25, 'vulnerability': 0.25,
             'frequent_onset_month': 3, 'avg_drought_length': 6, 'recovery_avg': 10,
             'max_drought': 0.25, 'frequency': 0.25, 'frequent_severity': 3}
    
    # --- Convert to GeoDataFrame ---
    df_gdf = gpd.GeoDataFrame(df_change, geometry=gpd.points_from_xy(df_change['lon_hist'], df_change['lat_hist']))
    df_gdf.crs = huc2_shp.crs
    df_gdf = gpd.sjoin(df_gdf, huc2_filtered, how="inner", predicate='intersects')

    # --- Plot ---
    plot_map(df_gdf, metric, states_shp, huc2_filtered, ax, vmins[metric], vmaxs[metric], fig)

    plt.suptitle(f"{metric.replace('_', ' ').title()} (Circular Change, months)" if metric == 'frequent_onset_month' 
                 else f"{metric.replace('_', ' ').title()} (Change)", fontsize=8, y=0.90)
    plt.tight_layout()
    plt.show()


# %%  ---------------------- Example Usage ---------------------- #

# Define working directory

os.chdir(r'PATH/TO/WORKING/DIRECTORY')
wd = os.getcwd()

# Load shapefiles
states_path = f"{wd}/datasets/shapefiles/cb_2015_us_state_500k/cb_2015_us_state_500k.shp"
states_shp = gpd.read_file(states_path)

huc2_path = f"{wd}/datasets/huc2/HUC_2.shp"
huc2_shp = gpd.read_file(huc2_path)

# Load data
hist_filename = "Reservoir_Drought_Signatures_MOSART-CLM_HIST_DT20_RT25.csv"
future_filename = "Reservoir_Drought_Signatures_MOSART-CLM_RCP85_HOT_FAR_DT20_RT50.csv"

historical_df = pd.read_csv(f"{wd}/outputs/drought_signatures/{hist_filename}")
future_df = pd.read_csv(f"{wd}/outputs/drought_signatures/{future_filename}")

# Convert to GeoDataFrames
historical_gdf = gpd.GeoDataFrame(historical_df, geometry=gpd.points_from_xy(historical_df['lon'], historical_df['lat']))
future_gdf = gpd.GeoDataFrame(future_df, geometry=gpd.points_from_xy(future_df['lon'], future_df['lat']))

historical_gdf.crs = huc2_shp.crs
future_gdf.crs = huc2_shp.crs

# Spatial join
historical_gdf = gpd.sjoin(historical_gdf, huc2_shp[['huc2', 'geometry']], how='left', predicate='intersects')
future_gdf = gpd.sjoin(future_gdf, huc2_shp[['huc2', 'geometry']], how='left', predicate='intersects')

historical_df = pd.DataFrame(historical_gdf.drop(columns='geometry'))
historical_df['max_drought']=1-historical_df['max_drought']
future_df = pd.DataFrame(future_gdf.drop(columns='geometry'))
future_df['max_drought']=1-future_df['max_drought']

# metrics = ['frequent_onset_month', 'avg_drought_length', 'recovery_avg',
#             'max_drought', 'frequency', 'frequent_severity']
metrics = ['frequent_onset_month']  # Only one metric for single plot
selected_regions = ['03', '12', '14', '17', '18']

# Create the figure
create_figure(historical_df, future_df, metrics, huc2_shp, states_shp, selected_regions)


# %% Statistics
huc2_filtered = huc2_shp[huc2_shp['huc2'].isin(selected_regions)]
metric = metrics[0]  # Plot only one metric
df_change = calculate_circular_change(historical_df, future_df, metric)
df_gdf = gpd.GeoDataFrame(df_change, geometry=gpd.points_from_xy(df_change['lon_hist'], df_change['lat_hist']))
df_gdf.crs = huc2_shp.crs
df_gdf = gpd.sjoin(df_gdf, huc2_filtered, how="inner", predicate='intersects')
huc2_stats_hist = historical_df.groupby('huc2')[metric].agg(['mean', 'max', 'min']).reset_index()
huc2_stats_fut = future_df.groupby('huc2')[metric].agg(['mean', 'max', 'min']).reset_index()
huc2_stats = df_gdf.groupby('huc2')[metric].agg(['mean', 'max', 'min']).reset_index()
print(huc2_stats_hist)
print(huc2_stats_fut)
print(huc2_stats)


# %% Circular Changes

import pandas as pd
import numpy as np
from scipy.stats import circmean
import geopandas as gpd

# --- helper functions ---
def circular_mean_month(values):
    radians = np.deg2rad(values * 30)
    mean_angle = np.angle(np.mean(np.exp(1j * radians)))
    if mean_angle < 0:
        mean_angle += 2 * np.pi
    return (mean_angle / (2 * np.pi)) * 12

def circular_diff(m1, m2):
    diff = ((m2 - m1 + 6) % 12) - 6  # ensures range [-6, 6]
    return diff

def month_to_season(month):
    if month >= 12 or month < 3:
        return "Winter"
    elif 3 <= month < 6:
        return "Spring"
    elif 6 <= month < 9:
        return "Summer"
    else:
        return "Fall"

# --- region mapping ---
region_map = {
    '03': 'South Atlantic–Gulf',
    '12': 'Texas–Gulf',
    '14': 'Upper Colorado',
    '17': 'Pacific Northwest',
    '18': 'California'
}

# --- subset to selected HUC2 regions ---
historical_sel = historical_df[historical_df['huc2'].isin(selected_regions)].copy()
future_sel = future_df[future_df['huc2'].isin(selected_regions)].copy()

# --- merge historical and future by reservoir ---
df_merged = pd.merge(
    historical_sel[['reservoir', 'huc2', 'frequent_onset_month']],
    future_sel[['reservoir', 'frequent_onset_month']],
    on='reservoir',
    suffixes=('_hist', '_fut')
)

# --- compute circular difference for each reservoir ---
df_merged['circular_shift'] = df_merged.apply(
    lambda x: circular_diff(x['frequent_onset_month_hist'], x['frequent_onset_month_fut']),
    axis=1
)

# --- identify dams with max delay (+ shift) and max advance (− shift) per region ---
extreme_shifts = []
for huc in selected_regions:
    df_region = df_merged[df_merged['huc2'] == huc]
    if not df_region.empty:
        max_delay = df_region.loc[df_region['circular_shift'].idxmax()]
        max_advance = df_region.loc[df_region['circular_shift'].idxmin()]
        extreme_shifts.append({
            'huc2': huc,
            'region_name': region_map[huc],
            'max_delay_dam': max_delay['reservoir'],
            'max_delay_shift_months': round(max_delay['circular_shift'], 2),
            'max_advance_dam': max_advance['reservoir'],
            'max_advance_shift_months': round(max_advance['circular_shift'], 2)
        })

extreme_shifts_df = pd.DataFrame(extreme_shifts)

# --- compute circular means for each HUC2 region ---
circular_hist = (historical_sel
    .groupby('huc2')['frequent_onset_month']
    .apply(circular_mean_month)
    .reset_index(name='circular_mean_month_hist'))

circular_fut = (future_sel
    .groupby('huc2')['frequent_onset_month']
    .apply(circular_mean_month)
    .reset_index(name='circular_mean_month_fut'))

# --- merge and compute change ---
circ_summary = circular_hist.merge(circular_fut, on='huc2')
circ_summary['circular_change_months'] = circ_summary.apply(
    lambda x: circular_diff(x['circular_mean_month_hist'], x['circular_mean_month_fut']), axis=1
)
circ_summary['region_name'] = circ_summary['huc2'].map(region_map)
circ_summary['hist_season'] = circ_summary['circular_mean_month_hist'].apply(month_to_season)
circ_summary['fut_season'] = circ_summary['circular_mean_month_fut'].apply(month_to_season)

# --- merge both summaries for reporting ---
summary_full = pd.merge(circ_summary, extreme_shifts_df, on=['huc2', 'region_name'])

# --- display results ---
print("===== CIRCULAR MEAN DROUGHT ONSET (Historical vs Future) =====")
print(summary_full)


# %% Extract specific dams

import pandas as pd

# === Define regions and key dams ===
target_hucs = ['17', '18']
key_dams = ['Grand Coulee', 'Libby', 'New Melones', 'Shasta']

# === Select relevant metrics ===
metrics = ['avg_drought_length', 'frequency']

# Filter data for the selected HUC2s only
hist_sel = historical_df[historical_df['huc2'].isin(target_hucs)].copy()
fut_sel = future_df[future_df['huc2'].isin(target_hucs)].copy()

# === Regional summary (mean change by HUC2) ===
regional_change = []
for huc in target_hucs:
    row = {'huc2': huc}
    for metric in metrics:
        hist_mean = hist_sel.loc[hist_sel['huc2'] == huc, metric].mean()
        fut_mean = fut_sel.loc[fut_sel['huc2'] == huc, metric].mean()
        row[f'{metric}_hist_mean'] = hist_mean
        row[f'{metric}_fut_mean'] = fut_mean
        row[f'{metric}_change'] = fut_mean - hist_mean
    regional_change.append(row)

regional_change_df = pd.DataFrame(regional_change)
print("===== Regional Mean Changes =====")
print(regional_change_df.round(3))

# === Dam-level change (for selected key dams) ===
dam_change = []
for dam in key_dams:
    hist_row = historical_df[historical_df['reservoir'] == dam]
    fut_row = future_df[future_df['reservoir'] == dam]
    if not hist_row.empty and not fut_row.empty:
        for metric in metrics:
            hist_val = hist_row[metric].values[0]
            fut_val = fut_row[metric].values[0]
            dam_change.append({
                'reservoir': dam,
                'metric': metric,
                'hist_val': hist_val,
                'fut_val': fut_val,
                'change': fut_val - hist_val,
                'huc2': hist_row['huc2'].values[0]
            })

dam_change_df = pd.DataFrame(dam_change)
print("\n===== Key Dam Changes =====")
print(dam_change_df.round(3))
