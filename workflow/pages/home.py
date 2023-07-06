#Copyright (c) Microsoft. All rights reserved.
import dash
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from dash import dcc ,html, ctx
import pandas as pd
from dash.exceptions import PreventUpdate
import re
import logging
# Import master app object
from workflow.main import app

### Import utilities ###
from utilities.dboperations import dboperations

### Import static ##
from workflow.common.config import GET_EXPERIMENT_SET_SP, SAVE_NEW_EXPERIMENT_SET_SP, ErrorAnalysisReport

from workflow.common.common import dropdownTags, getLoadingElement, detect_special_characer, getModalPopup

import os

print(os.getenv('ErrorAnalysisReportURL'))
logging.info(os.getenv('ErrorAnalysisReportURL'))

ErrorAnalysisReportURL = ErrorAnalysisReport

logging.info(ErrorAnalysisReportURL)

# Layout for Existing section
existingExperimentSetLayout = [html.Div([
            dbc.Row([
                dbc.Col(html.Label('Experiment Set '), width=3),
                dbc.Col( dcc.Dropdown(id = 'experimentDropDown'), width=4)
            ]),
            dbc.Row([
                dbc.Col(html.A(html.Button(id = 'upd_fct_btn' ,children = "Update Forecast Setup" , n_clicks = 0 ,disabled=True), href="/sitesetup"), width=3),
                # dbc.Col(html.A(html.Button(id = 'run_btn',children = "Run Tracking", n_clicks = 0,disabled=True), href="/runtracking"), width=3),
                dbc.Col(html.A(html.Button(id = 'err_btn',children = "Error Analysis", n_clicks = 0,disabled=True), href=ErrorAnalysisReportURL), width=3),
                dbc.Col(html.A(html.Button(id = 'prov_btn',children = "Experiment Provenance", n_clicks = 0,disabled=True), href="/provenance"), width=3),
                dbc.Col(html.A(html.Button(id = 'golive_btn',children = "Go-Live Configuration", n_clicks = 0,disabled=True), href="/goliveconfig"), width=3)
                ])
            ])
]

newExperimentSetLayout = [
    html.Div([
                dbc.Row([
                    dbc.Col(html.Label('Enter Experiment Set Name'), width=3),
                    dbc.Col(
                        dbc.Input(placeholder='Enter Experiment Set Name',
                            id = 'experimentsetname',
                            type = 'text',
                            autoComplete = 'on',
                            minLength = 5,
                            maxLength =15,
                            invalid = False,
                            debounce=True
                        ), width=4) ,
                    getLoadingElement("newExpLoading"),
                    ]),
                dbc.Row([dbc.Col(
                    html.Button(id = 'fct_btn' , children = "Create Forecast Setup" , n_clicks = 0,disabled=True)
                    , width=3)]),
                getModalPopup("homePageModal","Alert","")
            ],
            id = "newExperimentSetParentDiv"
    )
]

homepageLayout = dbc.Container([
    html.Div(
        children=[
            dbc.Row([
                dbc.Col(html.H1("Power and Utilities Forecasting Framework"), className="mb-2")
            ] ),
            dbc.Row([
                dropdownTags('Entity Type','entityTypeDropdown',3,False,False,[{'value': 'wind', 'label': 'wind'},
                                {'value': 'solar', 'label': 'solar'} ,
                                {'value': 'price', 'label': 'price'} ,
                                {'value': 'demand', 'label': 'demand'} ])
            ]),
            dbc.Row([
                dropdownTags('Experiment Type','experimentType',3,False,False,[ {'label':'New' ,  'value' : 'new'} , {'label':'Existing' ,  'value' : 'existing'} ])
            ]),
            getLoadingElement("expSetLoading"),
            dbc.Row([
                html.Div(existingExperimentSetLayout,id = 'existingExperimentSetForm',style={'display':'none'}),
                html.Div(newExperimentSetLayout,id = 'newExperimentSetForm',style={'display':'none'})
            ],justify = 'center' ),
        ]
    ),
    html.Div(id="hidden_div_for_redirect_callback"),
    # Add style sheet
    html.Link(
        rel='stylesheet',
        href='/static/homestylesheet.css?v=7'
    )
],fluid = True)

#=======================================Form validation and action callbacks==========================================
@app.callback(
    Output('existingExperimentSetForm', 'style'),Output('newExperimentSetForm', 'style'),Output('expSetLoadingOutput', 'children'),
    Input('experimentType', 'value'),State('entityTypeDropdown','value'), prevent_initial_call=False
    )
def updateLayout(value,entityType):
    if value == 'new' :
        return {'display':'none'},{'display':'block'},""
    elif value == 'existing' :
        return {'display':'block'},{'display':'none'},""
    else:
        raise PreventUpdate()

@app.callback(
    [Output('fct_btn','disabled'),Output('experimentsetname','invalid')], #
    [Input('experimentsetname','value')]
)
def validateExperimentSetName(value):
    if(len(value)>=4 & len(value)<=50):
        return (False,False)
    else:
        return (True,True)

#=============================================New Experiments==============================================

