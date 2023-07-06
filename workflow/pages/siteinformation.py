#Copyright (c) Microsoft. All rights reserved.
import dash
from dash import html , dcc, ctx
from dash.dependencies import Input, Output ,State
import dash_bootstrap_components as dbc
import pandas as pd
import dash_daq as daq
import plotly.express as px
from dash.exceptions import PreventUpdate
from dash import dash_table as dt
import json

# Import master app object
from workflow.main import app

### Import utilities ###
from utilities.dboperations import dboperations
from workflow.common.getdata import * 

from workflow.common.common import *
from workflow.common.config import GET_WIND_TURBINES_SP, SAVE_SET_EXPERIMENT_DETAILS_SP, DATA_SAVE_MESSAGE
from workflow.common.closest_airport import * 


# Get windturbines on page load
def windturbines():
    df = dboperations.executeStoredProcedure(GET_WIND_TURBINES_SP,None,None,"dbo",2)
    names = df['manufacturer'].unique() 
    return df,names

df,names  = windturbines()

# default Geo Map Initial values
def geoMapFig(geo_df,zoom=0):
    fig = px.scatter_mapbox(
        geo_df,
        lat="lat",
        lon="long",
        hover_name="LocationsType",
        hover_data=["Name","Dist","ICAO"],
        color ="LocationsType",
        zoom=zoom,
        height=500,
        opacity = 1
    )
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    fig.update_traces(marker=dict(size=16),selector=dict(mode='markers',type ='scattermapbox'))
    fig.update_layout(legend = dict(yanchor = "bottom" , y = 0.01,xanchor = 'left' ,x = 0.01))
    #fig.update_layout(showlegend=False)
    return fig

# Airport Source columns list
airporttblCols = ['Name', 'ICAO', 'Latitude', 'Longitude', 'Tz database time zone',
       'Dist', 'Country']
airporttblColsOptions = []
for i in airporttblCols:
    airporttblColsOptions.append({'name': i,'id': i,'deletable': False,'renamable': False } )

def airportsTable(lat,long):
    ClosestAirportObj = ClosestAirport(lat,long)
    df = ClosestAirportObj.get_closest_airports_by_number(5)
    return df

windLayout = [            
                                    dbc.Row([  
                                            dbc.Col([   
                                                    html.Label('Manufacturer')
                                                ],width = 3),
                                            dbc.Col([   
                                                    dcc.Dropdown(id='manufact_dropdown', style={'width': '100%'})
                                                ],width = 6)
                                        ]),
                                    dbc.Row([  
                                            dbc.Col([ 
                                                html.Label('Turbine')
                                            ],width = 3),
                                            dbc.Col([ 
                                                dcc.Dropdown( id='turbine_dropdown', style={'width': '100%'})
                                            ],width = 6)
                                        ]),
                                    dbc.Row([  
                                        dbc.Col([
                                                html.Label('Total Number of Turbines')
                                            ],width = 4),
                                        dbc.Col([
                                                dcc.Input( id = 'totturbines',type = 'number', style={'width': '100px'})
                                            ],width = 3)
                                        ]),
                                    dbc.Row([
                                            dbc.Col([
                                                html.Label('Turbine Rated Power (MW)')
                                            ],width = 4),
                                            dbc.Col([
                                                daq.NumericInput( id = 'maxcapactiy-output',disabled=True, style={'width': '100%'})
                                            ],width = 3)
                                        ]),
                                    dbc.Row([
                                            dbc.Col([
                                                html.Label('Site Nominal Power (MW)')
                                            ],width = 4),
                                            dbc.Col([
                                                daq.NumericInput( id = 'sitetotalcapacity', style={'width': '100%'})
                                            ],width = 3)
                                    ]),
                            ]

