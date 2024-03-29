import pickle
import unittest

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
from obspy import UTCDateTime
from obspy import read
from obspy.clients.fdsn import Client

stations = {'Nagano, Japan': {'network': 'IU', 'station': 'MAJO', 'channel': 'BHZ', 'scale': 1.0,
                              'start': "2024-01-01T07:10:00", 'end': "2024-01-01T07:19:00", 'color': 'r',
                              'lat': 36.546, 'lng': 138.204},
            'Meade River, AK': {'network': 'AK', 'station': 'B20K', 'channel': 'BHZ', 'scale': 0.8,
                                'start': "2024-01-01T07:19:00", 'end': "2024-01-01T07:23:00", 'color': 'b',
                                'lat': 70.0079, 'lng': -157.1599},
            'Casper, WY': {'network': 'N4', 'station': 'K22A', 'channel': 'HHZ', 'scale': 0.6,
                           'start': "2024-01-01T07:23:00", 'end': "2024-01-01T07:28:00", 'color': 'g',
                           'lat': 42.65, 'lng': -106.32},
            'Pittsboro, NC': {'network': 'N4', 'station': 'V58A', 'channel': 'HHZ', 'scale': 0.5,
                              'start': "2024-01-01T07:28:00", 'end': "2024-01-01T07:53:00", 'color': 'k',
                              'lat': 35.79, 'lng': -79.11
                              },
            }

t = UTCDateTime(2024, 1, 1, 7, 8, 0)  # start point for waveform charts


class TestCases(unittest.TestCase):
    def test_iris(self):
        st = read()  # load example seismogram
        st.filter(type='highpass', freq=3.0)
        st = st.select(component='Z')
        st.plot()

    def test_iris_waveforms(self):
        seconds = 1700

        client = Client("IRIS")

        fig = plt.figure(figsize=(16, 9))

        for label, stationinfo in stations.items():
            picklefilename = f'waveforms_{seconds}.pickle'
            try:
                file = open(picklefilename, 'rb')
                data = pickle.load(file)
                file.close()
            except Exception as e:
                print(e)
                data = {}

            if label not in data:
                print(f'fetching waveforms for {label}')
                st = client.get_waveforms(stationinfo['network'], stationinfo['station'], "*", stationinfo['channel'],
                                          t, t + seconds)
                data[label] = st
                file = open(picklefilename, 'wb')
                pickle.dump(data, file)
                file.close()
            st = data[label]
            tr = st[0]

            x_bold = []
            x_dim = []
            y_bold = []
            y_dim = []
            m = max(tr.data)
            print(label, m)
            l = len(tr.data)
            for n, (date, value) in enumerate(zip(tr.times("utcdatetime"), tr.data)):
                if date >= UTCDateTime(stationinfo['start']):
                    if date < UTCDateTime(stationinfo['end']):
                        x = x_bold
                        y = y_bold
                    else:
                        x = x_dim
                        y = y_dim
                    x.append(date)
                    y.append(value * (32471296 / m) * stationinfo['scale'])

            plt.plot(x_bold, y_bold, f"{stationinfo['color']}-", label=label, alpha=1, )
            plt.plot(x_dim, y_dim, f"{stationinfo['color']}-", label=None, alpha=.2, )

        plt.tight_layout()
        plt.axis('off')
        plt.legend()

        filename = 'images/waveforms.png'
        plt.savefig(filename, dpi=300)

    def test_map(self):

        fig = plt.figure(figsize=(12, 7))

        # recenter projection on the Pacific
        usemap_proj = ccrs.PlateCarree(central_longitude=180)
        usemap_proj._threshold /= 20.  # to make greatcircle smooth

        ax = plt.axes(projection=usemap_proj)
        # set appropriate extents: (lon_min, lon_max, lat_min, lat_max)
        ax.set_extent([105, 315, -35, 85], crs=ccrs.PlateCarree())

        geodetic = ccrs.Geodetic()
        plate_carree = ccrs.PlateCarree(central_longitude=180)

        # Plot map markers for stations
        for station_name, station_data in stations.items():
            ax.plot(station_data['lng'], station_data['lat'], markersize=10, marker='o',
                    color=station_data['color'], transform=ccrs.PlateCarree())

        # plot greatcircle arc
        gcc = ax.plot([stations['Nagano, Japan']['lng'], stations['Pittsboro, NC']['lng']], [stations['Nagano, Japan']['lng'], stations['Pittsboro, NC']['lat']],
                      color='black', transform=ccrs.Geodetic())

        ax.add_feature(cfeature.LAND, color='lightgray')

        filename = "images/map.png"
        plt.tight_layout()
        plt.axis('off')
        plt.savefig(filename, dpi=300)


if __name__ == '__main__':
    unittest.main()