#Copyright (c) Microsoft. All rights reserved.
import dash
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from dash import dcc, html, ctx, ALL
from dash import dash_table as dt
from dash.exceptions import PreventUpdate

import pandas as pd
import json
import requests
import logging
# Import master app object
from workflow.main import app

### Import static ##
from workflow.common.config import  *
from workflow.common import getdata
from workflow.common.common import *
from utilities.azure import blobOperations
from utilities.dboperations import dboperations
from utilities.azure import devops
from utilities import config

tableColumns = ["Experiment","InternalRunId","ModelName","MAE","RMSE","MAPE","MSE"]
tabel_data = pd.DataFrame(columns=tableColumns)


def step(id,filesoptions):
    if id is not None:
        htmlObj = dbc.Row([ 
                    dbc.Col(dcc.Dropdown(placeholder = 'Select File',options=listToOptions(filesoptions), id={"goLiveFile": str(id)}),width=2),
                    dbc.Col(html.Label('Frequency', className=""), width=1),
                    dbc.Col([
                        dcc.Input(
                            id={"goLiveRefreshTime": str(id)},
                            type='number',
                            value=0
                        )
                    ], width=1),
                    dbc.Col([
                        dcc.Dropdown(
                            id={"goLiveRefreshUnit": str(id)},
                            options=frequencyOptions
                        )
                    ], width=1),
                    dbc.Col(html.Label('Granularity', className=""), width=1),
                    dbc.Col([
                        dcc.Input(
                            id={"goLiveGranularityTime": str(id)},
                            type='number',
                            value=0
                        )
                    ], width=1),
                    dbc.Col([
                        dcc.Dropdown(
                            id={"goLiveGranularityUnit": str(id)},
                            options=granularityOptions
                        )
                    ], width=1),
                    dbc.Col([dcc.Checklist(options=[{"label":"Is IoT","value":"Is IoT"}],id={"goLiveIsIoT": str(id)}, inline=True)], width=2),
                    dbc.Col([dcc.Checklist(options=[{"label": "Is Entity", "value": "Is Entity"}],id={"goLiveIsIoTEnitity": str(id)}, inline=True)], width=2)
                ], className="fileConfigRow")

        return htmlObj
    else:
        []

def stepToMap(id,filesoptions):
    if id is not None:
        htmlObj = dbc.Row([ 
                    dbc.Col(dcc.Dropdown(placeholder = 'Select File',options=listToOptions(filesoptions), id={"goLiveFile": str(id)}),width=2),
                    dbc.Col(html.Label('API', className=""), width=1),
                    dbc.Col([
                        dcc.Dropdown(
                            id={"goLiveAPIType": str(id)},
                            options=listToOptions(["Darksky","Solcast","OpenWeather"])
                        )
                    ], width=1)
                ], className="fileConfigRow")

        return htmlObj
    else:
        []