demandLayout = [
            dbc.Row ([ 
                dbc.Col ([ 
                            html.Div([            
                                    dbc.Row([  
                                        dropdownTags("ResourceType","resourceType_dropDown",6,True,False,[
                                            {"label": "Residential", "value": 'Residential'},
                                            {"label": "Office", "value": 'Office'},
                                            {"label": "Manufacturing Unit", "value": 'Manufacturing Unit'},
                                            {"label": "Retail", "value": 'Retail'},
                                            {"label": "Misc", "value": 'Misc'}]
                                            ),
                                        dropdownTags("Consumption","consumption_dropDown",6,True,False,[
                                            {"label": "Weekend", "value": 'weekend'},
                                            {"label": "Weekday", "value": 'weekday'},
                                            {"label": "All days", "value": 'all days'}]
                                            )
                                    ]),
                                    dbc.Row([
                                            dbc.Col([
                                                    html.Label('Winter set point')
                                            ],width = 3),
                                            dbc.Col([
                                                    dcc.Input( id = 'wintersetpoint',placeholder="Enter winter set point",style={'width': '100%'})
                                            ],width = 3),
                                            dbc.Col([
                                                    html.Label('Summer set point')
                                            ],width = 3),
                                            dbc.Col([
                                                    dcc.Input( id = 'summersetpoint',placeholder="Enter summer set point",style={'width': '100%'})
                                            ],width = 3)
                                    ])
                                ])
                            ])
                        ])
                    ]


solarLayout = [
            dbc.Row ([  
                dbc.Col ([ 
                            html.Div([            
                                    dbc.Row([  
                                             dbc.Col([
                                                    html.Label('Resource Type')
                                            ],width = 3),
                                        dbc.Col([
                                        dcc.Dropdown(id = "solarresourceType_dropDown",options = [
                                            {"label": "Fixed", "value": 'Fixed'},
                                            {"label": "ManualTracker", "value": 'ManualTracker'},
                                            {"label": "PassiveTracker", "value": 'PassiveTracker'},
                                            {"label": "ActiveSingleAxis", "value": 'ActiveSingleAxis'},
                                            {"label": "ActiveDualAxis", "value": 'ActiveDualAxis'}])                                       
                                    ] ,width = 3)
                                    ]),

                                    dbc.Row([
                                            dbc.Col([
                                                    html.Label('Overall Capacity (MW)')
                                            ],width = 3),
                                            dbc.Col([
                                                    dcc.Input( id = 'overallcapacity',placeholder="Enter Overall Capacity",style={'width': '100%'})
                                            ],width = 3)
                                    ]),

                                    dbc.Row([
                                            dbc.Col([
                                                    html.Label('DC/AC Ratio')
                                            ],width = 3),
                                            dbc.Col([
                                                    dcc.Input( id = 'dcfactor',placeholder="Enter DC/AC Ratio",min=0,style={'width': '100%'})
                                            ],width = 3)
                                    ]) 
                                ])
                            ])
                        ])
                    ]


priceLayout = [
            dbc.Row ([ 
                dbc.Col ([ 
                            html.Div([            
                                    dbc.Row([  
                                             
                                             
                                            dropdownTags("ResourceType","priceResourceType",6,False,False,[
                                            {"label": "Day-Ahead", "value": 'Day-Ahead'},
                                            {"label": "Real-Time", "value": 'Real-Time'},
                                            {"label": "Ancilliary", "value": 'Ancilliary'},
                                            {"label": "Misc", "value": 'Misc'}]
                                            ),  
                                             dropdownTags("Geaography List","geoList",6,False,False
                                            ),
                                            dbc.Col([ html.Label('Region'),
                                                    dcc.Input( id = 'region',type = 'text',placeholder="Enter Region",style={'width': '100%'})
                                            ],width = 6)
                                    ])
                                   
                                ])
                            ])
                        ])
                    ]


latlong_layout = [
      dbc.Row([  
                dbc.Col([
                        html.Label('Latitude')
                ],width = 3),
                dbc.Col([
                        dcc.Input( id = 'lat',min=-90,max=90,style={'width': '100%'})
                ],width = 3),
                dbc.Col([
                        html.Label('Longitude')
                ],width = 3),
                dbc.Col([
                        dcc.Input( id = 'long',min=-180,max=180,style={'width': '100%'})
                ],width = 3)
        ]),
        dbc.Row([  
                dbc.Col([
                html.Label('Search Type'),
                dcc.RadioItems(options=[
                        {"label": "Site", "value": 'site'},
                    {"label": "Site + Nearest Airports", "value": 'siteandairports'}], 
                    id="locationsBtn" ,value = 'site'
                    )

                ] , width = 6)]),
        
        dbc.Row([
            html.I('***Note : Airport weather data can be downloaded from various sources.***')
        ]),
        dbc.Row([  
                    dbc.Col([
                        html.Button(id = "searchBtn", children = 'Search',n_clicks = 0)
                    ], width=3)
        ])
     ]


