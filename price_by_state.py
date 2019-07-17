import os
import json
import requests

import folium
import numpy as np
import pandas as pd
from branca import colormap

import warnings
warnings.filterwarnings('ignore')


def local_states_geo_json():
    fn_states_geo = os.path.join('data', 'us-states.json')
    if not os.path.exists(fn_states_geo):
        url = 'https://raw.githubusercontent.com/python-visualization/folium/master/examples/data'
        us_states = '{}/us-states.json'.format(url)
        geo_json_states = requests.get(us_states).json()
        with open(fn_states_geo, 'w') as fp:
            json.dump(geo_json_states, fp)

    return fn_states_geo


def make_color_map(df, col_keys, col_data):

    values = df[col_data].values
    df.set_index('State', drop=True, inplace=True)
    state_to_value = {state: df.loc[state, 'MedianPPSQFT'] for state in df.index}

    cmap = colormap.linear.OrRd_07.scale(
        int(np.percentile(values, 5)),
        int(np.percentile(values, 95))
    )
    cmap.caption = 'Zillow Median Price Per Square Foot ($ in thousands)'

    def value_to_color(entry):
        return {
            'fillColor': cmap(state_to_value.get(entry['id'], 0)),
            'weight': 1,
            'fillOpacity': 1.0,
        }

    return cmap, value_to_color


def main():
    # load data downloaded from Zillow
    out_fn = 'price_by_state.html'
    df = pd.read_csv('data/State_MedianValuePerSqft_AllHomes.csv')
    data = df[['State', df.columns[-1]]]
    data.rename(columns={df.columns[-1]: 'MedianPPSQFT'}, inplace=True)

    # create a color map
    cmap, f_value_to_color = make_color_map(data, col_keys='State', col_data='MedianPPSQFT')

    # add the US states Geo JSON data to the Map
    state_values = folium.GeoJson(
        local_states_geo_json(),
        style_function=f_value_to_color
    )

    m = folium.Map(location=[37, -102], zoom_start=4)
    cmap.add_to(m)
    state_values.add_to(m)
    m.save(out_fn)
    print('View the map with a browser by opening {}.'.format(out_fn))


if __name__ == '__main__':
    main()
