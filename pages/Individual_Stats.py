import streamlit as st
import pandas as pd
import plotly.express as px



st.set_page_config(
    page_title="Individual Stats",
    page_icon="🎾",
    layout="wide"
)



#Title
st.title('Individual Stats')

#sidebar title
st.sidebar.header('Filters')

#cached data to speed up reloads
@st.cache_data(ttl=3600) #refresh every hour
def load_data_individual():
    return pd.read_csv('data_files/atp_player_stats.csv.gz')

ind_df = load_data_individual()
ind_df = ind_df.dropna(subset=["PlayerId"])
ind_df = ind_df[ind_df['Matches'] >= 5]   #only include players who played at least 5 matches


#ensuring proper formatting. This was an unecessarily easy fix to a lot of problems.
ind_df['Country'] = ind_df['Country'].astype(str).str.strip()
ind_df['Surface'] = ind_df['Surface'].astype(str).str.strip()
ind_df['Time'] = ind_df['Time'].astype(str).str.strip()
ind_df['Stat'] = ind_df['Stat'].astype(str).str.strip()


#ensuring number column is clean and numeric
if 'Number' in ind_df:
    ind_df['Number'] = (ind_df['Number'].astype(str).str.replace(',', '', regex=False).str.strip().astype(float))

#ensuring percentage column is numeric
if 'Percentage' in ind_df:
    ind_df['Percentage'] = (ind_df['Percentage'].astype(str).str.replace('%', '', regex=False).str.strip().astype(float))

# -------------
# FILTER OPTIONS: Players, Stats, Time Periods, Countries, Surface
# ------------

players = sorted(ind_df['PlayerName'].dropna().astype(str).unique())

stats = sorted(ind_df['Stat'].dropna().astype(str).unique())

time = sorted(ind_df['Time'].dropna().astype(str).unique())

countries = sorted(ind_df['Country'].dropna().astype(str).unique())

surfaces = sorted(ind_df['Surface'].dropna().astype(str).unique())




#--------------
# CREATING FILTERS
#--------------
#session state defaults
if 'ind_selected_countries' not in st.session_state:
    st.session_state['ind_selected_countries'] = ['all']
if 'ind_selected_surfaces' not in st.session_state:
    st.session_state['ind_selected_surfaces'] = ['all']



def update_category(key, default_token, all_options=None): #function that takes in session state key, default filter option. All options are all possible filter options
    sel = st.session_state[key] #current selection from user

    if all_options and len(sel) > 1: #if more than one selection
        selectable_options = set(all_options) - {default_token} #removes default from all options

        if set(sel) == selectable_options: #if user has selected every option
            st.session_state[key] = [default_token]  #revert back to default
            return
    
    if default_token in sel and len(sel) > 1 and sel[-1] == default_token:  #if default is selected, there's more than one selection, and the default was the last selection
        st.session_state[key] = [default_token] #revert back to the default
    elif default_token in sel and len(sel) > 1: #if default and another option selected
        st.session_state[key] = [x for x in sel if x != default_token] #selection is most recent selection. Gets rid of default if another option selected
    elif not sel: #if filter is empty
        st.session_state[key] = [default_token] #revert back to default






# --- PLAYER FILTER (with dynamic defaults) ---
if 'ind_selected_players' not in st.session_state:
    st.session_state['ind_selected_players'] = []

selected_players = st.sidebar.multiselect(
    'Select Player(s)',
    options=players,
    default=st.session_state.ind_selected_players,
    key='ind_selected_players'
)


#stats filter above graph, not sidebar
selected_stat = st.selectbox('Select Stats(s)', stats) 

#time filter
selected_time = st.sidebar.selectbox('Select Time', time, index=time.index('career'))

#country filter
selected_countries = st.sidebar.multiselect('Select Countries', 
                                            countries, 
                                            default=st.session_state.ind_selected_countries,
                                            key='ind_selected_countries',
                                            on_change=lambda: update_category('ind_selected_countries', 'all')
                                            )

#surface filter
selected_surfaces = st.sidebar.multiselect('Select Surface(s)', 
                                           surfaces, 
                                           default=st.session_state.ind_selected_surfaces,
                                           key='ind_selected_surfaces',
                                           on_change=lambda: update_category('ind_selected_surfaces', 'all', surfaces)
                                           )

#new df for filtering
filtered_df = ind_df.copy()





#creating filter logic
if selected_players:
    filtered_df = filtered_df[filtered_df['PlayerName'].isin(selected_players)]
