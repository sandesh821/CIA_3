#Copyright (c) Microsoft. All rights reserved.
import plotly.graph_objs as go
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize

class HexPlotly:
    def __init__(self, x, y, gridsize=100, bins=None, cmap=plt.cm.Blues):
        self.x = x
        self.y = y
        self.gridsize = gridsize
        self.bins = bins
        self.cmap = cmap

    def _compute_hexbin(self):
        """Computes the hexagonal binning
        """
        collection = plt.hexbin(self.x, self.y, bins=self.bins, gridsize=self.gridsize)
        plt.close()

        pts_in_hexagon = collection.get_array()

        # compute colors for the svg shapes
        colors = ["#%02x%02x%02x" % (int(r), int(g), int(b)) for r, g, b, _ in 255 * self.cmap(Normalize()(pts_in_hexagon))]

        # coordinates for single hexagonal patch
        hx = [0, .5, .5, 0, -.5, -.5]
        hy = [-.5 / np.cos(np.pi / 6), -.5 * np.tan(np.pi / 6), .5 * np.tan(np.pi / 6),
              .5 / np.cos(np.pi / 6), .5 * np.tan(np.pi / 6), -.5 * np.tan(np.pi / 6)]

        # number of hexagons needed
        m = len(collection.get_offsets())

        # scale of hexagons
        n = (self.x.max() - self.x.min()) / self.gridsize

        # y_scale to adjust for aspect ratio
        y_scale = (self.y.max() - self.y.min()) / (self.x.max() - self.x.min())

        # coordinates for all hexagonal patches
        hxs = np.array([hx] * m) * n + np.vstack(collection.get_offsets()[:, 0])
        hys = np.array([hy] * m) * n * y_scale + np.vstack(collection.get_offsets()[:, 1])

        return hxs.tolist(), hys.tolist(), colors, pts_in_hexagon

    def plotter(self, width, height):
        x, y, color_list, pts_in_hexagon = self._compute_hexbin()
        shape_container = []
        hover_point_x = []
        hover_point_y = []

        for x_list, y_list, color in zip(x, y, color_list):
            # Create the svg path based on the computed points

            svg_path = 'M {},{} L {},{} L {},{} L {},{} L{},{} L{},{}' \
                .format(x_list[0], y_list[0],
                        x_list[1], y_list[1],
                        x_list[2], y_list[2],
                        x_list[3], y_list[3],
                        x_list[4], y_list[4],
                        x_list[4], y_list[1])

            # Create hover point from the hexagon, witch is the center of gravity
            hover_point_x.append(round((max(x_list) - min(x_list)) / 2 + min(x_list), 2))
            hover_point_y.append(round((max(y_list) - min(y_list)) / 2 + min(y_list), 2))

            shape_container.append({
                "fillcolor": color,
                "line": {
                    "color": color,
                    "width": 1.5
                },
                "path": svg_path,
                "type": "path"
            })

        trace = go.Scattergl(x=hover_point_x,
                             y=hover_point_y,
                             mode='markers'
                             )

        trace['marker']['colorbar'] = {"title": "#points"}
        trace['marker']['reversescale'] = False
        trace['marker']['colorscale'] = self.cmap.__dict__['name']
        trace['marker']['color'] = pts_in_hexagon
        trace['marker']['size'] = 0
        trace['text'] = list(map(lambda z: 'Amount of points: {}'.format(int(z)), pts_in_hexagon))

        layout = {'shapes': shape_container,
                  'width': width,
                  'height': height,
                  'hovermode': 'closest',
                  'paper_bgcolor' : 'rgba(0,0,0,0)',
                  'plot_bgcolor' : 'rgba(0,0,0,0)'
        }

        fig = go.Figure(dict(data=[trace], layout=layout))
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=False)
        return fig

def gen_data():
    N = 1000
    random_x = np.random.randn(N)
    random_y = np.random.randn(N)
    return random_x, random_y

if __name__ == '__main__':
    random_x, random_y = gen_data()
    hp = HexPlotly(random_x, random_y, gridsize=20, cmap=plt.cm.Blues)

    fig = hp.plotter(width=850, height=700)
    fig.show()
