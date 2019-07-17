import os
import pickle
import requests
from collections import namedtuple, defaultdict

import folium
import xmltodict
import numpy as np
from folium.plugins import HeatMap

import warnings
warnings.filterwarnings('ignore')

ZillowHomeInfo = namedtuple('ZillowHomeInfo', 'zpid lat lon value')
session = requests.session()


def get_search_results(address, city_state):
    params = {
        'zws-id': os.environ['ZILLOW_WSID'],
        'address': address,
        'citystatezip': city_state.replace(' ', '+')
    }
    response = session.get('https://www.zillow.com/webservice/GetSearchResults.htm', params=params)
    if not response.ok:
        raise Exception('Fail code ({}): {}'.format(response.status_code, response.text))

    homes = list()
    d = xmltodict.parse(response.text)
    try:
        results = d['SearchResults:searchresults']['response']['results']['result']
        code = int(d['SearchResults:searchresults']['message']['code'])
    except Exception:
        code = -1

    if code == 0 and isinstance(results, list):
        for res in results:
            zpid = res.get('zpid')
            if zpid is not None:
                # look for real estate details
                real_estate = res.get('localRealEstate')
                if real_estate is not None:
                    # look for the house valuation
                    value = real_estate.get('region', {}).get('zindexValue')
                    if value is not None:
                        # if a valuation exists, parse it and lat/lon info
                        value = float(value.replace(',', ''))
                        address = res.get('address')
                        if address is not None:
                            lat, long = address.get('latitude'), address.get('longitude')
                            homes.append(ZillowHomeInfo(zpid=zpid, lat=float(lat), lon=float(long), value=value))

    return homes


def get_comps(zpid):

    def inner(comp):
        if comp is not None:
            try:
                zpid = comp.get('zpid')
                lat = comp.get('address', {}).get('latitude')
                lon = comp.get('address', {}).get('longitude')
                value = comp.get('localRealEstate', {}).get('region', {}).get('zindexValue')
            except Exception:
                zpid = lat = lon = value = None

            if not any([e is None for e in [zpid, lat, lon, value]]):
                return {
                    'zpid': zpid,
                    'lat': float(lat),
                    'long': float(lon),
                    'value': float(value.replace(',', ''))
                }

    # make call to Zillow to get comps response
    params = {
        'zws-id': os.environ['ZILLOW_WSID'],
        'zpid': zpid,
        'count': 25
    }
    response = session.get('http://www.zillow.com/webservice/GetComps.htm', params=params)
    if not response.ok:
        raise Exception('Fail code ({}): {}'.format(response.status_code, response.text))

    # parse the response and create ZillowHomeInfo objects
    d = xmltodict.parse(response.text)
    code = int(d['Comps:comps']['message']['code'])
    if code == 0:
        comp_list = d['Comps:comps']['response']['properties']['comparables']['comp']
        for comp in map(inner, comp_list):
            if comp is not None:
                comp_info = ZillowHomeInfo(zpid=comp['zpid'], lat=comp['lat'], lon=comp['long'], value=comp['value'])
                yield comp_info


def meets_criteria(home):
    val = (
        home.lat > 33.6 and
        home.lat < 33.9 and
        home.lon < -84.2 and
        home.lon > -84.5
    )
    return val


def main():
    # set to True to generate a new heatmap for a city
    data_fn = 'data/data.pkl'
    out_fn = 'atlanta_heatmap.html'
    generate_new = False

    if generate_new:
        node_map = defaultdict(list)
        all_nodes = set()
        node_data = dict()
        msg = ''
        city = 'Atlanta'
        state = 'GA'
        print('City: {}'.format(city))
        n_iter = 0
        max_iter = np.inf
        size_target = 10000

        # get initial results to seed the graph
        homes = get_search_results(
            address=city,
            city_state='{city}+{state}'.format(city=city, state=state)
        )
        if len(homes) == 0:
            raise ValueError('No results found for city {}.'.format(city))

        for home in homes:
            node_data[home.zpid] = home

        done = False
        while len(homes) > 0 and not done:
            n_iter += 1

            home = homes.pop(-1)

            comps = get_comps(home.zpid)
            for comp in comps:

                if comp.zpid not in all_nodes:

                    if meets_criteria(comp):
                        # add to set of all nodes
                        all_nodes.add(comp.zpid)

                        # add to the queue
                        homes.append(comp)

                        # add to the id -> home info mapping
                        node_data[comp.zpid] = comp

                # add to the id -> comps mapping
                node_map[home.zpid].append(comp.zpid)

            # iterate until we have reached the desired condition
            if len(node_data) >= size_target:
                msg = 'Desired # elements reached'
                done = True
            elif n_iter == max_iter:
                msg = 'Maximum # iterations reached'
                done = True
            elif len(homes) == 0:
                msg = 'All homes traversed/dead end reached.'
                done = True
            # randomly print out how many homes we've found
            elif np.random.normal() < -2:
                print('# of homes found: [}'.format(len(node_data)))

            if done:
                print(msg)
                print('Found {} homes.'.format(len(homes)))

        with open(data_fn, 'wb') as fp:
            pickle.dump({'node_data': node_data, 'node_map': node_map}, fp)
    else:
        with open(data_fn, 'rb') as fp:
            data = pickle.load(fp)
        node_data, node_map = data['node_data'], data['node_map']

    print('# houses: {}'.format(len(node_data)))

    data = np.array([
        [home_info.lat, home_info.lon, home_info.value]
        for home_info in node_data.values()
    ])

    m = folium.Map(
        location=data[:, :2].mean(axis=0),
        control_scale=True,
        zoom_start=11
    )

    radius = 10
    hm = HeatMap(
        data,
        radius=radius,
        blur=int(2 * radius)
    )
    hm.add_to(m)

    m.save(out_fn)
    print('View the map with a browser by opening {}.'.format(out_fn))


if __name__ == '__main__':
    main()
