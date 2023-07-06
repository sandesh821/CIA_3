#Copyright (c) Microsoft. All rights reserved.
from dash import html , dcc, ctx
from dash.dependencies import Input, Output ,State
import dash_bootstrap_components as dbc
import pandas as pd
from dash import dash_table
from datetime import timedelta, datetime
from dash.exceptions import PreventUpdate

# Import master app object
from workflow.main import app

### Import utilities ###
from utilities.dboperations import dboperations
import re
from workflow.common.getdata import getExperimentDetails 
from workflow.common.common import getLoadingElement, listToOptions, getModalPopup
import timezonefinder, pytz
import base64

from workflow.common.config import *


dash_tbl_col_list = ["InitialWindowSteps","InitialWindowStepsUnits" ,"ForecastHorizon" ,"Granularity" ,"GranularityUnits","ForecastTime","Lookback","TimeZone"]
dash_tbl_col_options = []
for i in dash_tbl_col_list:
    dash_tbl_col_options.append({'name': i,'id': i,'deletable': True,'renamable': True } )

timezoneTypeList = ['Timezone','Local']
timezoneTypeOptions = listToOptions(timezoneTypeList) 

# Get timezones
def loadTimeZoneOptions():
    timezoneDF = dboperations.executeStoredProcedure(GET_TIMEZONES_SP,None,None,"dbo",2)
    col_list =  timezoneDF['TimeZone'].unique()
    options = []
    for i in col_list:
        options.append({'label' : i ,'value' :i})
    return options

granularityOptions = [{'label' : 'Hour', 'value' : 'H'} , {'label' : 'Minute', 'value' : 'min'} ,{'label' : 'Seconds', 'value' : 'S'} ]

layout = dbc.Container(
                [html.Div([
                    dbc.Row([  
                        dbc.Col([
                            dbc.Row([  
                                    dbc.Col([
                                            html.Label('Granularity'),
                                            dcc.Input( id = 'Granularity',type = 'number',placeholder = 'Enter a Numeric Value', persistence=True,persistence_type='session'),
                                            dcc.Dropdown(id = 'GranularityUnits' ,options = granularityOptions)       
                                        ],width = 4),
                                    dbc.Col([
                                        html.Label('Initial Window Steps'),
                                        dcc.Input( id = 'InitialWindowSteps',type = 'number',placeholder = 'Enter a Numeric Value',persistence=True,persistence_type='session'),
                                        dcc.Dropdown(id = 'InitialWindowStepsUnits' ,options = granularityOptions),
                                    ],width = 4),
                                    dbc.Col([
                                        html.Label('Forecast Horizon'),
                                        dcc.Input( id = 'ForecastHorizon',type = 'number',placeholder = 'Enter a Numeric Value',persistence=True,persistence_type='session'),
                                    ],width = 4)
                                   ]),
                                   dbc.Row([  
                                    dbc.Col([
                                        html.Label('TimeZone Type'),
                                        dcc.Dropdown(id = 'TimeZoneType' ,options = timezoneTypeOptions)
                                    ],width = 4) ,
                                    dbc.Col([
                                        html.Label('TimeZone'),
                                        dcc.Dropdown(id = 'TimeZone'  ,persistence=True,persistence_type='session')
                                    ],width = 4) ,
                                    dbc.Col([
                                            html.Label('Forecast Time'),
                                            dcc.Input( id = 'ForecastTime',type = 'text',placeholder = 'Enter in %H:%M:%S format')
                                    ],width = 4)
                                ]),
                                dbc.Row([
                                    dbc.Col([
                                            html.Label('Lookback'),
                                            dcc.Input( id = 'Lookback',type = 'text',placeholder = 'Enter lookback period')
                                    ],width = 4),
                                    dbc.Col(width=6),
                                    dbc.Col([
                                        html.Button("Add",id = 'addRowButton',n_clicks = 0 )
                                    ],width = 2)
                                ]),
                            ], width=8),
                            dbc.Col([
                                    html.Div([
                                        html.Img(src=app.get_asset_url('/forecast.png') , style = {'width' : "100%" ,'height' : 200})
                                    ])
                            ], width=4)
                        ]),
                        getLoadingElement("timezoneLoading"),
                        
                        dbc.Row([
                                dbc.Col([
                                    dash_table.DataTable(id='adding-rows-table',columns=dash_tbl_col_options,row_deletable=True,persistence = True,persisted_props = ['data'],persistence_type = 'session',
                                                        # Styling alternate rows
                                                        style_data_conditional=[{
                                                                                'if': {'row_index': 'odd'},
                                                                                'backgroundColor': 'rgb(220, 220, 220)',
                                                                                }])
                                ]) 
                            ]),
                        getLoadingElement("forecastTableLoading"),
                        getLoadingElement("saveDataLoading"),
                        dbc.Row([
                                dbc.Col ([ 
                                    html.Div(id = 'forecasttable')
                                ] ,width = 6) ,
                                dbc.Col ([ 
                                    html.Div(id = "hidden_div")
                                ] ,width = 4) ,
                                dbc.Col ([ 
                                    html.Button(id = "saveForecastSetup" , children = 'save' ,n_clicks = 0, disabled=True)
                                ] ,width = 2) 
                            ]),
                        getModalPopup("fcstsetupModal","Alert",""),
                        getModalPopup("fcstSavePageModal","Alert","")

                    ])
            ], id="forecastSetupContainer")


