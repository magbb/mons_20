import math
import pandas as pd
import folium
import dhlab as dh
import streamlit as st
from streamlit_folium import st_folium

@st.cache_data
def load_metadata() -> pd.DataFrame:
    metadata = pd.read_excel("../newspapers.xlsx")
    return metadata

@st.cache_data
def count(word, limit=1000) -> pd.DataFrame:
    corpus = dh.Corpus(doctype="digavis", fulltext=word, order_by="random", limit=limit)
    counts = corpus.count(words=[word])
    corpus.frame["split_urn"] = corpus.frame["urn"].apply(lambda x: '_'.join(x.split("_")[0:3]))
    
    # merge with metadata
    metadata = load_metadata()
    corpus_metadata = corpus.frame.merge(metadata, left_on="split_urn", right_on="id")

    # merge with counts
    counts = counts.frame.transpose().reset_index()
    corpus_count_metadata = corpus_metadata.merge(counts, left_on="dhlabid", right_on="urn")

    return corpus_count_metadata

def create_map(corpus_count_metadata, word) -> folium.Map:
    map_data = corpus_count_metadata.groupby(by=["place_id", "place", "county", "long", "lat"])[[word]].sum().reset_index()

    # Ensure the 'latitude' and 'longitude' columns are numeric 
    map_data['lat'] = pd.to_numeric(map_data['lat'], errors='coerce')
    map_data['long'] = pd.to_numeric(map_data['long'], errors='coerce')
    map_data[word] = pd.to_numeric(map_data[word], errors='coerce') 
    map_data.dropna(subset=['lat', 'long', word], inplace=True)

    m = folium.Map(location=[62.4720, 32.4689], zoom_start=5)

    # Add markers to the map
    for i, row in map_data.iterrows():
        folium.CircleMarker(location=[row['lat'], row['long']],
                            radius=row[word] / 2, # Adjust the divisor to control the size
                            color='blue',
                            fill=True,
                            fill_color='blue').add_to(m)

    return m

def main():
    st.set_page_config(page_title="Kart fra aviser", page_icon="📚", layout="wide")
    st.title("Kart fra aviser")

    word = st.text_input("Søkeord")

    if word:
        corpus_count_metadata = count(word)

        map = create_map(corpus_count_metadata, word)

        output = st_folium(
            map, width=2000, height=600
        )


if __name__ == "__main__":
    main()