layout = html.Div([
    dbc.Row([
        dbc.Col(html.H1("POWER AND UTILITIES FORECASTING FRAMEWORK"))
    ]),
    html.Div([
        dbc.Row([
            dbc.Col(html.B('Model Selection **Required**'))
        ],className="sectionHeader"),
        dbc.Row([
            dbc.Col([
                html.Label('Best Models', title="Select the primary model for deployment"),
                dt.DataTable([], [{"name": i, "id": i} for i in tableColumns],
                            id="bestModelsTable",
                            style_table={'height': 150},
                            style_cell={'textAlign': 'right'})
            ], align="center")
        ]),
        dbc.Row([
            dbc.Col([
                html.Label('Alternate Models (Optional)', title="Select the alternate model for deployment in case of model drift"),
                dt.DataTable([], [{"name": i, "id": i} for i in tableColumns],
                            id="alternateModelsTable",
                            style_table={'height': 150},
                            style_cell={'textAlign': 'right'})
            ], align="center")
        ]),
        dbc.Row([
            dbc.Col([],width=11),
            dbc.Col(html.Button('Save',
                                id='saveModelSelectionBtn',
                                disabled=True,
                                className='btnCls')
                    ,width=1)
        ])
    ]),
    getModalPopup("loadExperimentModal","Alert",""),
    getLoadingElement("loadExperimentsLoading"),
    getModalPopup("saveExperimentSelectionModal","Alert",""),
    getLoadingElement("saveExperimentSelectionLoading"),
    html.Div([
        dbc.Row([
            dbc.Col(html.B('Data Ingestion Configurations **Required**'))
        ],className="sectionHeader"),
        dbc.Row([
            dbc.Col(html.Label('Storage Account to pull streaming data'), width=3),
            dbc.Col([
                dcc.Dropdown(
                    id='goliveStorageAccount',
                    options=[]
                )
            ], width=2),
            dbc.Col(html.Label('Container name'), width=2),
            dbc.Col([
                dcc.Dropdown(
                    id='goliveContainer',
                    options=[]
                )
            ], width=2)
        ]),
        getLoadingElement("loadgoliveContainersLoading"),
        getModalPopup("saveDataIngestionModal","Alert",""),
        getLoadingElement("saveDataIngestionLoading"),
        dbc.Row([
            dbc.Col(html.Label('Configure file refresh frequency', className="refreshCycleLabel"), width=4)
        ]),
        dbc.Row([], id = "fileConfigSection"),
        dbc.Row([
            dbc.Col([],width=11),
            dbc.Col(html.Button('Save',
                                id='saveDataIngestionBtn',
                                disabled=True,
                                className='btnCls')
                    ,width=1)
        ])
    ]),
    html.Div([
        dbc.Row([
            dbc.Col(html.B('Events Configurations'))
        ],className="sectionHeader"),
        dbc.Row([
            dbc.Col(html.Label('Model retraining frequency', className="refreshCycleLabel"), width=2),
            dbc.Col([
                dcc.Input(
                    id='modelRetrainTime',
                    type='number',
                    placeholder="Enter duration in number"
                )
            ], width=2),
            dbc.Col([
                dcc.Dropdown(
                    id='modelRetrainUnit',
                    options=retrainFrequencyOptions
                )
            ], width=2),
            dbc.Col([dcc.Checklist(options=[{"label":"Use Historical data","value":"historyEnabled"}],id="historyEnabled", inline=True)], width=2),
            dbc.Col([],width=4)
        ], className="fileConfigRow"),
        dbc.Row([
            dbc.Col(html.B(html.Label('Data Drift configurations', className="refreshCycleLabel")), width=2)
        ]),
        dbc.Row([
            dbc.Col(html.Label('Drift share threshold', className="cat_col_threshold"), width=2),
            dbc.Col([
                dcc.Input(
                    id='catColThreshold',
                    type='number',
                    placeholder="Enter threshold in numerics"
                )
            ], width=2),
            dbc.Col(html.Label('Numerical column drift threshold', className="num_col_threshold"), width=2),
            dbc.Col([
                dcc.Input(
                    id='numColThreshold',
                    type='number',
                    placeholder="Enter threshold in numerics"
                )
            ], width=2),
            dbc.Col([],width=4)
        ], className="fileConfigRow"),
        getLoadingElement("loadEventConfigLoading"),
        getModalPopup("saveEventConfigModal","Alert",""),
        getLoadingElement("saveEventConfigLoading"),
        dbc.Row([
            dbc.Col([],width=11),
            dbc.Col(html.Button('Save',
                                id='saveEventSetupBtn',
                                disabled=True,
                                className='btnCls')
                    ,width=1)
        ])
    ]),
    html.Div([
        dbc.Row([
            dbc.Col(html.B('Parameters for model deployment **Required**'))
        ],className="sectionHeader"),
        dbc.Row([
            dbc.Col(html.Label('Accelerator Type'), width=2),
            dbc.Col([
                dcc.Dropdown(
                    id='acceleratortype',
                    options=[{"label":"CPU", "value":"CPU"}]
                )
            ], width=2),
            dbc.Col(html.Label('Cost'), width=2),
            dbc.Col([
                dcc.Dropdown(
                    id='cost',
                    options=[{"label":"Medium", "value":"medium"},{"label":"High", "value":"high"}]
                )
            ], width=2),
            dbc.Col(html.Label('Hosting model'), width=2),
            dbc.Col([
                dcc.Dropdown(
                    id='hostingmodel',
                    options=[{"label":"Custom", "value":"custom"}]
                )
            ], width=2)
        ], className="fileConfigRow"),
        dbc.Row([
            dbc.Col(html.Label('Version dependency'), width=2),
            dbc.Col([
                dcc.Dropdown(
                    id='versiondependency',
                    options=[{"label":"Medium", "value":"medium"}]
                )
            ], width=2),
            dbc.Col(html.Label('Platform preference'), width=2),
            dbc.Col([
                dcc.Dropdown(
                    id='platformpreference',
                    options=[{"label":"AKS", "value":"AKS"},{"label":"Azure Function", "value":"AF"}]
                )
            ], width=2),
            dbc.Col(html.Label('Model Type'), width=2),
            dbc.Col([
                dcc.Dropdown(
                    id='modelType',
                    options=[{"label":"Multi step", "value":"multi"}]
                )
            ], width=2),
        ]),
        getLoadingElement("loadDeploymentLoading"),
        getModalPopup("saveDeploymentModal","Alert",""),
        getLoadingElement("saveDeploymentLoading"),
        dbc.Row([
            dbc.Col([],width=11),
            dbc.Col(html.Button('Save',
                                id='saveDeploymentSetupBtn',
                                disabled=True,
                                className='btnCls')
                    ,width=1)
        ])
    ]),
    html.Div([
        dbc.Row([
            dbc.Col(html.B('Notification configurations **Required**'))
        ],className="sectionHeader"),
        dbc.Row([
            dbc.Col(html.Label('SMTP Server'), width=2),
            dbc.Col([
                dcc.Input(
                    id='smtpServer',
                    placeholder="Enter SMTP server (default smtp-mail.outlook.com)"
                )
            ], width=2),
            dbc.Col(html.Label('SMTP Port'), width=2),
            dbc.Col([
                dcc.Input(
                    id='smtpPort',
                    placeholder="Enter SMTP port (default 587)"
                )
            ], width=2),
            dbc.Col(html.Label('List of receivers'), width=2),
            dbc.Col([
                dcc.Input(
                    id='receiversList',
                    placeholder="Format - email1,email2,email3"
                )
            ], width=2),
        ], className="fileConfigRow"),
        getModalPopup("saveNotificationModal","Alert",""),
        getLoadingElement("saveNotificationLoading"),
        dbc.Row([
            dbc.Col([],width=11),
            dbc.Col(html.Button('Save',
                                id='saveNotificationBtn',
                                disabled=True,
                                className='btnCls')
                    ,width=1)
        ])
    ]),
    html.Div([
            html.Div([
                    html.Label("Follow steps for model deployment: "),
                    html.Ol([
                        html.Li("Add keys in key vault for api manager, notification tool, etc (Details are present in deployment document)"), 
                        html.Li("Update API Manager if needed to add custom code for existing API or add new API and check in the code in selected branch"),   
                        html.Li("Update SP in database for prediction schedule"),
                        html.Li("Run go live infra setup pipeline"),  
                        html.Li("Validate newly added configurations are available in web app (AKSSERVICE, GOLIVESTORAGEACCOUNTNAME, GOLIVEFUNCTIONAPP, FUNCTIONAPPNAME, KEYVAULT, ACR)"),  
                        html.Li("Update configurations in utilities folder of code in the mapped repository"),  
                        html.Li("Execute triggerDeployment.sh script to deploy components for go live flow") 
                    ])
                ]),
            html.Div([],id="goliveDetails"),
            html.Div(["Note: Use type as 'best' for best model deployment and 'alternate' for alternate model deployment, make fileUpload as false for alternate deployment"])
    ]),
    # html.Div([
    # getLoadingElement("setupLoading"),
    # getLoadingElement("deployLoading"),
    # dbc.Row([
    #         dbc.Col([],width=8),
    #         dbc.Col(html.Button('Setup golive flow',
    #                             id='goliveFunctionAppBtn',
    #                             # disabled=True,
    #                             className='btnCls')
    #                 ,width=2),
    #         dbc.Col(html.Button('Deploy Model',
    #                             id='deployModelBtn',
    #                             disabled=True,
    #                             className='btnCls')
    #                 ,width=2)
    #     ])
    # ]),
    html.Link(
        rel='stylesheet',
        href='/static/golivestylesheet.css?v=7'
    )
], id="goLiveConfigPage")