@app.callback(Output('TimeZone','options'),Output("timezoneLoadingOutput","children"),
              Input('TimeZoneType', 'value'),
              State('experimentStore','data'))
def getTimeZone(TimeZoneType,data):
    if TimeZoneType is not None : 
        if TimeZoneType == 'Timezone':
            options  = loadTimeZoneOptions()
        elif TimeZoneType == 'Local':
            getInfo = getExperimentDetails(data)
            tf = timezonefinder.TimezoneFinder()
            timezone_str = tf.certain_timezone_at(lat=float(getInfo['Lat']), lng= float(getInfo['Long']))
            options = listToOptions([timezone_str])
        elif TimeZoneType == 'Standard':
            timezoneDF = dboperations.executeStoredProcedure(GET_TIMEZONES_SP,None,None,"dbo",2)
            col_list =  timezoneDF['UTC offset'].unique()
            options = []
            for i in col_list:
                options.append({'label' : i ,'value' :i})
        return options, ""
    else : 
        raise PreventUpdate()

# Callback for Add row button
@app.callback(
    [Output('adding-rows-table', 'data'), Output("fcstsetupModalBody","children"),Output("fcstsetupModal","is_open")],
     [Input('addRowButton', 'n_clicks')
    ,Input('data', 'children')
    ,Input("fcstsetupModalClose", "n_clicks")
     ],
    [State('adding-rows-table', 'data'),
    State('InitialWindowSteps', 'value'),
    State('InitialWindowStepsUnits', 'value'),
    State('ForecastHorizon', 'value'),
    State('Granularity', 'value'),
    State('GranularityUnits', 'value'),
    State('ForecastTime', 'value'),
    State('Lookback','value'),
    State('TimeZone', 'value')],
    State('experimentStore','data')
   )
def add_row(n_clicks,inp1,closeClicks,rows, InitialWindowSteps,InitialWindowStepsUnits,ForecastHorizon,Granularity,GranularityUnits,ForecastTime,Lookback,TimeZone,storeData):
    validMesage = ''
    if rows is None : 
        rows = []
    if closeClicks > 0 and ctx.triggered_id == "fcstsetupModalClose":
        return [rows,validMesage, False]
    if n_clicks > 0 :
        if len(rows) == 1:
            validMesage = "Only one forecast setup is permitted, to update delete existing and add new record"
            return [rows,validMesage, True]
        else:
            validationValues = [InitialWindowSteps,InitialWindowStepsUnits,ForecastHorizon,Granularity,GranularityUnits,ForecastTime,Lookback,TimeZone]
            
            for value in validationValues :
                # add more validations
                if value == '' or  value is None :
                    validMesage =  "All Fields Are Mandatory"
                    return [rows,validMesage, True]
            if int(ForecastHorizon) > int(Lookback) :
                validMesage =  "Lookback should not be less than Forecast Horizon"
                return [rows,validMesage, True]
            
            if not (re.search("^((?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d$)", ForecastTime)) :
                validMesage =  "Enter Valid Forecast Time"
                return [rows,validMesage, True]

            rows.append({"InitialWindowSteps": InitialWindowSteps,"InitialWindowStepsUnits": InitialWindowStepsUnits ,"ForecastHorizon": ForecastHorizon ,"ForecastHorizonUnits": '',"Granularity": Granularity ,"GranularityUnits": GranularityUnits,"ForecastTime": ForecastTime,"Lookback":Lookback,"TimeZone": TimeZone  })
            return [rows,validMesage, False]
    elif "forecastSetupDetails" in storeData.keys():
        rows = storeData["forecastSetupDetails"]
        return [rows,validMesage, False]
    else:
        raise PreventUpdate()

# Update state of Save button
@app.callback(Output('saveForecastSetup','disabled'),
              [Input('adding-rows-table', 'data_previous'),Input('adding-rows-table', 'data')],
              [State('adding-rows-table', 'data')])
def rowsRemoved(previous,inputCurrent,current):
    print("Enabling Save invoked")
    if current is None or len(current) == 0:
        return True # Disable save if there are no rows in current view of the table
    else:
        return False


