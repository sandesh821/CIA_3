#Copyright (c) Microsoft. All rights reserved.

### Import Packages ###
from  dash import dcc, html,ctx
from dash.dependencies import Input, Output
import dash_daq
import dash

### Import Dash Instance and Pages ###
from workflow.main import app
from workflow.pages import runtracking,erroranalysis,sitesetup,experimentDetails,home,goliveconfig
from workflow.common.common import *

### Page container ###
page_container = html.Div(
    children=[
        # represents the URL bar, doesn't render anything
        dcc.Location(
            id='url',
            refresh=False,
        ),

        html.A([
            html.Img(
                src=app.get_asset_url('homebtn.png'),
                className = "homeBtn"
                )
            ], href='/'),
        # content will be rendered in this element
        html.Div(id='page-content'),
        dcc.Store(id='newExperiment', storage_type='session'),
        dcc.Store(id='existingExperiment', storage_type='session'),
        dcc.Store(id='experimentStore', storage_type='session'),
        # Master style sheet
        html.Link(
            rel='stylesheet',
            href='/static/stylesheet.css?v=02'
        )
    ]
)

### Set app layout to page container ###
app.layout = page_container

### Update Page Container ###
@app.callback(
    Output(
        component_id='page-content',
        component_property='children',
        ),
    [Input(
        component_id='url',
        component_property='pathname',
        )  
        ]
)
def display_page(pathname): 
    if pathname == '/':
        return home.homepageLayout 
    # TODO: Need to discuss ( No page should be directly accessible, it should go from home page after selection of experiment set only)
    elif pathname == '/siteinformation':
        return sitesetup.layout     
    elif pathname == '/sitesetup':  
        return sitesetup.layout 
    elif pathname == '/runtracking':
        return runtracking.layout
    elif pathname == '/erroranalysis':
        return erroranalysis.layout
    elif pathname == '/provenance':
        return experimentDetails.layout
    elif pathname == '/goliveconfig':
        return goliveconfig.layout
    else:
        return '404'
