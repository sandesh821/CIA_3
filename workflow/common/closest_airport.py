#Copyright (c) Microsoft. All rights reserved.
import pandas as pd
import h3

"""
Larger Dataset - https://ourairports.com/data/
Main Source - https://gist.githubusercontent.com/fletchjeff/b60f46ca3c1aa51e9aea9fd86d0ab433/raw/81ee446939110daf8b5c3a79425ccf1100070578/airports.csv
"""

class ClosestAirport:
    def __init__(self, lat, lon):
        self.df = self._read_airport_file()
        self.point_lat = lat
        self.point_lon = lon
        self._calculate_distances()
        self.cols = ['Name','ICAO','Latitude','Longitude', 'Tz database time zone', 'Dist', 'Country']

    def _read_airport_file(self):
        df = pd.read_csv("workflow/common/airports.txt")
        return df

    def _calculate_distances(self):
        self.df['Dist'] = self.df.apply(lambda row: h3.point_dist((row['Latitude'], row['Longitude']), (self.point_lat, self.point_lon)), axis=1)
        self.df.sort_values("Dist", inplace=True)

    def _cleaner(self, df):
        return df.reset_index().drop(['index'], axis=1)

    def get_closest_airports_by_distance(self, distance=100):
        return self._cleaner(self.df[self.df['Dist']<=distance][self.cols])

    def get_closest_airports_by_number(self, number = 5):
        return self._cleaner(self.df[self.cols][:number])

if __name__ == '__main__':
    """
    longhorn_site_lat, longhorn_site_lon = 34.313209,-101.2370824
    ca = ClosestAirport(longhorn_site_lat, longhorn_site_lon)
    print(ca.get_closest_airports_by_distance(161))
    print(ca.get_closest_airports_by_number(6))
    """
    harvest2_lat, harvest2_lon = 43.7819895,-83.2106631
    ca = ClosestAirport(harvest2_lat, harvest2_lon)
    print(ca.get_closest_airports_by_distance(161))
    print(ca.get_closest_airports_by_number(6))