@app.callback(
    [Output('forecasttable','children'), Output("forecastTableLoading","children")],
    [State('adding-rows-table', 'data'),Input("adding-rows-table",'active_cell')])
def f(data,active):
    if data is not None : 
        df = pd.DataFrame(data)
        # Get configuration values below : 
        curr_date_str = '2020-01-01' # This hardcoding is expected
        forecast_times_str = df.iloc[active['row'],:]['ForecastTime']
        deltaduration_config =  df.iloc[active['row'],:]['GranularityUnits'] 
        granulairty =  int(df.iloc[active['row'],:]['Granularity'] )
        initial_timestep = df.iloc[active['row'],:]['InitialWindowStepsUnits']     
        inittimesteps_config = int(df.iloc[active['row'],:]['InitialWindowSteps']    ) 
        forecasthorizon_steps = int(df.iloc[active['row'],:]['ForecastHorizon']   )
        datetime_format_str = "%Y-%m-%d %H:%M:%S"
        forecast_datetime = datetime.strptime("{} {}".format(curr_date_str,forecast_times_str), datetime_format_str)
        deltaduration = {'H' : (60*60) , 'min' :  (60) , 'S' : 1 }
        delta = deltaduration[deltaduration_config]
        granulairty = granulairty
        timestepsdelta = deltaduration[initial_timestep]
        inittimesteps = inittimesteps_config
        forecast_datetimes = []
        # get forecast prediction values
        forecast_datetime = forecast_datetime + timedelta(seconds = inittimesteps * timestepsdelta )
        forecast_datetimes.append(forecast_datetime)
        for i in range(forecasthorizon_steps):
            forecast_datetime = forecast_datetime + timedelta(seconds = granulairty * delta )
            forecast_datetimes.append(forecast_datetime)

        df = pd.DataFrame(forecast_datetimes , columns= ['DateTime'])
        data = df.to_dict('rows')
        columns =  [{"name": i, "id": i,} for i in (df.columns)]
        return [dash_table.DataTable(data=data, columns=columns,persistence = True,persisted_props = ['data'],persistence_type = 'session',
                                    # Styling alternate rows
                                    style_data_conditional=[{
                                                            'if': {'row_index': 'odd'},
                                                            'backgroundColor': 'rgb(220, 220, 220)',
                                                            }]),""]
    else:
        raise PreventUpdate()
        
# Save details to database 
@app.callback([Output('tab-3','disabled'), 
                Output("saveDataLoadingOutput","children"),
                Output("fcstSavePageModalBody","children"),
                Output("fcstSavePageModal","is_open")],

                [Input('saveForecastSetup', 'n_clicks'),
                Input('data', 'children'),
                Input('adding-rows-table', 'data'),
                Input("fcstSavePageModalClose", "n_clicks")],

                [State('adding-rows-table', 'data') ,
                State('experimentStore','data')]
            )
def saveButtonClicked(clicks,inp1,inpDataTable,closeClicks,dataTable,data):
    if closeClicks is not None and closeClicks > 0 and ctx.triggered_id == "fcstSavePageModalClose":
        return [False,"","",False]
    if (clicks > 0):
        try:
            # Delete all records in database
            dboperations.executeStoredProcedure(DELETE_FORECAST_SETUP_DETAILS_SP,"@ExperimentSetID = ? ",(data["experimentsetid"]),"dbo",0)
            identifier = 0
            for row in dataTable:
                # Save forecast details to database
                dboperations.executeStoredProcedure(SAVE_FORECAST_SETUP_DETAILS_SP,"@ExperimentSetID = ? ,@RowID=?, @Granularity =?, @GranularityUnits=?, @InitialWindowSteps=?, @InitialWindowStepsUnits =?, @ForecastHorizon =?, @ForecastHorizonUnits =?, @ForecastTime = ?, @Lookback = ?, @TimeZone = ?",(data["experimentsetid"], identifier, row["Granularity"],row["GranularityUnits"],row["InitialWindowSteps"],row["InitialWindowStepsUnits"],row["ForecastHorizon"],row["ForecastHorizonUnits"],row["ForecastTime"], row["Lookback"], row["TimeZone"]),"dbo",0)
                identifier = identifier + 1
            print("Saved forecast information!")
            return [False,"",DATA_SAVE_MESSAGE,True]
        except Exception as ex:
            print(ex)
            raise PreventUpdate()
    elif "forecastSetupDetails" in data.keys():
        return [False,"","",False]
    elif ctx.triggered_id == "adding-rows-table" and (dataTable is None) and (inpDataTable is None or len(inpDataTable) == 0):
        return [True, "","",False]
    else:
        raise PreventUpdate()