# On page load
@app.callback([Output("bestModelsTable", "data"), 
               Output("alternateModelsTable", "data"),
               Output('loadExperimentsLoadingOutput',"children"),
               Output("loadExperimentModalBody","children"),
               Output("loadExperimentModal","is_open"),
               Output("fileConfigSection","children"),
               Output("goliveStorageAccount","options")],
              [Input('page-content','children'),Input("loadExperimentModalClose", "n_clicks")],
              [State("existingExperiment","data")],prevent_initial_call=False
)
def onPageLoad(inpt1, closeClicks, data):
    if closeClicks > 0 and ctx.triggered_id == "loadExperimentModalClose":
        return [dash.no_update,dash.no_update,"","",False,dash.no_update,dash.no_update]
    if data is not None:
        print("Loading experiment data")
        topModelsData = getdata.getDFToDictData(GET_TOP_MODELS_SP,data)
        
        if len(topModelsData) > 0:
            # Read source data files
            sourceFileDetails = getdata.getSourceDataDetails(data)
            filesOptions = sourceFileDetails["FileIdentifier"].values
            #step
            rowList = []
            for i in range(2):
                rowList.append(step(i,filesOptions))

            #step
            i = 2
            while i < len(filesOptions):
                rowList.append(stepToMap(i,filesOptions))
                i= i+1

            # Get storage account list
            storageAccounts = listToOptions(blobOperations.getStorageAccountList())

            # Bind data to drop downs
            return [topModelsData, topModelsData,"","",False,rowList,storageAccounts]
        else:
            return [dash.no_update,dash.no_update,"","No experiments completed!",True,dash.no_update,dash.no_update]
    else:
        raise PreventUpdate()

