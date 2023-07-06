#Copyright (c) Microsoft. All rights reserved.

# source data 
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
from utilities.azure import blobOperations
from utilities.dboperations import dboperations
from workflow.common.common import listToOptions, fileTypeList, getLoadingElement, dropdownTags, detect_special_characer, getModalPopup

from workflow.common.config import *

dash_tbl_col_list = ["FileType","AccountName","ContainerName" ,"BlobName" ,"Tag","FileIdentifier" ]
dash_tbl_col_options = []
for i in dash_tbl_col_list:
    dash_tbl_col_options.append({'name': i,'id': i,'deletable': True,'renamable': True } )


tagsList = {'Entity' : ['Farm-level', 'Turbine-level', 'Block-level', 'Sub-regional'] ,
              'PastCovariates' : [ 'IoT/Sensor', 'SCADA', 'Historical Actuals' , 'Airport'],
                'FutureCovariates' : ['Historical Forecasts','Airport','Weather'] }

fileTypeOptions = listToOptions(fileTypeList) 

layout = html.Div([
         html.Div([
                    dbc.Row([  
                            dbc.Col([
                                html.Label('File Type'),
                                dcc.Dropdown(id = 'FileType' ,options = fileTypeOptions ),
                            ],width = 4),
                            dbc.Col([
                                html.Label('Account Name'),
                                dcc.Dropdown(id = 'AccountName'  ),
                            ],width = 4),
                            dbc.Col([
                                html.Label('Container Name'),
                                dcc.Dropdown(id = 'ContainerName' ),
                            ],width = 4)
                        ]),
                        getLoadingElement("storageAccountLoading"),
                        getLoadingElement("containerLoading"),
                        getLoadingElement("storageAccountFileLoading"),
                    dbc.Row([
                            dbc.Col([
                                html.Label('Blob Name'),
                                dcc.Dropdown(id = 'BlobName' ),
                            ],width = 4),
                            dropdownTags('File Tag',"tagsDropdown",4,True,False),
                                dbc.Col([
                                            html.Label('File Identifier'),
                                            dcc.Input( id = 'FileIdentifier',type = 'text',
                                            placeholder = 'Enter in FileIdentifier:',style={
                                            'width': '100%'})
                                    ],width = 4)
                            ]),
                    
                    dbc.Row([
                            dbc.Col([
                                    html.Button("Add",id = 'sourceAddButton',n_clicks = 0 )
                                    ],width = 4,align = 'end')
                            ]),
                    getLoadingElement("addRowLoading"),
                    dbc.Row([
                       html.I('***Note : click on any cell of the below rows to display respective source data***'),
                       html.I('***Note : supported maximum filesize is 10 MB and supported filetype is csv***')
                    ]),
                    dcc.Store(id='intermediate-sourcevalue'),
                    dbc.Row([
                            dbc.Col([
                            dash_table.DataTable(
                            id='sourceListTable',
                            columns=dash_tbl_col_options,
                            editable=True,
                            row_deletable=True,
                            persistence = True,
                            persisted_props = ['data'],
                            persistence_type = 'session',
                            # Styling alternate rows
                            style_data_conditional=[{
                                            'if': {'row_index': 'odd'},
                                            'backgroundColor': 'rgb(220, 220, 220)',
                                            }]
                            
                            
                         )
                        ]) ]),
                    getLoadingElement("secondTableLoading"),
                    dbc.Row([
                            dbc.Col ([ 
                            html.Div(id = 'sourcetable')
                            ] ,width = 8) ,

                        dbc.Col ([  
                                    html.Button(children = "Save",id = 'saveButton',n_clicks = 0 , style={"float":"right"})
                            ] , align = 'baseline')
                         ]),
                        #  html.Div(id = 'sourcePageValidation'),
                         getModalPopup("sourcePageModal","Alert",""),
                         getModalPopup("saveSourcePageModal","Alert",""),
                         dcc.Store(id='intermediate-value3') ,
                    ])
]       )

blobOperations.getStorageAccountList()

@app.callback(
    Output('AccountName','options') ,
    Output('tagsDropdown','options') , 
    Output("storageAccountLoadingOutput","children"),
    Input('FileType','value' ))
def accountDropdown(value):
    if value is not None:
        global df
        opts = blobOperations.getStorageAccountList()
        options=[{'label':opt, 'value':opt} for opt in opts]
        tagOptions =   listToOptions(tagsList[value])
        return options ,tagOptions, ""
 
@app.callback(
    Output('ContainerName','options') ,
    Output("containerLoadingOutput","children"),
    Input('AccountName','value'))
def containerDropdown(account_name):
    if account_name is not None:
        opts = blobOperations.getContainerList(account_name)
        options=[{'label':opt, 'value':opt} for opt in opts]
        return options , ""
    else:
        raise PreventUpdate()

@app.callback(
    Output('BlobName','options' ) ,
    Output("storageAccountFileLoadingOutput","children"),
    State('AccountName','value' ),
    Input('ContainerName','value'))
def blobDropdown(account_name,container_name):
    if (account_name is not None and container_name is not None):
        opts,_ = blobOperations.getBlobList(container_name)
        options=[{'label':opt, 'value':opt} for opt in opts]
        return options , ""
    else:
        raise PreventUpdate()