layout = dbc.Container([
        html.Div([
            dbc.Row ([ 
                dbc.Col ([ 
                            html.Div(windLayout,id = "windLayout", style={'display' : 'none'}),
                            html.Div(demandLayout,id = "demandLayout", style={'display' : 'none'}),
                            html.Div(solarLayout,id = "solarLayout", style={'display' : 'none'}),
                            html.Div(priceLayout,id = "priceLayout", style={'display' : 'none'}),
                            html.Div(latlong_layout,id = "latlong_layout", style={'display' : 'none'}) ,
                            dbc.Row([  
                            dbc.Col([
                                html.Button(id = "saveSiteInformation" , children = 'save' ,n_clicks = 0, disabled=True)
                            ], width=3)                                                
                    ]),
                getLoadingElement("pageLoading")
                ]) ,
                dbc.Col ([
                        html.Div([
                                dbc.Row([
                                    dbc.Col([
                                        html.Div(children=[],id = 'getgraph'),
                                           # dcc.Graph(id='graph', config={'displayModeBar': False, 'scrollZoom': True}
                                            ])
                                        ])
                                ]),
                        ])
                    
                ]),
            
            getModalPopup("sitePageModal","Alert",""),
            getModalPopup("siteInfoSavePageModal","Alert","")
        ]),
        html.Div(children=[],id="hidden_for_callbacks", style={'display' : 'none'})
    ] ,id="siteInformationContainer",fluid = True)

def get_graph(fig):
    return dcc.Graph(id = 'graphname',figure = fig)
     
@app.callback( Output('getgraph', 'children'),
                Output("sitePageModalBody","children"),
                Output("sitePageModal","is_open"),
                Input('searchBtn', 'n_clicks'),
                Input('experimentStore','data'),
                Input("sitePageModalClose", "n_clicks"),
                State('lat', 'value'),
                State('long', 'value'),
                State('locationsBtn' , 'value'),
            )
def update_figure(clicks,data,closeClicks,latvalue,longvalue,locationsTypeValue):
    if data["entityType"] =='price' :
        dash.no_update,"",False
    else : 
        lat = [0]
        long = [0]
        zoom = 0
        if "experimentSetDetails" in data.keys():
            experimentSetDetails = data["experimentSetDetails"]
            lat = experimentSetDetails["Lat"]
            long =experimentSetDetails["Long"]
            zoom = 3
        LocationsType = ['Site']
        Name = ['Site Location']
        Dist = [0]
        ICAO = ['ICAO']
        geo_df = pd.DataFrame({'lat' : lat , 'long' : long , 'LocationsType' : LocationsType , 'Name' : Name , 'Dist' : Dist ,'ICAO':ICAO})
        
        initfig = geoMapFig(geo_df,zoom)

        if closeClicks > 0 and ctx.triggered_id == "sitePageModalClose":
            return get_graph(initfig),"",False
        if clicks > 0 :
            if longvalue is None  or latvalue is None  :
                validMesage =  "Latitude and Longitude Fields are Mandatory"
                data=None
                return get_graph(initfig),validMesage,True
            # if the function is triggered at app load, this will disable the button
            if latvalue is not None and longvalue is not None :
                latvalue = float(latvalue)
                longvalue = float(longvalue)
                lat = [latvalue]
                long = [longvalue]
                LocationsType = ['Site']
                Name = ['Site Location']
                ICAO = ['ICAO']
                Dist = [0]
                geo_df = pd.DataFrame({'lat' : lat , 'long' : long , 'LocationsType' : LocationsType , 'Name' : Name , 'Dist' : Dist , 'ICAO' :ICAO})
                if  locationsTypeValue == 'siteandairports' :
                    df = airportsTable(latvalue,longvalue)
                    df = df[['Name','Latitude','Longitude','Dist','ICAO']]
                    df['LocationsType'] = 'Nearest Airports'
                    df.rename(columns = {'Latitude' :'lat' , 'Longitude' :'long'} , inplace = True)
                    geo_df = pd.concat([geo_df,df],axis = 0)
                fig = geoMapFig(geo_df,zoom = 3)
                return get_graph(fig),"",False
        return get_graph(geoMapFig(geo_df,zoom)),"",False