# On model selection
@app.callback(Output("saveModelSelectionBtn", 'disabled'),
              [Input('bestModelsTable', 'active_cell'), Input('alternateModelsTable', 'active_cell')],
)
def onModelSelection(best_cell, alternate_cell):
    print("Triggered on model selection")
    save_btn_disabled = True
    if best_cell is not None:
        print("State updated")
        save_btn_disabled = False

    return save_btn_disabled

# On save button event
@app.callback([Output('saveExperimentSelectionLoadingOutput',"children"),
               Output("saveExperimentSelectionModalBody","children"),
               Output("saveExperimentSelectionModal","is_open"),
               Output("goliveDetails","children")],
              [Input('saveModelSelectionBtn', 'n_clicks'),Input("saveExperimentSelectionModalClose", "n_clicks")],
              [State('bestModelsTable', 'active_cell'), State('alternateModelsTable', 'active_cell'),State('bestModelsTable', 'data'),State("existingExperiment","data")]
)
def saveModelSelection(clicks,closeClicks,best_cell,alternate_cell,bestModelData,data):
    if closeClicks > 0 and ctx.triggered_id == "saveExperimentSelectionModalClose":
        return "","",False,dash.no_update
    if clicks:
        try:
            # Get selected rows from both tables
            best_row_data = bestModelData[best_cell["row"]]
            # Setting alternate model deployment is optional
            if alternate_cell is not None:
                alternate_row_data = bestModelData[alternate_cell["row"]]
            else:
                alternate_row_data = None
            # Create a dictionary with the selected row data
            selected_rows = {
                "best_model": best_row_data,
                "alternate_model": alternate_row_data
            }
            
            # Delete all records in database
            dboperations.executeStoredProcedure(DELETE_MODEL_SELECTION_SP,"@ExperimentSetID = ?",(data["experimentsetid"]),"golive",0)
            # Execute stored procedure to save selected rows to database
            dboperations.executeStoredProcedure(SAVE_MODEL_SELECTION_SP,"@ExperimentSetID = ?,@ModelDetails=?",(data["experimentsetid"],json.dumps(selected_rows)),"golive",0)
        
            experimentsetid = data["experimentsetid"]
            experimentsetname =  data["experimentsetname"]

            return  ["", "Selection saved successfully!", True, "Command for go live deployment: " + f"bash triggerDeployment.sh -i {experimentsetid} -n '{experimentsetname}' -f 'False' -t 'best'"]
            
        except Exception as e:
            print("Error:", e)
            return ["", "Save operation failed", True, dash.no_update]
    else:
        raise PreventUpdate()

