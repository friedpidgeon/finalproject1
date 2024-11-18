import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import pydeck as pdk


def cleanNumValues(df, column, inequality="equal"):  # Cleans values with 0 or less in dataframe
    if inequality == "more":
        df[f"{column}Clean"] = df[column].apply(lambda x: None if x > 0 else x)
    elif inequality == "less":
        df[f"{column}Clean"] = df[column].apply(lambda x: None if x < 0 else x)
    elif inequality == "more equal":
        df[f"{column}Clean"] = df[column].apply(lambda x: None if x >= 0 else x)
    elif inequality == "less equal":
        df[f"{column}Clean"] = df[column].apply(lambda x: None if x <= 0 else x)
    else:
        df[f"{column}Clean"] = df[column].apply(lambda x: None if x == 0 else x)


# Function to replace incorrect values with NaN
def cleanNumberData(df):
    # Replace invalid values with NaN using lambda function
    cleanNumValues(df, 'location.latitude')
    cleanNumValues(df, 'location.longitude')
    cleanNumValues(df, 'statistics.floors above', "less equal")
    cleanNumValues(df, 'statistics.height', "less equal")
    cleanNumValues(df, 'status.completed.year', "less equal")
    cleanNumValues(df, 'status.started.year', "less equal")
    return df


def cleanData(df):
    # Necessary to clean data before using useful data
    df = cleanNumberData(df)
    df = df.dropna(subset=['location.city', 'location.latitudeClean',
                           'location.longitudeClean', 'statistics.floors aboveClean',
                           'statistics.heightClean', 'status.completed.yearClean',
                           'status.started.yearClean'])
    return df


# Prepare datasets for visualization/analysis
def filterData(df):
    # Question 1: What materials are most skyscrapers made from?
    # What is the most popular construction material for a given city?
    # Columns required: materials, cities, & country
    # Pie chart
    df1 = df[['material', 'location.city', 'location.country']]

    # Question 2: How many skyscrapers are in a selected
    # city, and which selected cities have the most skyscrapers?
    # Columns required: cities
    # Bar chart
    df2 = df[['location.city']]

    # Question 3: What cities have an average height above
    # (or below) a selected height?
    # Columns required: cities, & statistics.height/rank
    # Map showing average heights
    df3 = df[['location.city', 'statistics.heightClean', 'statistics.rank',
              'location.latitudeClean', 'location.longitudeClean', 'name']]
    return df1, df2, df3


def skyscrapersMaterial(df, city=None):
    # Question 1: What materials are most skyscrapers made from?
    # What is the most popular construction material for a given city?
    # list comprehension, .iterate rows
    materialCityList = [(row['material'], row['location.city']) for index, row in df.iterrows()]  # return list

    materialCityDf = pd.DataFrame(materialCityList, columns=['material', 'location.city'])  # list to dataframe

    materialCountsCity = materialCityDf.value_counts().reset_index(name='count')  # materials by city
    #reset index redoes the index column. Missing values are erased such that indexes are reassigned
    materialCountsTotal = materialCountsCity.groupby('material')['count'].sum().reset_index()  # total materials
    #researched numeric_only, and reset index
    cityMaterialCounts = pd.DataFrame()
    if city:
        cityMaterialCounts = materialCountsCity[materialCountsCity['location.city'] == city]
        totalCityCount = cityMaterialCounts['count'].sum()
        cityMaterialCounts['percentage'] = round((cityMaterialCounts['count'] / totalCityCount) * 100, 2)

    totalMaterialCount = materialCountsTotal['count'].sum()
    materialCountsTotal['percentage'] = round(materialCountsTotal['count'] / totalMaterialCount * 100, 2)

    # return materials used in skyscraper in cities, AND return total skyscrapers using materials
    return cityMaterialCounts, materialCountsTotal


def pieChartTotal(dfTotal):
    dfTotal = dfTotal.sort_values(by='percentage', ascending=False).reset_index(drop=True)
    topNum = 5  # to show top 5 values
    fig1, ax1 = plt.subplots(figsize=(8, 10), layout='constrained')  # fig size for size, layout for values

    # Create the pie chart
    slices, texts, values = ax1.pie(
        dfTotal['percentage'],
        wedgeprops={"edgecolor": "black"},  # outline
        explode=(.05, .05, .05, 0, 0, 0, 0),  # separates the slices for cool visual effect
        autopct=lambda pct: ('%1.2f%%' % pct) if pct > dfTotal['percentage'].iloc[topNum] else '')  #shows top 5 values
    ax1.set_title("Most Popular Materials for Skyscrapers in US", fontsize=20)

    # Pie chart values
    for i, text in enumerate(values):
        if i < topNum:
            text.set_color('white')
            text.set_fontsize(8)
        else:
            text.set_text('')

    ax1.legend(
        slices,  # Link legend to pie slices, zip pairs the materials and the values together for later
        [f"{material}: {percentage:.2f}%" for material, percentage in zip(dfTotal['material'], dfTotal['percentage'])],
        title="Materials (with Percentages)",
        loc="upper left",
        bbox_to_anchor=(1, 0.25),  # Position legend outside chart
        fontsize=12)
    st.pyplot(fig1)


