import streamlit as st
import pandas as pd
import plotly.express as px

#setting wide layout so graphs look better
st.set_page_config(
    page_title="ATP Dashboard",
    page_icon="🎾",
    layout="wide"
)



#webpage title
st.title('ATP Statistics')
st.caption('The ATP provides their own statistics that measures serve, return, and under pressure performance for each player. ' \
'The line chart displays these ratings over time, while the scatter plot shows how heavily certain metrics ' \
'correlate to these ratings.')

#sidebar title
st.sidebar.header('Filters')

#dropdown menu allows user to select which dataframe they want to see
metric_choice = st.sidebar.selectbox(
    'Select Metric',
    ['Serve Rating', 'Return Rating', 'Under Pressure Rating']
)


#reads dataframe depending on users choice
@st.cache_data(ttl=3600) #refresh every hour
def load_data(metric_choice):
    if metric_choice == 'Serve Rating':
        return pd.read_csv('data_files/atp_serve_data.csv')
    elif metric_choice == 'Return Rating':
        return pd.read_csv('data_files/atp_return_data.csv')
    else:
        return pd.read_csv('data_files/atp_pressure_data.csv')
df = load_data(metric_choice)


#titles each graph
title_map = {
    'Serve Rating' : 'ATP Serve Rating Over Time',
    'Return Rating' : 'ATP Return Rating Over Time',
    'Under Pressure Rating' : 'ATP under Pressure Rating Over Time'
}

#selects y-axis
metric_col_map = {
    'Serve Rating' : 'ServeRating',
    'Return Rating' : 'ReturnRating',
    'Under Pressure Rating' : 'PressureRating'

}

# creating a subset of stats for each dataframe
stat_map = {
    'Serve Rating' : ['FirstServePct', 'FirstServePointsWonPct', 'SecondServePointsWonPct', 'ServiceGamesWonPct', 'AvgAcesPerMatch', 'AvgDblFaultsPerMatch'],
    'Return Rating' : ['FirstServeReturnPointsWonPct', 'SecondServeReturnPointsWonPct',	'ReturnGamesWonPct', 'BrkPointsConvertedPct'],
    'Under Pressure Rating' : ['BrkPointsConvertedPct', 'BrkPointsSavedPct', 'TieBreaksWonPct', 'DecidingSetsWonPct']
}

stat_label_map = {
    'FirstServePct' : 'First Serve %',
    'FirstServePointsWonPct' : 'First Serve Points Won %',
    'SecondServePointsWonPct' : 'Second Serve Points Won %',
    'ServiceGamesWonPct' : 'Service Games Won %',
    'AvgAcesPerMatch' : 'Average Aces Per Match',
    'AvgDblFaultsPerMatch' : 'Average Double Faults Per Match',
    'FirstServeReturnPointsWonPct' : 'First Serve Return Points Won %',
    'SecondServeReturnPointsWonPct' : 'Second Serve Return Points Won %',
    'ReturnGamesWonPct' : 'Return Games Won %', 
    'BrkPointsConvertedPct' : 'Break Points Converted %', 
    'BrkPointsSavedPct' : 'Break Points Saved %', 
    'TieBreaksWonPct' : 'Tie Breaks Won %', 
    'DecidingSetsWonPct' : 'Deciding Sets Won %'

}






#converting time to a numeric value and making sure it is a year. Not including Career and 52 Week
df['year'] = df['time'].str.extract(r'(\d{4})').astype(float) #extracting four digit year
serve_data = df.dropna(subset=['year'])



#unique lists of options for filters
players = sorted(df['PlayerName'].unique())
surface = sorted(df['surface'].unique())
vs_rank = sorted(df['vs_rank'].unique())


#players filter
selected_players = st.sidebar.multiselect('Select Player(s)', players, default=['Roger Federer', 'Novak Djokovic', 'Rafael Nadal'])


#checks if the keys exist within session state. Sets default to 'all'
if 'selected_surface' not in st.session_state:
    st.session_state.selected_surface = ['all']
if 'selected_vs_rank' not in st.session_state:
    st.session_state.selected_vs_rank = ['all']


#creating filter logic. More than one filter can be present, unless it is 'all' which clears the filter
def update_filter(key):
    sel = st.session_state[key] #grabs current list of selected fitlers

    # If 'all' selected, there's more than one filter, and 'all' is most recent, overide to 'all'
    if 'all' in sel and len(sel) > 1 and sel[-1] == 'all':
        st.session_state[key] = ['all']
    # If another option clicked while 'all' is present → remove 'all'
    elif 'all' in sel and len(sel) > 1:
        st.session_state[key] = [opt for opt in sel if opt != 'all'] # key = 
    # If nothing selected → default to 'all'
    elif not sel:
        st.session_state[key] = ['all']