@app.callback(
    Output('goliveContainer','options') ,
    Output("loadgoliveContainersLoadingOutput","children"),
    Input('goliveStorageAccount','value'))
def containerDropdown(account_name):
    if account_name is not None:
        opts = listToOptions(blobOperations.getContainerList(account_name))
        return opts , ""
    else:
        raise PreventUpdate()

# Enable save button event
@app.callback(Output('saveDataIngestionBtn',"disabled"),
              Input("goliveStorageAccount","value"),
              Input("goliveContainer","value"),
              [Input({"goLiveFile": ALL}, "value")],
              [Input({"goLiveRefreshTime": ALL}, "value")],
              [Input({"goLiveRefreshUnit": ALL}, "value")],
              [Input({"goLiveGranularityTime": ALL}, "value")],
              [Input({"goLiveGranularityUnit": ALL}, "value")],
              [Input({"goLiveIsIoT": ALL}, "value")],
              [Input({"goLiveIsIoTEnitity": ALL}, "value")]
)
def saveDataIngestion(*args):
    if args[0] is not None and args[1] is not None and args[2][0] is not None and args[3][0] is not None and args[4][0] is not None and args[5][0] is not None and args[6][0] is not None:
        return False
    else:
        raise PreventUpdate()

# On save button event
@app.callback([Output('saveDataIngestionLoadingOutput',"children"),
               Output("saveDataIngestionModalBody","children"),
               Output("saveDataIngestionModal","is_open")],
              [Input('saveDataIngestionBtn', 'n_clicks'),Input("saveDataIngestionModalClose", "n_clicks")],
              State("goliveStorageAccount","value"),
              State("goliveContainer","value"),
              [State({"goLiveFile": ALL}, "value")],
              [State({"goLiveRefreshTime": ALL}, "value")],
              [State({"goLiveRefreshUnit": ALL}, "value")],
              [State({"goLiveGranularityTime": ALL}, "value")],
              [State({"goLiveGranularityUnit": ALL}, "value")],
              [State({"goLiveIsIoT": ALL}, "value")],
              [State({"goLiveIsIoTEnitity": ALL}, "value")],
              [State({"goLiveAPIType": ALL}, "value")],
               State("existingExperiment","data")
)
def saveDataIngestion(clicks,closeClicks,*args):
    if closeClicks > 0 and ctx.triggered_id == "saveDataIngestionModalClose":
        return "","",False
    if clicks:
        try:
            storageAccountDetails = {
                "goliveStorageAccount": args[0],
                "goliveContainer": args[1]
            }
            dataRefreshDetails = []
            for i in range(2):
                dataRefreshDetails.append({
                    "goLiveFile": args[2][i],
                    "goLiveRefreshTime": args[3][i],
                    "goLiveRefreshUnit": args[4][i],
                    "goLiveGranularityTime": args[5][i],
                    "goLiveGranularityUnit": args[6][i],
                    "goLiveIsIoT": args[7][i],
                    "goLiveIsIoTEnitity": args[8][i]
                })
            for i in range(len(args[2])-2):
                apiMapping = {
                    "goLiveFile": args[2][i+2],
                    "goLiveAPIType": args[9][i]
                }
            data = args[10]
            # # Delete all records in database
            dboperations.executeStoredProcedure(DELETE_DATA_INGESTION_SP,"@ExperimentSetID = ?",(data["experimentsetid"]),"golive",0)
            # # Execute stored procedure to save selected rows to database
            dboperations.executeStoredProcedure(SAVE_DATA_INGESTION_SP,"@ExperimentSetID = ?,@SourceDataDetails=?, @DataRefreshDetails=?,@ApiMapping=?",(data["experimentsetid"],json.dumps(storageAccountDetails),json.dumps(dataRefreshDetails),json.dumps(apiMapping)),"golive",0)
            
            return  ["", "Selection saved successfully!", True]
            
        except Exception as e:
            print("Error:", e)
            return ["", "Save operation failed", True]
    else:
        raise PreventUpdate()