# Manufacturer drop down callback
@app.callback(
    Output('turbine_dropdown','options' ) ,
    [Input('manufact_dropdown','value') ],
    State('experimentStore','data'))
def displayClick2(manu_val,storeData):
    if manu_val is not None:
        opts = df[(df['manufacturer'] == manu_val) & (df['entitytype'] == storeData["entityType"])]['turbine'].unique()
        options=[{'label':opt, 'value':opt} for opt in opts]
        return options
    else:
        raise PreventUpdate()

# Update max capacity on the basis of manufacturer and tubine selection
@app.callback(
    Output('maxcapactiy-output','value' ),
    Input('turbine_dropdown' , 'value'),
    [State('manufact_dropdown','value' ) ,
    State('experimentStore','data')])
def displayClick3(turb_val,manu_val,storeData):
    if turb_val is not None  : 
        df_max = df[(df['manufacturer'] == manu_val) & (df['entitytype'] == storeData["entityType"]) &(df['turbine'] == turb_val)]
        df_max = df_max.iloc[:,3:]
        max = int(df_max.max(axis = 1)) /1000
        return max

@app.callback(
    Output('sitetotalcapacity','value' ) ,
    [Input('totturbines','value') , Input('maxcapactiy-output' ,'value') ])
def displayClick2(totalturbines,maxcapacity):
    if totalturbines is None :
        max_capacity = 0
    else :
        max_capacity = totalturbines * maxcapacity
    return max_capacity

# Enable save button, if any input is changed
@app.callback(Output('saveSiteInformation','disabled'),
                [
                    Input('manufact_dropdown' , 'value'),
                    Input('turbine_dropdown' , 'value'),
                    Input('totturbines' , 'value'),
                    Input('maxcapactiy-output' , 'value'),
                    Input('sitetotalcapacity' , 'value'),
                    Input('lat', 'value'),
                    Input('long', 'value'),
                    # Demand layout inputs
                    Input('consumption_dropDown' , 'value'),
                    Input('resourceType_dropDown' , 'value'),
                    Input('wintersetpoint', 'value'),
                    Input('summersetpoint', 'value'),
                    # Solar layout inputs
                    Input('solarresourceType_dropDown' , 'value'),
                    Input('overallcapacity' , 'value'),
                    Input('dcfactor', 'value'),

                    # Price layout inputs
                    Input('priceResourceType' , 'value'),
                    Input('geoList' , 'value'),
                    Input('region', 'value')
                ]
            )
def enableSaveButton(manufacturer,turbine,totturbine,maxcapacity,sitecapacity,lat,long,consumption_dropDown,resourceType_dropDown,wintersetpoint,summersetpoint,solarresourceType_dropDown,overallcapacity,dcfactor,priceResourceType , geoList ,region):
    if (manufacturer is not None or turbine is not None or totturbine is not None or maxcapacity is not None or sitecapacity is not None or lat is not None or long is not None or
        consumption_dropDown is not None or resourceType_dropDown is not None or wintersetpoint is not None or summersetpoint is not None  or solarresourceType_dropDown is not None  or overallcapacity  is not None or dcfactor is not None or
        priceResourceType  is not None  or geoList   is not None or region  is not None ):
        print("Enabled Save button")
        return False
    else:
        raise PreventUpdate()