@app.callback(
    Output('sourceListTable', 'data'),
    Output("sourcePageModalBody","children"),Output("sourcePageModal","is_open"),
    
    [Input('sourceAddButton', 'n_clicks'),Input('data', 'children'),Input("sourcePageModalClose", "n_clicks")],
    [State('sourceListTable', 'data'),
    State('FileType', 'value'),
    State('AccountName', 'value'),
    State('ContainerName', 'value'),
    State('BlobName', 'value'),
    State('tagsDropdown', 'value'),
    State('FileIdentifier', 'value'),
    State('experimentStore','data')]
   )
def addRowToTable(n_clicks,inp1, closeClicks, rows, FileType,AccountName,ContainerName,BlobName,Tag,FileIdentifier,storeData):
    validateMessage = ''
    if rows is None : 
            rows = []
    if closeClicks > 0 and ctx.triggered_id == "sourcePageModalClose":
        return rows,validateMessage, False
    if n_clicks > 0 :
        validationValues = [FileType,AccountName,ContainerName,BlobName,Tag,FileIdentifier]

        for value in validationValues :
            # add more validations
            if value == '' or  value is None :
                validateMessage =  "All Fields Are Mandatory"
                return rows,validateMessage, True

        filesIdentifierList = [rows[i]['FileIdentifier'] for i in range(len(rows))]
        if FileIdentifier in filesIdentifierList :
            validateMessage =  "File Identifier Already Exists"
            return rows,validateMessage, True

        if detect_special_characer(FileIdentifier) :
            validateMessage =  "Special Characters Not Allowed in File Identifiers Field"
            return rows,validateMessage, True
        
        rows.append({"FileType": FileType,"AccountName": AccountName ,"ContainerName": ContainerName ,"BlobName": BlobName,"Tag": str(Tag) ,"FileIdentifier": FileIdentifier  })
        return rows,validateMessage, False

    elif "sourceDataDetails" in storeData.keys():
        rows = storeData["sourceDataDetails"]
        return rows,validateMessage, False
    else:
        raise PreventUpdate()

# Update state of Save button
@app.callback(Output('saveButton','disabled'),
              [Input('sourceListTable', 'data_previous'),Input('sourceListTable', 'data')],
              [State('sourceListTable', 'data')])
def rowsRemoved(previous,inputCurrent,current):
    print("Enabling Save invoked")
    if current is None or len(current) == 0:
        return True # Disable save if there are no rows in current view of the table
    else:
        return False

@app.callback(
    Output('sourcetable','children'), Output("secondTableLoadingOutput","children"),
    [State('sourceListTable', 'rows'),
     State('sourceListTable', 'data'),Input("sourceListTable",'active_cell')])
def displaySourceData(rows,data,active):
    df = pd.DataFrame(data)
    AccountName = df.iloc[active['row'],:]['AccountName']
    ContainerName = df.iloc[active['row'],:]['ContainerName']
    BlobName = df.iloc[active['row'],:]['BlobName']
    data,_,columns = blobOperations.getBlobDf(AccountName,ContainerName,BlobName)
    columnNames =  [{"name": i, "id": i,} for i in columns]
    data = data.to_dict('rows')
    return dash_table.DataTable(data=data, columns=columnNames,persistence = True,persisted_props = ['data'],
                                         persistence_type = 'session',style_table={'overflowX': 'scroll'},style_cell={
                                'textAlign': 'center',
                                'minWidth': '80px', 'width': '80px', 'maxWidth': '80px'
                            },
                            # Styling alternate rows
                            style_data_conditional=[{
                                                    'if': {'row_index': 'odd'},
                                                    'backgroundColor': 'rgb(220, 220, 220)',
                                                     }]
                            ,
                            ), ""

#Add SAVE Button and data loads into Database 
@app.callback(
    [Output('tab-4','disabled'), Output("addRowLoadingOutput","children"),Output("saveSourcePageModalBody","children"),Output("saveSourcePageModal","is_open")],
    Input('saveButton', 'n_clicks'),Input('data', 'children'),Input('sourceListTable', 'data'),Input("saveSourcePageModalClose", "n_clicks"),
    State('sourceListTable', 'data'),State('experimentStore','data'))
def saveData(n_clicks,inp1,inpDataTable,closeClicks,currentDataTable,data):
    if ctx.triggered_id == "saveSourcePageModalClose" and closeClicks is not None and closeClicks > 0:
        return [False, "","",False]
    if n_clicks > 0:
        try:
            # Delete all records in database
            dboperations.executeStoredProcedure(DELETE_SOURCEDATA_DETAILS_SP,"@ExperimentSetID = ? ",(data["experimentsetid"]),"dbo",0)
            identifier = 0
            for row in currentDataTable:
                # Save forecast details to database
                dboperations.executeStoredProcedure(SAVE_SOURCEDATA_DETAILS_SP ,"@ExperimentSetID = ? ,@RowID=?, @FileType =?, @AccountName=?, @ContainerName=?, @BlobName =?, @Tag =?, @FileIdentifier =?",(data["experimentsetid"], identifier, row["FileType"],row["AccountName"],row["ContainerName"],row["BlobName"],row["Tag"],row["FileIdentifier"]),"dbo",0)
                identifier = identifier + 1
            print("Saved source data information!")
            return [False, "",DATA_SAVE_MESSAGE,True]
        except Exception as ex:
            print(ex)
            raise PreventUpdate()
    elif "sourceDataDetails" in data.keys():
        return [False, "","",False]
    elif ctx.triggered_id == "sourceListTable" and (currentDataTable is None) and (currentDataTable is None or len(currentDataTable) == 0):
        return [True, "","",False]
    else:
        raise PreventUpdate()