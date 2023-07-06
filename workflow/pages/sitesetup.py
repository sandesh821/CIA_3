#Copyright (c) Microsoft. All rights reserved.
### Import Packages ###
import dash
import dash_daq
from dash import dcc ,html, ctx
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from workflow.common import common
from workflow.common import getdata
import sys


from workflow.common.PrepopulateTransformations import *
from workflow.pages import forecastsetup,sourcedata,transformations,mergefiles,featureengineering,abalation,multivariateEDA
from workflow.pages import siteinformation
### Import Dash Instance ###
from workflow.main import app
import dash_bootstrap_components as dbc

layout = html.Div([  
        html.Link(
            rel='stylesheet',
            href='/static/sitesetupstylesheet.css?v=4'
        ),     
        dbc.Row([
            dbc.Col([
                html.H1('Power and Utilities Forecasting Framework')
            ] ,width = 12) ]),

        dbc.Row([

            dbc.Col([
                dcc.Tabs(id="siteSetupNavigation", value='tab-1', 
                children=[
                    dcc.Tab(label='Site Information',id='tab-1' ,value='tab-1'),
                    dcc.Tab(label='Forecast Setup', id='tab-2', value='tab-2',disabled = True),
                    dcc.Tab(label='Source Data',id='tab-3' ,value='tab-3',disabled = True),
                    dcc.Tab(label='Transformations', id='tab-4',value='tab-4',disabled = True),
                    dcc.Tab(label='MergeFiles', id='tab-5',value='tab-5',disabled = True),
                    dcc.Tab(label='FeatureEngineering', id='tab-6',value='tab-6',disabled = True),
                    dcc.Tab(label='MultivariateEDA', id='tab-7',value='tab-7',disabled = True),
                    dcc.Tab(label='Abalation', id='tab-8',value='tab-8',disabled = True)
                ]   
                )
                ], width=11, class_name="tabCol"),
            dbc.Col([
                html.Button(id = "nextTab" , children = 'next' ,n_clicks = 0)
                ], width=1, class_name="nextTabCol")
            ]),
        common.getLoadingElement("tabLoading"),
        html.Div(id='tabs-content-inline'),
        html.Div(list("ABC"), id="data", style={"display":"none"})
])

@app.callback(Output('siteSetupNavigation', 'value'), 
              [Input('nextTab','n_clicks')],
              State('siteSetupNavigation', 'value')
              ,State("tab-2","disabled")
              ,State("tab-3","disabled")
              ,State("tab-4","disabled")
              ,State("tab-5","disabled")
              ,State("tab-6","disabled")
              ,State("tab-7","disabled")
              ,State("tab-8","disabled")
              )
def navigateToNextPage(clicks,currentTab,tab2,tab3,tab4,tab5,tab6,tab7,tab8):
    selectedTabNum = int(currentTab[-1])
    if clicks > 0:
        if (selectedTabNum == 1 and not tab2) or (selectedTabNum == 2 and not tab3) or (selectedTabNum == 3 and not tab4) or (selectedTabNum == 4 and not tab5)  or (selectedTabNum == 5 and not tab6) or (selectedTabNum == 6 and not tab7)  or (selectedTabNum == 7 and not tab8):
            selectedTabNum = selectedTabNum + 1
            return 'tab-'+ str(selectedTabNum)
        else:
            raise PreventUpdate()
    else:
            raise PreventUpdate()

@app.callback([Output('tabs-content-inline', 'children'),
               Output('experimentStore','data'),
               Output("data","children"),
               Output("tabLoadingOutput","children")],
              Input('siteSetupNavigation', 'value'), 
              [State("newExperiment","data"),State("existingExperiment","data"),State('experimentStore','data')],
              prevent_initial_call=False)
def render_content(tab,data1,data2,data):
    print("Loading tab ", tab)
    
    if tab == 'tab-1':
        # Load experiment set id from session and save it in master store
        if data1 is not None:
            data = data1
        elif data2 is not None:
            data = data2
        print("Loading site details for tab 1")
        selectedLayout = siteinformation.layout

        df = getdata.getExperimentDetails(data)
        if (data["experimenttype"] == "existing" and df is not None and len(df) > 0):
            data["experimentSetDetails"] = df
            
    elif tab == 'tab-2':
        if data["experimenttype"] == "new":
            data["experimenttype"] = "existing"

        df = getdata.getForecastSetupDetails(data)
        if (data["experimenttype"] == "existing" and df is not None and len(df) > 0):
            print("Loading forecast details")
            data["forecastSetupDetails"] = df.to_dict("records")
        selectedLayout = forecastsetup.layout

    elif tab == 'tab-3':
        df = getdata.getSourceDataDetails(data)
        if (data["experimenttype"] == "existing" and df is not None and len(df) > 0):
            print("Loading source data details")
            data["sourceDataDetails"] = df.to_dict("records")
        selectedLayout = sourcedata.layout
        
    elif tab == 'tab-4':
        transformData = getdata.getTransformationDetails(data)
        columnTransformData = getdata.getColumnTransformationDetails(data)
        timezoneData = getdata.getTimezoneDetails(data)
        if (data["experimenttype"] == "existing" and transformData is not None and len(transformData) > 0):
            print("Loading transformation data details")
            data["transformationDataDetails"] = transformData
        if (data["experimenttype"] == "existing" and columnTransformData is not None and len(columnTransformData) > 0):
            print("Loading column level transformation data lists")
            data["columnTransformationDataDetails"] = columnTransformData
        if (data["experimenttype"] == "existing" and timezoneData is not None and len(timezoneData) > 0):
            print("Loading timezone data details")
            data["timezoneDataDetails"] = timezoneData
        selectedLayout = transformations.layout
    
    elif tab == 'tab-5':
        selectedLayout = mergefiles.layout

    elif tab == 'tab-6':
        newColumnData = getdata.getNewColumnInfo(data)
        interpolationData = getdata.getInterpolationInfo(data)
        if (data["experimenttype"] == "existing" and newColumnData is not None and len(newColumnData) > 0):
            print("Loading new column data details")
            data["newColumnInfo"] = newColumnData
        if (data["experimenttype"] == "existing" and interpolationData is not None and len(interpolationData) > 0):
            print("Loading column level interpolation details")
            data["interpolationInfo"] = interpolationData
        selectedLayout = featureengineering.layout

    elif tab == 'tab-7':
        multivariateDF = getdata.getMultiVariateEDASelections(data)
        if (data["experimenttype"] == "existing" and multivariateDF is not None and len(multivariateDF) > 0):
            print("Loading new column data details")
            data["multivariateSelections"] = multivariateDF
        selectedLayout = multivariateEDA.layout

    elif tab == 'tab-8':
        print("Tab 8 selected")
        expdf = getdata.getSavedExperiments(data)
        if (data["experimenttype"] == "existing" and expdf is not None and len(expdf) > 0):
            print("Loading experiment details")
            data["savedExperiments"] = expdf
        selectedLayout = abalation.layout       

    return [selectedLayout,data,tab,""]