# Enable Events save button
@app.callback(Output("saveEventSetupBtn", 'disabled'),
              [Input('modelRetrainTime', 'value'), Input('modelRetrainUnit', 'value')
               , Input("catColThreshold","value"), Input("numColThreshold","value")],
)
def onEventGridSelection(modelRetrainTime,modelRetrainUnit,catColThreshold,numColThreshold):
    print("Triggered on model selection")
    save_btn_disabled = True
    if (modelRetrainTime is not None and modelRetrainUnit is not None) or (catColThreshold is not None and numColThreshold is not None):
        print("State updated")
        save_btn_disabled = False

    return save_btn_disabled

# Save Event configuration
@app.callback([Output('saveEventConfigLoadingOutput',"children"),
               Output("saveEventConfigModalBody","children"),
               Output("saveEventConfigModal","is_open")],
              [Input('saveEventSetupBtn', 'n_clicks'),Input("saveEventConfigModalClose", "n_clicks")],
              State('modelRetrainTime', 'value'), State('modelRetrainUnit', 'value'),
               State("existingExperiment","data"), State("catColThreshold","value"), State("numColThreshold","value"), State("historyEnabled","value")
)
def saveDataIngestion(clicks,closeClicks,modelRetrainTime,modelRetrainUnit,data,catColThreshold,numColThreshold,historyEnabled):
    if closeClicks > 0 and ctx.triggered_id == "saveEventConfigModalClose":
        return "","",False
    if clicks:
        try:
            eventConfig = {
                "modelRetrainTime": modelRetrainTime,
                "modelRetrainUnit": modelRetrainUnit,
                "historyEnabled" : historyEnabled,
                "catColThreshold": catColThreshold,
                "numColThreshold": numColThreshold
            }
            # # Delete all records in database
            dboperations.executeStoredProcedure(DELETE_EVENT_CONFIG_SP,"@ExperimentSetID = ?",(data["experimentsetid"]),"golive",0)
            # # Execute stored procedure to save selected rows to database
            dboperations.executeStoredProcedure(SAVE_EVENT_CONFIG_SP,"@ExperimentSetID = ?,@RetrainingSchedule=?",(data["experimentsetid"],json.dumps(eventConfig)),"golive",0)
            
            return  ["", "Selection saved successfully!", True]
            
        except Exception as e:
            print("Error:", e)
            return ["", "Save operation failed", True]
    else:
        raise PreventUpdate()

# Enable save deployment button
@app.callback(Output("saveDeploymentSetupBtn", 'disabled'),
              [Input('acceleratortype', 'value'), Input('cost', 'value'), Input('hostingmodel', 'value'), Input('versiondependency', 'value'), Input('platformpreference', 'value'), Input('modelType', 'value')],
)
def onModelDeploySelection(acceleratortype,cost,hostingmodel,versiondependency,platformpreference,modelType):
    print("Triggered on model selection")
    save_btn_disabled = True
    if acceleratortype is not None and cost is not None and hostingmodel is not None and versiondependency is not None and platformpreference is not None and modelType:
        print("State updated")
        save_btn_disabled = False

    return save_btn_disabled

# Save Model Deployment configurations
@app.callback([Output('saveDeploymentLoadingOutput',"children"),
               Output("saveDeploymentModalBody","children"),
               Output("saveDeploymentModal","is_open")],
              [Input('saveDeploymentSetupBtn', 'n_clicks'),Input("saveDeploymentModalClose", "n_clicks")],
              State('acceleratortype', 'value'), State('cost', 'value'), State('hostingmodel', 'value'), State('versiondependency', 'value'), State('platformpreference', 'value'), State('modelType', 'value'),
               State("existingExperiment","data")
)
def saveDeploymentConfig(clicks,closeClicks,acceleratortype,cost,hostingmodel,versiondependency,platformpreference,modelType,data):
    if closeClicks > 0 and ctx.triggered_id == "saveDeploymentModalClose":
        return "","",False
    if clicks:
        try:
            deplopymentConfig = {
                "acceleratortype":acceleratortype,
                "cost":cost,
                "hostingmodel":hostingmodel,
                "versiondependency":versiondependency,
                "platformpreference":platformpreference,
                "modelType":modelType
            }
            # # Delete all records in database
            dboperations.executeStoredProcedure(DELETE_MODEL_DEPLOYMENT_SP,"@ExperimentSetID = ?",(data["experimentsetid"]),"golive",0)
            # # Execute stored procedure to save selected rows to database
            dboperations.executeStoredProcedure(SAVE_MODEL_DEPLOYMENT_SP,"@ExperimentSetID = ?,@deploymentManagerConfig=?",(data["experimentsetid"],json.dumps(deplopymentConfig)),"golive",0)
            
            return  ["", "Selection saved successfully!", True]
            
        except Exception as e:
            print("Error:", e)
            return ["", "Save operation failed", True]
    else:
        raise PreventUpdate()
    
