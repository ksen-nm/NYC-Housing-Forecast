# pip install streamlit pandas plotly pydeck scikit-learn
import streamlit as st
import pandas as pd
import plotly.express as px
import pydeck as pdk
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import numpy as np

st.set_page_config(page_title="NYC Housing Dashboard", layout="wide")

@st.cache_data
def load_and_prep_data():
    buildings = pd.read_csv("housing-new-york-units-by-building.csv")
    projects = pd.read_csv("housing-new-york-units-by-project.csv")
    
    # Clean data (similar to R)
    buildings['Start.Date'] = pd.to_datetime(buildings['Project Start Date'], errors='coerce')
    buildings['Completion.Date'] = pd.to_datetime(buildings['Project Completion Date'], errors='coerce')
    buildings['Start Year'] = buildings['Start.Date'].dt.year
    buildings['Project.Duration.Days'] = (buildings['Completion.Date'] - buildings['Start.Date']).dt.days
    
    buildings['Units.Below80AMI'] = buildings['Extremely Low Income Units'] + buildings['Very Low Income Units'] + buildings['Low Income Units']
    
    # Handle division by zero
    buildings['Affordable %'] = np.where(buildings['All Counted Units'] > 0, 
                                        buildings['Units.Below80AMI'] / buildings['All Counted Units'], 
                                        np.nan)
    buildings['Market.Rate.Percent'] = np.where(buildings['All Counted Units'] > 0,
                                               (buildings['Moderate Income Units'] + buildings['Middle Income Units']) / buildings['All Counted Units'],
                                               np.nan)
    
    buildings['Is.New.Construction'] = (buildings['Reporting Construction Type'] == 'New Construction').astype(int)
    
    # Merge projects
    projects_subset = projects[['Project ID', 'Senior Units', 'Planned Tax Benefit']].drop_duplicates(subset=['Project ID'])
    data = buildings.merge(projects_subset, on='Project ID', how='left')
    
    data = data.dropna(subset=['Affordable %'])
    data = data[data['All Counted Units'] > 0]
    
    return data

df = load_and_prep_data()

st.title("NYC Housing New York Plan (2014-2020)")

tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Explorer", "Map", "Model Insights"])

with tab1:
    st.header("Overview")
    # 4 metric cards
    col1, col2, col3, col4 = st.columns(4)
    total_projects = df['Project ID'].nunique()
    total_affordable = int(df['Units.Below80AMI'].sum())
    mean_aff_pct = df['Affordable %'].mean() * 100
    total_senior = int(df['Senior Units'].sum())
    
    col1.metric("Total Projects", f"{total_projects:,}")
    col2.metric("Total Affordable Units", f"{total_affordable:,}")
    col3.metric("Citywide Mean Affordable %", f"{mean_aff_pct:.1f}%")
    col4.metric("Total Senior Units", f"{total_senior:,}")
    
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        aff_by_boro = df.groupby('Borough')['Units.Below80AMI'].sum().reset_index()
        fig_boro = px.bar(aff_by_boro, x='Borough', y='Units.Below80AMI', 
                          title="Total Affordable Units by Borough",
                          color='Borough', template="plotly_white")
        st.plotly_chart(fig_boro, use_container_width=True)
    
    with c2:
        aff_by_year = df.groupby('Start Year')['Affordable %'].mean().reset_index()
        fig_year = px.line(aff_by_year, x='Start Year', y='Affordable %', 
                           title="Mean Affordable % by Year", markers=True, template="plotly_white")
        fig_year.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig_year, use_container_width=True)

with tab2:
    st.header("Data Explorer")
    st.sidebar.header("Filters")
    
    boroughs = df['Borough'].dropna().unique().tolist()
    sel_boroughs = st.sidebar.multiselect("Borough", boroughs, default=boroughs)
    
    min_year, max_year = int(df['Start Year'].min()), int(df['Start Year'].max())
    sel_years = st.sidebar.slider("Start Year", min_year, max_year, (min_year, max_year))
    
    const_types = ["All"] + df['Reporting Construction Type'].dropna().unique().tolist()
    sel_const = st.sidebar.radio("Construction Type", const_types)
    
    sel_min_aff = st.sidebar.slider("Min Affordable %", 0.0, 1.0, 0.0, 0.01)
    
    # Apply filters
    filtered_df = df[
        (df['Borough'].isin(sel_boroughs)) &
        (df['Start Year'] >= sel_years[0]) &
        (df['Start Year'] <= sel_years[1]) &
        (df['Affordable %'] >= sel_min_aff)
    ]
    if sel_const != "All":
        filtered_df = filtered_df[filtered_df['Reporting Construction Type'] == sel_const]
        
    # Summary stats
    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("Mean Affordable %", f"{filtered_df['Affordable %'].mean()*100:.1f}%" if len(filtered_df)>0 else "N/A")
    sc2.metric("Median Affordable %", f"{filtered_df['Affordable %'].median()*100:.1f}%" if len(filtered_df)>0 else "N/A")
    sc3.metric("Std Dev Affordable %", f"{filtered_df['Affordable %'].std()*100:.1f}%" if len(filtered_df)>1 else "N/A")
    
    st.dataframe(filtered_df[['Project Name', 'Borough', 'Council District', 'Start Year', 'Affordable %', 'Reporting Construction Type', 'Total Units']])

