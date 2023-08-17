import streamlit as st
import pandas as pd
import numpy as np
# import plotly as pt
import plotly.express as px
# import seaborn as ss
# from sklearn.preprocessing import MinMaxScaler
from model_scoring import get_data_and_weights, calculate_scores
from folium.plugins import HeatMap
from IPython.display import display
import streamlit.components.v1 as components
import folium


#Page settings
st.set_page_config(layout='wide')


# Defining a function that will cache df_final data for the rest of the code
@st.cache
def fetch_data_and_weights():
    return get_data_and_weights()

df_final, weights, df_scale, df4 = get_data_and_weights()

### Header section ###
section_title = st.empty()
section_title.markdown('# PH Housing Opportunity Score Report')
section_header = st.empty()
section_header.markdown('Opportunity scores are derived from the assignment of weightages to specific attributes at regional, provincial, and city levels.')

#### Sidebar filters ###

st.sidebar.markdown('## Weight Input:')
weights_input = {}
for feature, weight in weights.items():
    weights[feature] = st.sidebar.slider(f"Weight for {feature}", min_value=0.0, max_value=1.0, value=weight, step=0.01)

st.sidebar.markdown(f"**Sum of weights: {sum(weights.values()):.2f}**")

if st.sidebar.button('Apply weights'):
    if sum(weights.values()) != 1:
        st.sidebar.warning('Please adjust the weights so that their total equals 1.')
    else:
        df_final = calculate_scores(df_scale, df4, weights)

st.sidebar.markdown("---")

st.sidebar.markdown('## Filters for Raw Dataset:')

## Regions
regions = df_final['region'].unique()
default_region_index = list(regions).index("NCR")

selected_region = st.sidebar.selectbox('Select Region', options=regions, index=default_region_index)
df_filtered_by_region = df_final[df_final['region'] == selected_region]

## Provinces
provinces = df_filtered_by_region['province'].unique()
selected_provinces = st.sidebar.multiselect('Select Province(s)', options=provinces, default=provinces)
df_filtered = df_filtered_by_region[df_filtered_by_region['province'].isin(selected_provinces)]

### Folium heatpam
section_map = st.empty()

# Create the Folium map
m = folium.Map(location=[df_final['lat'].mean(), df_final['long'].mean()], zoom_start=5.5, width='100%', height='100%')
gradient = {0.0: 'blue', 0.5: 'lightblue', 0.7: 'orange', 1.0: 'red'}
heat_data = [[row['lat'], row['long'], row['opportunity_score']] for index, row in df_final.iterrows()]
HeatMap(heat_data, min_opacity=0.2, max_opacity=0.8, gradient=gradient).add_to(m)

# Convert the map to HTML
html = m._repr_html_()

# Display the HTML in the map section
section_map.markdown("---")
section_map.markdown("### Opportunity score map")
html = m._repr_html_()
components.html(html, width=1000, height=600)

#### New Plots ####

section_plots = st.empty()
section_plots.markdown("---")

opportunity_score_column = "opportunity_score"
top_n = 10

# Create mappings
city_to_province = df_final[['city_municipality', 'province']].set_index('city_municipality').squeeze().to_dict()
city_to_region = df_final[['city_municipality', 'region']].set_index('city_municipality').squeeze().to_dict()
province_to_region = df_final[['province', 'region']].set_index('province').squeeze().to_dict()

for level in ['region', 'province', 'city_municipality']:
    # Reduce spacing before each plot
    # st.markdown("&nbsp;", unsafe_allow_html=True)
    # Group by the level and calculate the mean opportunity score
    df_grouped = df_final[[level, opportunity_score_column]].groupby(level).mean().reset_index()

    # Sort by opportunity score and select top N
    df_sorted = df_grouped.sort_values(by=opportunity_score_column, ascending=True)
    df_top = df_sorted.tail(top_n)

    # Map 'region' and 'province' to 'city_municipality', and 'region' to 'province'
    if level == 'city_municipality':
        df_top['region'] = df_top[level].map(city_to_region)
        df_top['province'] = df_top[level].map(city_to_province)
    elif level == 'province':
        df_top['region'] = df_top[level].map(province_to_region)

    # Create the plot
    hover_data = ['region', 'province'] if level == 'city_municipality' else ['region'] if level == 'province' else None
    fig = px.bar(df_top, 
                 x=opportunity_score_column, 
                 y=level, 
                 orientation='h', 
                 hover_data=hover_data,
                 title=f"Top 10 {level.title()}s")
    fig.update_layout(autosize=True, height=400, width=400)

    # Display the plot
    st.plotly_chart(fig, use_container_width=True)


# #### Old Plots ###
# section_plots = st.empty()
# section_plots.markdown("---")
# col1, col2, col3 = st.columns(3)

# opportunity_score_column = "opportunity_score"
# top_n = 10

# # Create mappings
# city_to_province = df_final[['city_municipality', 'province']].set_index('city_municipality').squeeze().to_dict()
# city_to_region = df_final[['city_municipality', 'region']].set_index('city_municipality').squeeze().to_dict()
# province_to_region = df_final[['province', 'region']].set_index('province').squeeze().to_dict()

# for col, level in zip([col1, col2, col3], ['region', 'province', 'city_municipality']):
#     # Group by the level and calculate the mean opportunity score
#     df_grouped = df_final[[level, opportunity_score_column]].groupby(level).mean().reset_index()

#     # Sort by opportunity score and select top N
#     df_sorted = df_grouped.sort_values(by=opportunity_score_column, ascending=True)
#     df_top = df_sorted.tail(top_n)

#     # Map 'region' and 'province' to 'city_municipality', and 'region' to 'province'
#     if level == 'city_municipality':
#         df_top['region'] = df_top[level].map(city_to_region)
#         df_top['province'] = df_top[level].map(city_to_province)
#     elif level == 'province':
#         df_top['region'] = df_top[level].map(province_to_region)

#     # Create the plot
#     hover_data = ['region', 'province'] if level == 'city_municipality' else ['region'] if level == 'province' else None
#     fig = px.bar(df_top, 
#                  x=opportunity_score_column, 
#                  y=level, 
#                  orientation='h', 
#                  hover_data=hover_data,
#                  title=f"Top 10 {level.title()}s")
#     fig.update_layout(autosize=True, height=400, width=400)

#     # Display the plot in the corresponding column
#     col.plotly_chart(fig)


### Raw Dataset ###
section_raw = st.empty()
section_raw.markdown("---")
section_raw.markdown('### Raw Dataset')
st.write(df_filtered)