# Enable save notification configurations button
@app.callback(Output("saveNotificationBtn", 'disabled'),
              [Input('receiversList', 'value')],
)
def onNotificationConfigUpdate(receiversList):
    print("Triggered on notification configurations")
    save_btn_disabled = True
    if receiversList is not None:
        print("State updated")
        save_btn_disabled = False

    return save_btn_disabled

# Save Notification configurations
@app.callback([Output('saveNotificationLoadingOutput',"children"),
               Output("saveNotificationModalBody","children"),
               Output("saveNotificationModal","is_open")],
              [Input('saveNotificationBtn', 'n_clicks'),Input("saveNotificationModalClose", "n_clicks")],
              State('receiversList', 'value'), State('smtpServer', 'value'), State('smtpPort', 'value'),
               State("existingExperiment","data")
)
def saveNotificationConfig(clicks,closeClicks,receiversList,smtpServer,smtpPort,data):
    if closeClicks > 0 and ctx.triggered_id == "saveNotificationModalClose":
        return "","",False
    if clicks:
        try:
            smtpServer = "smtp-mail.outlook.com" if smtpServer is None else smtpServer
            smtpPort = "587" if smtpPort is None else smtpPort
            notificationConfig = {
                "receiversList":receiversList,
                "smtpServer":smtpServer,
                "smtpPort":smtpPort
            }
            # # Delete all records in database
            dboperations.executeStoredProcedure(DELETE_NOTIFICATION_CONFIG_SP,"@ExperimentSetID = ?",(data["experimentsetid"]),"golive",0)
            # # Execute stored procedure to save selected rows to database
            dboperations.executeStoredProcedure(SAVE_NOTIFICATION_CONFIG_SP,"@ExperimentSetID = ?,@Config=?",(data["experimentsetid"],json.dumps(notificationConfig)),"golive",0)
            
            return  ["", "Selection saved successfully!", True]
            
        except Exception as e:
            print("Error:", e)
            return ["", "Save operation failed", True]
    else:
        raise PreventUpdate()

# DO NOT DELETE (This is to automate the go live flow)
# Prepare go live event manager function app and deploy it on Azure
# @app.callback(Output('setupLoadingOutput',"children"),Output('deployModelBtn', 'disabled'),
#               [Input('goliveFunctionAppBtn', 'n_clicks')],
#               State("existingExperiment","data")
# )
# def saveConfig(goliveFunctionAppBtnClick,data):
#     if ctx.triggered_id == "goliveFunctionAppBtn" and goliveFunctionAppBtnClick > 0:
#         print("Go live function app button clicked")
#         data["fileUpload"] = "true"
#         data["deploymentType"] = "best"
#         devops.generateDevOpsRequest(config.GoLiveAppDeployemntBuildId,data)
    
#         return "",False
#     else:
#         raise PreventUpdate()
    
# # Deploy model using Deployment manager
# @app.callback([Output('deployLoadingOutput',"children")],
#               [Input('deployModelBtn', 'n_clicks')],
#               State("existingExperiment","data")
# )
# def saveDeploymentConfig(deployModelBtnClick,data):
#     if deployModelBtnClick > 0 and ctx.triggered_id == "deployModelBtn":
#         data["deploymentType"] = "best"
#         # Setup and deploy go live AKS module
#         devops.generateDevOpsRequest(config.DeploymentManagerBuildId,data)

#         logging.info("Deployment complete")
#         return [""]
#     else:
#         raise PreventUpdate()