# Callback for Save experiment button
@app.callback(
    [Output('hidden_div_for_redirect_callback', 'children'),
     Output("newExperiment","data"),
     Output("homePageModalBody","children"),
     Output("homePageModal","is_open"),
     Output("newExpLoadingOutput","children"),
     
     Output('upd_fct_btn','disabled'),
     Output('err_btn','disabled'),
     Output('prov_btn','disabled'),
     Output('golive_btn', 'disabled'),
     Output("existingExperiment","data")
    ],
    [Input('fct_btn', 'n_clicks'),Input("homePageModalClose", "n_clicks"),Input('experimentDropDown','value')],
    [State('experimentsetname','value'), State('entityTypeDropdown', 'value'), State('experimentDropDown','options')], prevent_initial_call=True
    )
def saveExperimentSet(n_clicks,closeClicks,experimentdropdown,value, entityType,experimentoptions):
    if closeClicks > 0 and ctx.triggered_id == "homePageModalClose":
        return [dcc.Location(pathname="/", id="someid_doesnt_matter"),None,"",False,"",dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update]
    if (n_clicks !=0) and ctx.triggered_id == "fct_btn" :

        # Skip validation if it is the first experiment set being created
        try:
            experimentSetList = expSetDF["ExperimentSetName"].tolist()
            
            if (value in experimentSetList):
                # print("Experiment already exists, cannot create a new experiment")
                validMesage =  "Experiment Setup Name already exists"#html.Label("Experiment Setup Name already exists",style = {'font-size': '18px' , 'color': 'red'})
                data=None
                return [dcc.Location(pathname="/", id="someid_doesnt_matter"),data,validMesage,True,"",dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update]
        except NameError:
            pass
        
        if bool(re.search(r"\s", value)):
            validMesage =  "Spaces are not allowed in the Experiment Setup Name"
            data=None
            return [dcc.Location(pathname="/", id="someid_doesnt_matter"),data,validMesage,True,"",dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update]

        if len(value) < 5  :
            validMesage =  "Minumum Length of the Experiment Setup Name is 5"#html.Label("Minumum Length of the Experiment Setup Name is 5",style = {'font-size': '20px' , 'color': 'red'})
            data=None
            return [dcc.Location(pathname="/", id="someid_doesnt_matter"),data,validMesage,True,"",dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update]

        if detect_special_characer(value) :
            validMesage =  "Special Characters Not Allowed in Experiment Setup Name"#html.Label("Special Characters Not Allowed in Experiment Setup Name",style = {'font-size': '20px' , 'color': 'red'})
            data=None
            return [dcc.Location(pathname="/", id="someid_doesnt_matter"),data,validMesage,True,"",dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update]

        else :
            try:
                print("Saving new Experiment set")
                experimentsetid = dboperations.executeStoredProcedure(SAVE_NEW_EXPERIMENT_SET_SP,"@ExperimentSet=?,@EntityType=?",(value,entityType),"dbo",1)
                experimentsetid = int(experimentsetid[0])
                if experimentsetid == -1:
                    validMesage = "Experiment Setup Name already exists, load existing experiment"
                    data = None
                    return [dcc.Location(pathname="/", id="someid_doesnt_matter"),data,validMesage,True,"",dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update]
                else:
                    print(experimentsetid)
                    newExperimentInserted = True
                    data={
                        "experimentsetid" :experimentsetid,
                        "experimenttype": "new",
                        "experimentsetname" :value,
                        "entityType" : entityType
                    }
                    validMesage =''
                    return [dcc.Location(pathname="/sitesetup", id="someid_doesnt_matter"),data,validMesage,False,"",dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update]
            except Exception as ex:
                print(ex)
                print("Experiment creation failed")
                raise PreventUpdate()
    
    elif  experimentdropdown and ctx.triggered_id == 'experimentDropDown' :
        validMesage = ''
        experimentSetName = [x['label'] for x in experimentoptions if x['value'] == experimentdropdown]
        experimentSetName = experimentSetName[0]
        data={
                "experimentsetid" :int(experimentdropdown),
                "experimentsetname" :experimentSetName,
                "experimenttype": "existing",
                "entityType" : entityType
            }
        print(data)
        return  [dcc.Location(pathname="/", id="someid_doesnt_matter"),None,validMesage,False,dash.no_update,False,False,False,False,data]


    else:
        raise PreventUpdate()

#=============================================Existing Experiments==================================================
# Code to get experiment list
def getExperimentSetList(entityType):
    options = []
    print("Invoked")
    expSetDF = dboperations.executeStoredProcedure(GET_EXPERIMENT_SET_SP,"@EntityType=?",(entityType),"dbo",2)
    for i, row in expSetDF.iterrows():
        options.append({'label' : row["ExperimentSetName"] ,'value' :row["ExperimentSetID"]})
    return options

@app.callback(Output('experimentDropDown','options'),
            Input('experimentType', 'value'),State('entityTypeDropdown', 'value'))
def updateOptions(exp,entityType):
    if exp == "existing":
        return getExperimentSetList(entityType)
    else:
        return []