# Save details to database and enable next button and tab
@app.callback([Output('tab-2','disabled'),Output("pageLoadingOutput","children"),
                Output("siteInfoSavePageModalBody","children"),
                Output("siteInfoSavePageModal","is_open")],
                [Input('saveSiteInformation', 'n_clicks'),
                Input('hidden_for_callbacks', 'children'),
                Input("siteInfoSavePageModalClose", "n_clicks")],
                [
                    # Wind layout inputs
                    State('manufact_dropdown' , 'value'),
                    State('turbine_dropdown' , 'value'),
                    State('totturbines' , 'value'),
                    State('maxcapactiy-output' , 'value'),
                    State('sitetotalcapacity' , 'value'),
                    State('lat', 'value'),
                    State('long', 'value'), 
                    # Demand layout inputs
                    State('consumption_dropDown' , 'value'),
                    State('resourceType_dropDown' , 'value'),
                    State('wintersetpoint', 'value'),
                    State('summersetpoint', 'value'),
                    # Solar layout inputs
                    State('solarresourceType_dropDown' , 'value'),
                    State('overallcapacity' , 'value'),
                    State('dcfactor', 'value'),
                    # Solar layout inputs
                    State('priceResourceType' , 'value'),
                    State('geoList' , 'value'),
                    State('region', 'value'),
                  
                    State('experimentStore','data')
                ]
            )
def enableNextTab(clicks,inp1,closeClicks,manufacturer,turbine,totturbine,maxcapacity,sitecapacity,lat,long,consumption_dropDown,
                resourceType_dropDown,wintersetpoint,summersetpoint,
                solarresourceType_dropDown,overallcapacity,dcfactor,
                priceResourceType , geoList ,region,data):
    if closeClicks is not None and closeClicks > 0 and ctx.triggered_id == "siteInfoSavePageModalClose":
        return [False, "","",False]
    try:
        if (clicks > 0):
            if data["entityType"] != "price":
                if lat is None or long is None :
                    message = 'All Fields are Mandatory'
                    print(message)
                    return [True, "",message,True]
            if data["entityType"] == "wind":
                if totturbine is None:
                    message = 'All Fields are Mandatory'
                    print(message)
                    return [True, "",message,True]
                obj = {
                    "Manufacturer" : manufacturer,
                    "Turbine" : turbine,
                    "TotalTurbines" : totturbine,
                    "MaxCapacity" : maxcapacity,
                    "SiteCapacity" : sitecapacity,
                    "Lat" : lat,
                    "Long" : long
                }
            elif data["entityType"] == "demand":
                if consumption_dropDown is None or resourceType_dropDown is None or wintersetpoint is None or summersetpoint is None:
                    message = 'All Fields are Mandatory'
                    return [True, "",message,True]
                obj = {
                    "consumption_dropDown" : consumption_dropDown,
                    "resourceType_dropDown" : resourceType_dropDown,
                    "wintersetpoint" : wintersetpoint,
                    "summersetpoint" : summersetpoint,
                    "Lat" : lat,
                    "Long" : long
                }
            
            elif data["entityType"] == "solar":
                if solarresourceType_dropDown  is None or overallcapacity is None or dcfactor is None :
                    message = 'All Fields are Mandatory'
                    return [True, "",message,True]
                obj = {
                    "solarresourceType_dropDown" : solarresourceType_dropDown,
                    "overallcapacity" : overallcapacity,
                    "dcfactor" : dcfactor,
                    "Lat" : lat,
                    "Long" : long
                } 
            elif data["entityType"] == "price":
                if priceResourceType  is None or geoList is None or region is None :
                    message = 'All Fields are Mandatory'
                    return [True, "",message,True]
                obj = {
                    "priceResourceType" : priceResourceType,
                    "geoList" : geoList,
                    "region" : region
                }
            inputDict = json.dumps(obj)
            # Save form details to database
            dboperations.executeStoredProcedure(SAVE_SET_EXPERIMENT_DETAILS_SP,"@ExperimentSetID =?, @SiteInformation= ?",(data["experimentsetid"],inputDict),"dbo",0)
            print("Saved site information!")
            return [False, "",DATA_SAVE_MESSAGE,True]
        elif "experimentSetDetails" in data.keys():
            return [False, "","",False]
        else:
            raise PreventUpdate()
    except:
        raise PreventUpdate()