def pieChartCity(dfCity):
    dfCity = dfCity.sort_values(by='percentage', ascending=False).reset_index(drop=True)
    uniqueMaterials = dfCity['material'].nunique()  #for chart
    topN = min(5, uniqueMaterials)  # so that code doesn't break if city1 has 5, city 2 has 1 material
    fig2, ax2 = plt.subplots(figsize=(8, 10), layout='constrained')  # fig size for size, layout for values

    # Create the pie chart
    slices, texts, values = ax2.pie(
        dfCity['percentage'],
        wedgeprops={"edgecolor": "black"},  # outline
        explode=[0.1 if i < topN else 0 for i in range(len(dfCity))],
        # needs to change since city can have _ variety

        autopct=lambda pct: ('%1.2f%%' % pct) if pct > dfCity['percentage'].iloc[topN - 1]
        else '')  # shows top 5 values
    ax2.set_title("Most Popular Materials for Skyscrapers in US", fontsize=20)

    # Pie chart values
    for i, text in enumerate(values):
        if i < topN:
            text.set_color('white')
            text.set_fontsize(8)
        else:
            text.set_text('')

    ax2.legend(
        slices,  # Link legend to pie slices
        [f"{material}: {percentage:.2f}%" for material, percentage in zip(dfCity['material'], dfCity['percentage'])],
        title="Materials (with Percentages)",
        loc="upper left",
        bbox_to_anchor=(1, 0.25),  # Position legend outside chart
        fontsize=12)

    st.pyplot(fig2)


def numSkyscraper(df):
    # Question 2: How many skyscrapers are in a selected
    # city, and which selected cities have the most skyscrapers?
    numSkyscraperList = [(row['location.city']) for index, row in df.iterrows()]  # List
    numSkyscraperDf = pd.DataFrame(numSkyscraperList, columns=['location.city'])

    numSkyscraperCity = (numSkyscraperDf['location.city'].value_counts()
                         .reset_index(name='count'))  # Skyscraper in cities
    numSkyscraperCity.columns = ['location.city', 'count']

    #reset index --> numSkyscraperCity stays df, to be used with 'group_by'
    numSkyscraperCity = numSkyscraperCity.sort_values(by='count', ascending=False).reset_index(drop=True)
    return numSkyscraperCity


def skyscrapersHeight(df):
    # Question 3: What cities have an average height above
    # (or below) a selected height?
    heightList = [(row['location.city'], row['statistics.heightClean']) for index, row in df.iterrows()]  # list

    skyscraperHeightDf = (pd.DataFrame(heightList, columns=['location.city', 'statistics.heightClean'])
                          .rename(columns={'location.city': 'City',
                                           'statistics.heightClean': 'Average Height'}))  # list to dataframe
    avgHeightCities = skyscraperHeightDf.groupby('City')['Average Height'].mean().reset_index()  # avg height, stays df
    avgHeightCities.set_index('City', inplace=True)
    avgHeightCities['Average Height'] = avgHeightCities['Average Height'].round(2)
    return avgHeightCities


def customMap(df, heightRange, dotSize):
    st.header("Customized Map")
    df.rename(columns = {'location.latitudeClean': 'lat', 'location.longitudeClean': 'lon'}, inplace=True)
    df['statistics.heightClean'] = round(df['statistics.heightClean'], 2)

    mapFilteredDf = df[(df['statistics.heightClean'] >= heightRange[0]) &
                       (df['statistics.heightClean'] <= heightRange[1])]

    if mapFilteredDf.empty:
        st.write("There are no skyscrapers that meet your conditions.")
        st.write("")
        return

    st.write("")
    st.write("Displaying all skyscrapers within your selected height range.")

    view_state = pdk.ViewState(
        latitude = mapFilteredDf["lat"].mean(),
        longitude = mapFilteredDf["lon"].mean(),
        zoom = 4,
        pitch = 0)

    layer1 = pdk.Layer('ScatterplotLayer',
                       data = mapFilteredDf,
                       get_position = '[lon, lat]',
                       get_radius = dotSize,
                       get_color = [0, 0, 255],  # big red circle
                       pickable = True)

    # stylish tool tip
    toolTip = {"html": "Building Name:<br> <b>{name}</br>"
                       "<br/>Height: <b>{statistics.heightClean} meters</b>",
               "style": {"backgroundColor": "steelblue",
                         "color": "white",
                         "fontSize": "15px"}}

    heightMap = pdk.Deck(
        map_style='mapbox://styles/mapbox/outdoors-v11',
        initial_view_state=view_state,
        layers=[layer1],
        tooltip=toolTip)

    st.pydeck_chart(heightMap)