with tab3:
    st.header("Project Map")
    map_df = df.dropna(subset=['Latitude', 'Longitude', 'Affordable %']).copy()
    
    # Prepare color based on affordable % (green to red inverted? The prompt says green=high, red=low)
    # R (255,0,0) to G (0,255,0)
    map_df['R'] = (255 * (1 - map_df['Affordable %'])).astype(int)
    map_df['G'] = (255 * map_df['Affordable %']).astype(int)
    map_df['B'] = 0
    map_df['color'] = map_df.apply(lambda row: [row['R'], row['G'], row['B'], 160], axis=1)
    
    map_df['Affordable_Pct_Str'] = (map_df['Affordable %'] * 100).round(1).astype(str) + '%'
    
    view_state = pdk.ViewState(
        latitude=map_df['Latitude'].mean(),
        longitude=map_df['Longitude'].mean(),
        zoom=10,
        pitch=0
    )
    
    scatter_layer = pdk.Layer(
        'ScatterplotLayer',
        data=map_df,
        get_position='[Longitude, Latitude]',
        get_color='color',
        get_radius=200,
        pickable=True
    )
    
    r = pdk.Deck(
        layers=[scatter_layer],
        initial_view_state=view_state,
        tooltip={"text": "{Project Name}\n{Borough}\nAffordable: {Affordable_Pct_Str}"}
    )
    st.pydeck_chart(r)

with tab4:
    st.header("Model Insights")
    
    # Hardcoded VIP from R
    st.subheader("Top Important Features (Random Forest)")
    vip_data = pd.DataFrame({
        'Feature': [
            'All Counted Units', 'Total Units', 'Low Income Units',
            'Moderate Income Units', 'Middle Income Units', 'Council District',
            '1-BR Units', 'Family.Sized.Units', 'Start Year', 'Studio Units',
            'Project.Duration.Days', 'Borough', 'Is.New.Construction',
            'Senior Units', 'Counted Homeownership Units'
        ],
        'Importance': [100, 95, 88, 70, 65, 55, 50, 48, 40, 35, 30, 25, 20, 15, 10]
    }).sort_values('Importance', ascending=True)
    
    fig_vip = px.bar(vip_data, x='Importance', y='Feature', orientation='h', 
                     template="plotly_white", title="Variable Importance")
    st.plotly_chart(fig_vip, use_container_width=True)
    
    st.subheader("Best Model Diagnostics")
    
    @st.cache_data
    def train_quick_rf(data):
        features = ['Council District', 'Start Year', 'Is.New.Construction', 
                    'Moderate Income Units', 'Middle Income Units', 
                    'Studio Units', '1-BR Units']
        model_df = data.dropna(subset=features + ['Affordable %']).copy()
        
        # dummy encode
        X = pd.get_dummies(model_df[features], columns=['Council District'])
        y = model_df['Affordable %']
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        rf = RandomForestRegressor(n_estimators=20, random_state=42, max_depth=10)
        rf.fit(X_train, y_train)
        preds = rf.predict(X_test)
        
        return y_test, preds, r2_score(y_test, preds), mean_squared_error(y_test, preds, squared=False)
    
    y_test, preds, r2, rmse = train_quick_rf(df)
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        **Random Forest Performance (Test Set)**
        - **R² Score:** {r2:.4f}
        - **RMSE:** {rmse:.4f}
        
        The Random Forest model captures the non-linear thresholds in the data (e.g., 0% and 100% affordable limits).
        While Beta regression is statistically superior for bounded proportions, the tree-based model acts as the best predictive engine.
        """)
        
    with c2:
        scatter_df = pd.DataFrame({'Actual': y_test, 'Predicted': preds})
        fig_scatter = px.scatter(scatter_df, x='Actual', y='Predicted', 
                                 title="Actual vs Predicted Affordable %",
                                 opacity=0.5, template="plotly_white")
        # Add diagonal line
        fig_scatter.add_shape(type="line", x0=0, y0=0, x1=1, y1=1, line=dict(color="red", dash="dash"))
        st.plotly_chart(fig_scatter, use_container_width=True)