if selected_stat:
    filtered_df = filtered_df[filtered_df['Stat'] == selected_stat]
if selected_time:
    filtered_df = filtered_df[filtered_df['Time'] == selected_time]
if selected_countries:
    filtered_df = filtered_df[filtered_df['Country'].isin(selected_countries)]
if selected_surfaces:
    filtered_df = filtered_df[filtered_df['Surface'].isin(selected_surfaces)]



#creating dynamic Y-axis
y_col_map = {
    "Aces": "Number",
    "1st-Serve": "Percentage",
    "1st-Serve-Points-Won": "Percentage",
    "2nd-Serve-Points-Won": "Percentage",
    "Service-Games-Won": "Percentage",
    "Break-Points-Saved": "Percentage",
    "1st-Serve-Return-Points-Won": "Percentage",
    "2nd-Serve-Return-Points-Won": "Percentage",
    "Break-Points-Converted": "Percentage",
    "Return-Games-Won": "Percentage"
}


#default if not in dictionary
y_col = y_col_map.get(selected_stat, "Number")





#-----
# new filters for 2nd tab, line chart
#-----
filtered_df_line = ind_df.copy()


if selected_stat: #stats filter
    filtered_df_line = filtered_df_line[filtered_df_line['Stat'] == selected_stat]
if selected_surfaces: #surfaces filter
    filtered_df_line = filtered_df_line[filtered_df_line['Surface'].isin(selected_surfaces)]
    
#Exclude career stats for the time-series chart
filtered_df_line = filtered_df_line[filtered_df_line['Time'] != 'career']


defaults_applied = False  #indicates if defaults are selected, which means no user selection
default_line_players = ['Roger Federer', 'Rafael Nadal', 'Novak Djokovic'] #big three players as default for line chart
country_players = [] #initializing players countries list

if selected_countries and 'all' not in selected_countries: #if user selects a country
    country_players = (
        ind_df.loc[ind_df['Country'].isin(selected_countries), 'PlayerName'] #find all the players from that country
        .dropna().unique().tolist() #create a list with each unique player
    )
if selected_players: #if a player is selected by user
    if country_players: #if a country is also selected
        players_for_line = list(set(selected_players) | set(country_players)) #show all the players from that country and the selected player
    else: #otherwise just show selected players
        players_for_line = selected_players      
elif country_players: #if country is selected
    players_for_line = country_players #show players from that country
else:
    players_for_line = [p for p in default_line_players if p in players] #line chart will show default (big three)
    defaults_applied = True  #indicator now shows defaults are selected

#filter for line chart to show players based on users selection above
filtered_df_line = filtered_df_line[filtered_df_line['PlayerName'].isin(players_for_line)]



#----
#Aggregation for multiple surface/country selections
#----

needs_agg = (
    (len(selected_surfaces) > 1 and 'all' not in selected_surfaces)
)

#ensuring aces will sum correctly. Had some problems with this
if selected_stat == 'Aces':
    filtered_df = (
        filtered_df.groupby(['PlayerName', 'Country'], as_index=False)
        .agg(Number=('Number', 'sum'), Matches=('Matches', 'sum'))
    )
    #for line chart
    filtered_df_line = (
        filtered_df_line.groupby(['PlayerName', 'Time', 'Country'], as_index=False)
        .agg(Number=('Number', 'sum'), Matches=('Matches', 'sum'))
    )
elif needs_agg and y_col == 'Percentage':
    filtered_df = (
        filtered_df
        .assign(weighted_val=lambda d: d[y_col] * d['Matches']) #temporary helper column with product of percetange and matches
        .groupby(['PlayerName', 'Country'], as_index=False)
        .agg(weighted_val=('weighted_val', 'sum'), Matches=('Matches', 'sum')) #summing total percentages and matches
        .assign(**{y_col: lambda d: d['weighted_val'] / d['Matches']}) #dividing by total matches to determine weighted percentage
        .drop(columns=['weighted_val'])
    )
    #for line chart
    filtered_df_line = ( 
        filtered_df_line
        .assign(weighted_val=lambda d: d[y_col] * d['Matches']) #temporary helper column with product of percetange and matches
        .groupby(['PlayerName', 'Time', 'Country'], as_index=False)
        .agg(weighted_val=('weighted_val', 'sum'), Matches=('Matches', 'sum')) #summing total percentages and matches
        .assign(**{y_col: lambda d: d['weighted_val'] / d['Matches']}) #dividing by total matches to determine weighted percentage
        .drop(columns=['weighted_val'])
    )