def main():
    st.set_page_config(page_title="Skyscraper Information Database", layout="wide",
                       initial_sidebar_state="expanded")
    st.sidebar.title("What do you want to know?")
    page = st.sidebar.radio("Go to", ["Home Page", "Skyscraper Materials", "Number of Skyscrapers",
                                      "Average Height of Skyscrapers across cities"])

    try:
        skyscrapers = pd.read_csv("skyscrapers.csv")
    except FileNotFoundError:
        print("The file 'skyscrapers.csv' was not found.")
        return

    data = cleanData(skyscrapers)
    dfMaterial, dfCitiesSkyscrapers, dfHeight = filterData(data)
    dfHeight = dfHeight.reset_index(drop=True)

    cityChoices = sorted({city for city in data['location.city']})
    defaultIndex = cityChoices.index('New York') if 'New York' in cityChoices else 0

    # _________________________________________________________________________________________
    if page == "Home Page":
        st.write("Hello Dear User! Want to learn about skyscrapers? You've come to the right place!")
        st.write("If you're impressed, please feel free to donate!")
        st.write("https://tinyurl.com/ydf5wj3j")
    #_________________________________________________________________________________________
    if page == "Skyscraper Materials":
        city = st.selectbox("Choose a City!", cityChoices, index=defaultIndex)
        materialCity, materialTotal = skyscrapersMaterial(dfMaterial, city)  # Q1
        st.title(f"Skyscraper Materials in {city}")
        pieChartCity(materialCity)
        if not materialCity.empty:
            popularMaterialCity = materialCity['material'].iloc[0]
            popularPercentageCity = materialCity['percentage'].iloc[0]
            st.write(f"One of the most popular skyscraper materials in {city} is {popularMaterialCity},"
                     f" accounting for {popularPercentageCity:.2f}% of buildings.")
        else:
            st.write(f"No material data available for {city}.")

        st.title(f"Total Percentage of Skyscraper Materials Across Cities in the US")
        pieChartTotal(materialTotal)
        popularMaterialCountry = materialTotal['material'].iloc[0]
        popularPercentageCountry = materialTotal['percentage'].iloc[0]
        st.write(f"This compares to the nationwide percentages, with {popularMaterialCountry} "
                 f"accounting for {popularPercentageCountry:.2f}% of all skyscraper construction material in the US.")
    # _________________________________________________________________________________________
    if page == "Number of Skyscrapers":
        st.title("Number of Skyscrapers by City")
        skyscrapersCities = numSkyscraper(dfCitiesSkyscrapers)  # Q2
        # city, and which selected cities have the most skyscrapers?
        selected = st.multiselect("Select Cities: ", skyscrapersCities['location.city'])

        skyscrapers = {}  # dictionary, initialize
        for city in selected:
            skyscrapers[city] = int(skyscrapersCities[skyscrapersCities['location.city'] == city]['count'].values[0])

        if skyscrapers:
            df = pd.DataFrame(list(skyscrapers.items()), columns=['City', 'Count'])
            df.set_index('City', inplace=True)  # Plot bar chart

            fig3, ax3 = plt.subplots(figsize=(15, 10), layout='tight')  # bar chart setup
            bars = ax3.barh(df.index, df['Count'], color='darkblue', label='Skyscrapers Count')
            ax3.set_title("Number of Skyscrapers by City", fontsize=15)
            ax3.set_xlabel('Number of Skyscrapers', fontsize=12)
            ax3.set_ylabel('City', fontsize=12)

            # add legend
            ax3.legend(
                title="City Skyscrapers",
                loc="upper left",
                bbox_to_anchor=(1, 0.25),  # Position legend outside chart
                fontsize=15)

            # more descriptive, numbers for each
            for bar in bars: ax3.text(bar.get_width(),
                                      bar.get_y() + bar.get_height() / 2,
                                      f'{bar.get_width():.0f}',
                                      va='center', ha='left', fontsize=15)
            st.pyplot(fig3)

            cityMostSkyscrapers = max(skyscrapers, key=skyscrapers.get)  #pull from dict
            cityLeastSkyscrapers = min(skyscrapers, key=skyscrapers.get)

            st.write(f"Out of your selected cities, the city with the highest "
                     f"amount of skyscrapers is {cityMostSkyscrapers}.")
            st.write(f"The city with the least skyscrapers out of your "
                     f"selected cities is {cityLeastSkyscrapers}.")

            rangeSkyscrapers = max(skyscrapers.values()) - min(skyscrapers.values())
            st.write(f"The difference in amount of skyscrapers within these cities is "
                     f"{rangeSkyscrapers} skyscrapers.")

            if max(skyscrapers.keys()) == min(skyscrapers.keys()):
                st.write("This is because you chose only 1 city. For more info, choose more cities.")
    # _________________________________________________________________________________________
    # Question 3: What cities have an average height above (or below) a selected height?
    if page == "Average Height of Skyscrapers across cities":
        st.title("Average Height of Skyscrapers by City")
        heightRange = st.slider("Select Height Range (meters)", 0, 600, (100, 200), 10)
        dotSize = st.slider("Select Dot Size on Map", 0, 50000, 25000, 100)
        customMap(dfHeight, heightRange, dotSize)

        st.write("View full table of information here: ")
        st.write(dfHeight)


# _________________________________________________________________________________________

if __name__ == "__main__":
    main()