#creating multiset widgets with keys
selected_surface = st.sidebar.multiselect(  #surface filter
    'Select Surface(s)',  #title
    surface,  #list of surfaces
    default= st.session_state.selected_surface,
    key= 'selected_surface',
    on_change= lambda: update_filter('selected_surface')  #when there's a change, enusre correct filter logic
)

selected_vs_rank = st.sidebar.multiselect(  #vs_rank filter
    'Select Vs Rank(s)',  #title
    vs_rank,   #lits of ranks
    default= st.session_state.selected_vs_rank,
    key= 'selected_vs_rank',
    on_change= lambda: update_filter('selected_vs_rank')   #follow filter logic when there is change
)


#new filtered df
filtered_df = df.copy()



#surface filter
if 'all' in selected_surface:
    filtered_df = filtered_df[filtered_df['surface'] == 'all']  #if 'all', only show 'all'
else:
    filtered_df = filtered_df[filtered_df['surface'].isin(selected_surface)] #otherwise show the selections


#vs_rank filter
if 'all' in selected_vs_rank:
    filtered_df = filtered_df[filtered_df['vs_rank'] == 'all']  #if 'all', only show 'all'
else:
    filtered_df = filtered_df[filtered_df['vs_rank'].isin(selected_vs_rank)] #otherwise show the selections

#players filter logic (line chart only)
if selected_players:
    filtered_df = filtered_df[filtered_df['PlayerName'].isin(selected_players)]


scatter_df = df.copy()



#if more than one filter is selected, takes the average of the values
if (len(selected_surface) > 1 and 'all' not in selected_surface) or (len(selected_vs_rank) > 1 and 'all' not in selected_vs_rank):
    filtered_df = filtered_df.groupby(['PlayerName', 'year'])[metric_col_map[metric_choice]].mean().reset_index()

#y-axis labels for graphing
metric_axis_labels = {
    'Serve Rating' : 'Serve Rating',
    'Return Rating' : 'Return Rating',
    'Under Pressure Rating' : 'Pressure Rating'

}



#logic to ensure that session state does not reset when users select different ratings
if 'active_tab_index' not in st.session_state:
    st.session_state.active_tab_index = 0


#two tabs for different graphs
tab_1, tab_2 = st.tabs(["Ratings Over Time", "Stat Correlations"])


#first tab
with tab_1:
    if not filtered_df.empty:
        fig = px.line(  #line chart
            filtered_df,
            x='year',
            y=metric_col_map[metric_choice], #user selcection
            color='PlayerName',
            title=title_map[metric_choice],  #user selection
            labels={'year' : 'Year', 
                    metric_col_map[metric_choice] : metric_axis_labels[metric_choice],
                    'PlayerName' : 'Player'
                    }
        )
    else:
        st.info('No data found for the selected options.')

    st.plotly_chart(fig, use_container_width=True)





#second tab
with tab_2:
    stat_choices = [stat_label_map[c] for c in stat_map[metric_choice] if c in df.columns] #list of stats relevant to user chosen metric

    #reset stat when metric
    if 'metric_prev' not in st.session_state or st.session_state.metric_prev != metric_choice:
        #setting default as first stat
        st.session_state.selected_stat = stat_choices[0] if stat_choices else None
        st.session_state.metric_prev = metric_choice

    #selection for stat
    selected_label = st.selectbox(
        'Select Stat',
        options=stat_choices,
        key='selected_stat'
)
    #reverses user picked lable back to original column name necessary for plotting
    label_to_col = {v: k for k, v in stat_label_map.items()}
    selected_stat = label_to_col[selected_label]
    

    #cleaner x and y labels
    x_label = stat_label_map[selected_stat]
    y_label = metric_axis_labels[metric_choice]


    fig_scatter = px.scatter( #scatter plot
        filtered_df,
        x=selected_stat,
        y=metric_col_map[metric_choice], #user choice
        color='PlayerName',
        trendline='ols',
        trendline_scope="overall",
        title=f"{y_label} Vs {x_label}",  #user choices
        labels={
            selected_stat: x_label,
            metric_col_map[metric_choice]: y_label,
            'PlayerName': 'Player'
        }
)
    st.plotly_chart(fig_scatter, use_container_width=True)