if y_col == 'Percentage':
    filtered_df[y_col] = filtered_df[y_col].round(2)
    filtered_df_line[y_col] = filtered_df_line[y_col].round(2)









#creating top n filter logic
top_n_option = st.sidebar.selectbox(
    'Select # of players to be displayed',
    options=['All', 'Top 5', 'Top 10', 'Top 25', 'Top 50'],
    index=2 #default
)

if top_n_option == 'All':
    top_n = None  #do nothing if All is selected
else: #otherwise
    top_n = int(top_n_option.split()[1]) #take the selection as a string and turn into integer (10, 25, or 50)


filtered_df = filtered_df.sort_values(by=y_col, ascending=False)
if top_n is not None: #if other option selected
    filtered_df = filtered_df.head(top_n)


# ---- Apply Top N players to line chart ----
# this chunk is possibly repetitive but it works so I'll leave it
if top_n is not None and not filtered_df_line.empty: 
    if y_col == 'Number': #if the stat is Aces
        ranking = (
            filtered_df_line.groupby('PlayerName', as_index=False)[y_col]
            .sum() #groups by player, and aggregates by total aces
            .sort_values(by=y_col, ascending=False)
        )
    else: #if any other stat
        ranking = ( #similar weighted average logic as before
            filtered_df_line
            .assign(weighted_val=lambda d: d[y_col] * d['Matches']) #multiply percentage by total matches
            .groupby('PlayerName', as_index=False)
            .agg(weighted_val=('weighted_val', 'sum'), Matches=('Matches', 'sum')) #total up percentages and matches
            .assign(**{y_col: lambda d: d['weighted_val'] / d['Matches']}) #divide total percent by matches to get weighted
            .drop(columns='weighted_val') #drop temp column
            .sort_values(by=y_col, ascending=False)
        )

    # Get top N player names
    top_players = ranking.head(top_n)['PlayerName'].tolist()

    # Keep only their full time-series data
    filtered_df_line = filtered_df_line[filtered_df_line['PlayerName'].isin(top_players)]





#dynamic control for toolip
hover_cols = ['Matches'] #default. Always want matches to show
if 'Country' in filtered_df.columns and selected_countries and 'all' not in selected_countries:
    hover_cols.append('Country') #add country to the tooltip if specific country selected



#two tabs
tab_1, tab_2 = st.tabs(["Individual Stats", "Individual Stats Over Time"])





#first tab
with tab_1:
    #ensuring proper ordering if aggregated
    
    order = filtered_df['PlayerName'].astype(str).tolist()

    if not filtered_df.empty:    
        fig = px.bar(    #plotting top players by stat
            filtered_df, 
            x='PlayerName',
            y=y_col, #dynamic axis for selected stat
            hover_data= hover_cols,
            title=f"{selected_stat} by Player",
            labels={'PlayerName': 'Player',
                   'Number': 'Aces'}
        )
        fig.update_xaxes(categoryorder='array', categoryarray=order)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("No Data to Display")
    if needs_agg:
        if selected_stat == 'Aces':
            st.caption("**Note:** Aces are summed when multiple surfaces or countries are selected.")
        else:
            st.caption("**Note:** Values are shown as a weighted average when multiple surfaces are selected, accounting for amount of matches played. " \
                "This may not account for players that played significantly less matches on some surfaces than others.")


#second tab showing line chart
with tab_2:
    if defaults_applied:
        st.caption("The Big Three are defaults. Select specific players or countries to view their stats.")
    if not filtered_df_line.empty:
        fig_2 = px.line(
            filtered_df_line,
            x='Time',
            y=y_col,
            color='PlayerName',
            hover_data=hover_cols,
            title=f"{selected_stat} Over Time",
            labels={'PlayerName': 'Player',
                   'Number': 'Aces'}
        )
        st.plotly_chart(fig_2, use_container_width=True)
    else:
        st.write("No Data to Display")

    #captions for certain situations
    if needs_agg:
        if selected_stat == 'Aces':
            st.caption("**Note:** Aces are summed when multiple surfaces or countries are selected.")
        else:
            st.caption("**Note:** Values are shown as a weighted average when multiple surfaces are selected, accounting for amount of matches played. " \
                "This may not account for players that played significantly less matches on some surfaces than others.")
    if selected_countries and 'all' not in selected_countries:
        st.caption("Note: Some combinations my not have adequate data. The chart is limited by ATP's website," \
        " who do not have complete data for some players within specific combinations. When selecting countries, try filtering for surfaces to get better results")

    


