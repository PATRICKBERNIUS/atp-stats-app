import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Win/Loss Index",
    page_icon="🎾",
    layout="wide"
)

#title
st.title('Win/Loss Index Stats')
st.caption('The Win/Loss Index shows the percentage of matches won by each player. Use the filters to view win percentages for different players, surfaces, tournaments, and more. ' \
'Selecting multiple categories will display a weighted average.')

#sidebar title
st.sidebar.header('Filters')

#cached data to speed up reloads
@st.cache_data(ttl=3600) #refresh every hour
def load_data_w_l():
    return pd.read_csv('data_files/atp_win_loss_index.csv')

w_l_df = load_data_w_l()
w_l_df = w_l_df.dropna(subset=["Index"])
w_l_df = w_l_df[w_l_df['Win'] + w_l_df['Loss'] > 1]



# -------------
# FILTER OPTIONS: Players, Categories, Time Periods, Countries
# ------------


#player list. Dropping NAs, ensuring each name is a string
players = sorted(w_l_df['PlayerName'].dropna().astype(str).unique())

#changing category labels
category_labels = {
    'all' : 'All',
    '1000': 'Masters 1000',
    '5thset' : '5th Set',
    'after1stsetwin' : 'After Winning 1st Set',
    'carpet' : 'Carpet LOL',
    'clay' : 'Clay',
    'hard' : 'Hard',
    'grass' : 'Grass',
    'finals' : 'Finals',
    'finalset' : 'Final Set',
    'grandslam' : 'Grand Slams',
    'indoor' : 'Indoors',
    'outdoor' : 'Outdoors',
    'tiebreak' : 'Tie Breaks',
    'vslefthanders' : 'Vs Left Handers',
    'vsrighthanders' : 'Vs Right Handers',
    'vstop10' : 'Vs Top 10'
}

#Category options. 
categories = [category_labels.get(cat, cat) for cat in sorted(w_l_df['Category'].unique())]

#reverse mapping from user labels to raw values for filtering
category_label_to_values = {v: k for k, v in category_labels.items()}


#changing time period labels
time_period_labels = {
    'all' : 'All',
    'career' : 'Career',
    'roll' : '52 Week',
    'ytd' : 'Year to Date'
}

# gets unique time periods for tp. Gets corresponding value in time_period_labels
time_periods = [time_period_labels.get(tp, tp) for tp in sorted(w_l_df['TimePeriod'].unique())]

#reverse mapping
time_period_label_to_value = {v: k for k, v in time_period_labels.items()}

#Country options
countries = sorted(w_l_df['Country'].unique())
countries = ['All' if c == 'all' else c for c in countries] #converting 'all' to 'All'


#--------------
# CREATING FILTERS
#--------------

#players filter
selected_players = st.sidebar.multiselect('Select Player(s)', players,)

#category filter

if 'selected_category_label' not in st.session_state:
    st.session_state['selected_category_label'] = ['All']

def update_category(key):
    sel = st.session_state[key] #grabs current list of selected fitlers
    # If 'all' selected, there's more than one filter, and 'all' is most recent, overide to 'all'
    if 'All' in sel and len(sel) > 1 and sel[-1] == 'All':
        st.session_state[key] = ['All']
    # If another option clicked while 'all' is present → remove 'all'
    elif 'All' in sel and len(sel) > 1:
        st.session_state[key] = [opt for opt in sel if opt != 'All'] # key = 
    # If nothing selected → default to 'all'
    elif not sel:
        st.session_state[key] = ['All']

selected_category_label = st.sidebar.multiselect(
    'Select Categories', 
    categories, 
    default=st.session_state.selected_category_label,
    key='selected_category_label',
    on_change= lambda: update_category('selected_category_label'))


#reversing labels to raw values for labeling
selected_category = [category_label_to_values[label] for label in selected_category_label]

#time filter
selected_time_period_label = st.sidebar.selectbox('Select Time Period', time_periods)
#reversing lables to raw values for labeling
selected_time_period = time_period_label_to_value.get(selected_time_period_label)

#country filter
if 'selected_countries' not in st.session_state:
    st.session_state['selected_countries'] = ['All']

selected_countries = st.sidebar.multiselect(
    'Select Countries', 
    countries, 
    default=st.session_state.selected_countries,
    key='selected_countries',
    on_change= lambda: update_category('selected_countries'))



#-------------
# APPLYING FILTER LOGIC
#-------------

#copying df
filtered_df = w_l_df.copy()



if selected_players:
    filtered_df = filtered_df[filtered_df['PlayerName'].isin(selected_players)]

if selected_category:
    filtered_df = filtered_df[filtered_df['Category'].isin(selected_category)]

if selected_time_period:
    filtered_df = filtered_df[filtered_df['TimePeriod'] == selected_time_period]

if selected_countries:
    filtered_df = filtered_df[filtered_df['Country'].isin(
        ['all' if c == 'All' else c for c in selected_countries]
        )]







#--------------
# GROUPING (if multiple values are selected)
#--------------


if len(selected_category) > 1: #if more than one category selected
    filtered_df = filtered_df.groupby('PlayerName').apply(
        lambda g : pd.Series({  #apply temporary dataframe
                                    'Win' : g['Win'].sum(), #total wins
                                    'Loss' : g['Loss'].sum(), #total losses
                                    'Titles' : g['Titles'].sum(), #total titles
                                    #compute weighted index
                                    'Index' : ((g['Index'] * (g['Win'] + g['Loss'])).sum() / (g['Win'] + g['Loss']).sum()).round(3)

    })
    ).reset_index()


#initiating session state for min wins parameter
if 'min_wins' not in st.session_state:
    st.session_state['min_wins'] = 10
    st.rerun()

#Making sure parameter dynamically updates based on max wins for each category
if not filtered_df.empty:
    min_poss_wins = int(filtered_df['Win'].min())
    max_poss_wins = int(filtered_df['Win'].max())
else:
    min_poss_wins, max_poss_wins = 0, 1
    


# Slider fitler for minimum wins
st.session_state['min_wins'] = st.slider(
    'Minimum Wins', 
    min_value= min_poss_wins,
    max_value= max_poss_wins,
    value=st.session_state['min_wins'], #session state ensures parameter doesn't reset each time a new filter is selected
    key='min_wins_slider')

#applying parameter slider
filtered_df = filtered_df[filtered_df['Win'] >= st.session_state['min_wins']]


#Ranking players by index
ranked_df = filtered_df.sort_values("Index", ascending=False)



#players displayed filter
top_n_option = st.sidebar.selectbox(
    'Select # of Players to be Displayed',
    options=['All', 'Top 10', 'Top 25', 'Top 50'],
    index=1 #default
)

if top_n_option == 'All':  
    top_n = None  #do nothing if All is selected
else:  #otherwise
    top_n = int(top_n_option.split()[1])  #turn the option into an integer (10, 25, or 50)


if top_n is not None: #if another option is selected
    ranked_df = ranked_df.head(top_n) #keep only the first n rows

#st.write(ranked_df[['PlayerName','Category']])

#---------------------
# Plotting bar chart
#---------------------
if not ranked_df.empty:
    fig = px.bar(
        ranked_df,
        x='PlayerName',
        y='Index',
        hover_data= ['Win', 'Loss', 'Titles'],
        labels={'PlayerName': 'Player'}
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Note: Use the slider to select minimum amount of wins for the players displayed. If the parameter starts acting weird, refresh the app.")
else:
    st.write("No Data To Display")