@app.callback([Output('manufact_dropdown' , 'options'),
               Output('manufact_dropdown' , 'value'),
               Output('turbine_dropdown' , 'value'),
               Output('totturbines' , 'value'),
               # generic outputs
               Output('lat', 'value'),
               Output('long', 'value'),
               # Demand layout outputs
               Output('consumption_dropDown' , 'value'),
               Output('resourceType_dropDown' , 'value'),
               Output('wintersetpoint', 'value'),
               Output('summersetpoint', 'value'),
                # Solar layout outputs
               Output('solarresourceType_dropDown', 'value'),
               Output('overallcapacity', 'value'),
               Output('dcfactor', 'value'),
                # Price layout outputs 
               Output('priceResourceType', 'value'),
               Output('geoList', 'value'),
               Output('region', 'value')
               ], 
              [Input('hidden_for_callbacks', 'children')],
              State('experimentStore','data'))
def onLayoutLoad(inp1, data):
    opts = df[df['entitytype'] == data["entityType"]]['manufacturer'].unique()
    options=listToOptions(opts)
    print("Executing layout load")
    if data["experimenttype"] == "new":
        return [options,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update]
    else:
        if "experimentSetDetails" in data.keys():
            experimentSetDetails = data["experimentSetDetails"]
            if data["entityType"] == "wind":
                return [options,experimentSetDetails["Manufacturer"],experimentSetDetails["Turbine"],experimentSetDetails["TotalTurbines"],experimentSetDetails["Lat"],experimentSetDetails["Long"],dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update]
            elif data["entityType"] == "demand":
                return [dash.no_update,dash.no_update,dash.no_update,dash.no_update,experimentSetDetails["Lat"],experimentSetDetails["Long"],experimentSetDetails["consumption_dropDown"],experimentSetDetails["resourceType_dropDown"],experimentSetDetails["wintersetpoint"],experimentSetDetails["summersetpoint"],dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update]
            elif data["entityType"] == "solar":
                return [dash.no_update,dash.no_update,dash.no_update,dash.no_update,experimentSetDetails["Lat"],experimentSetDetails["Long"],dash.no_update,dash.no_update,dash.no_update,dash.no_update,experimentSetDetails["solarresourceType_dropDown"],experimentSetDetails["overallcapacity"],experimentSetDetails["dcfactor"],dash.no_update,dash.no_update,dash.no_update]
            elif data["entityType"] == "price":
                return [dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,experimentSetDetails["priceResourceType"],experimentSetDetails["geoList"],experimentSetDetails["region"]]
        else:
            raise PreventUpdate()

@app.callback([Output('windLayout' , 'style'),Output('demandLayout' , 'style'),Output('solarLayout' , 'style'),Output('priceLayout' , 'style'),Output('latlong_layout' , 'style'), Output("hidden_for_callbacks","children"),Output('geoList','options')], 
              [Input('data', 'children')],
              State('experimentStore','data'))
def onTabLoad(inp1, data):
    countries = getCountries()
    countries = list(countries['CountryName'].values)
    countriesOptions = listToOptions(countries)
    print("Executing tab 1 page load")
    if data["entityType"] == "wind":
        return [{'display': 'block'},{'display': 'none'},{'display': 'none'},{'display': 'none'},{'display': 'block'},data["entityType"],countriesOptions]  
    elif data["entityType"] == "demand":
        return [{'display': 'none'},{'display': 'block'},{'display': 'none'},{'display': 'none'},{'display': 'block'},data["entityType"],countriesOptions]
    elif data["entityType"] == "solar":
        return [{'display': 'none'},{'display': 'none'},{'display': 'block'},{'display': 'none'},{'display': 'block'},data["entityType"],countriesOptions]
    elif data["entityType"] == "price":
        return [{'display': 'none'},{'display': 'none'},{'display': 'none'},{'display': 'block'},{'display': 'none'},data["entityType"],countriesOptions]
    else:
        raise PreventUpdate()
