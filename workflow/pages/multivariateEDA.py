#Copyright (c) Microsoft. All rights reserved.
#  
from dash import html , dcc, ctx
from dash.dependencies import Input, Output ,State
import dash_bootstrap_components as dbc
import pandas as pd
from dash import dash_table
from datetime import timedelta, datetime
from dash.exceptions import PreventUpdate
import json
import ast
import os
# Import master app object
from workflow.main import app
from workflow.common.MultivariatePlotly import * 
from workflow.common.WindPlotly import * 
from workflow.common.SolarPlotly import * 

### Import utilities ###
from utilities.azure import blobOperations
from utilities.dboperations import dboperations
from workflow.common.common import listToOptions, fileTypeList, getLoadingElement, dropdownTags, btnTags, detect_special_characer, getModalPopup
from workflow.common.config import *
from workflow.common.PrepopulateTransformations import * 
from workflow.common import getdata

multivariateCols = ['AnalysisType','RelevantColumns','Params']
multivariateColsOptions = []
for i in multivariateCols:
    multivariateColsOptions.append({'name': i,'id': i,'deletable': True,'editable': True } )

layout = html.Div([ 
                    dbc.Row([
                                dropdownTags('Multivariate EDA List','multivariateEDA',3,multi= True),
                                btnTags("Select Graphs",'selectgraphBtn',2) ,
                         ]),
                        getLoadingElement("multivariateInfoSaveLoading"),
                        dbc.Row([
                        dbc.Col([
                        dash_table.DataTable(
                            id='multivariateTable',
                            columns=multivariateColsOptions,
                            editable=True,
                            row_deletable=True,
                            # Styling alternate rows
                            style_data_conditional=[{
                                                    'if': {'row_index': 'odd'},
                                                    'backgroundColor': 'rgb(220, 220, 220)',
                                                     }] )
                        ]) 
                    ]),

                    getLoadingElement("graphloading"),

                    getLoadingElement("edapageLoading"),

                     dbc.Row([
                        dbc.Col([],width=11) , btnTags("save",'savemultivariateBtn',1,True) ,
                    ]),

                    dbc.Row([ 
                                    html.Div(children=[],id = 'multivariategraphComponent'),
                             ]),

                             getModalPopup("saveedaModal","Alert",""),
         ], id="multivariateEDAContainer")

def getColumnAndTags(newColsdataDF,transData,mergedDataColumns):
    df = transData
    newColsdataDF = newColsdataDF[['Name','Tag']]
    newColsdataDF.rename(columns={'Name':'ColumnName'},inplace = True)
    finalDF = pd.concat([df,newColsdataDF],axis = 0 )
    cols =  finalDF['ColumnName'].unique()
    colsTags= finalDF.groupby('Tag').agg(list)
    colTags = colsTags.reset_index()

    dct = {}
    for i in range(len(colTags)) :
        tg = colTags.iloc[i,:]['Tag']
        colum = colTags.iloc[i,:]['ColumnName']
        dct[tg] = colum
    return dct

# page load method
@app.callback(Output('multivariateEDA','options'),Output('edapageLoading','children'),
                [Input('data', 'children')],
              State('experimentStore','data'))
def onTabLoad(inp1, data):
    global multivariateDF,col,colist
    storeDataValue = getdata.getForecastSetupDetails(data)
    targetTimezone = str(storeDataValue.iloc[0,:]['TimeZone'])

    EntityTypeList = getdata.getEntityType(data)
    EntityType = EntityTypeList[0]['EntityType']
    experimentSetName = data["experimentsetname"]
    path = f'{MASTER_FOLDER}/{experimentSetName}/{MERGED_FOLDER}'#
    print("Executing tab 7 page load")
    blobOperations.downloadBlob(f'{path}/{PreprocessedFileName}',"")
    multivariateDF = pd.read_csv(os.path.join(path,PreprocessedFileName) ,index_col=0)
    multivariateDF.reset_index(inplace = True)
    multivariateDF['DateTime'] = pd.to_datetime(multivariateDF['DateTime'], utc=True).map(lambda x: x.tz_convert(targetTimezone))
    #multivariateDF['DateTime'] = pd.to_datetime(multivariateDF['DateTime'],utc = True )
    multivariateDF['Year'] = multivariateDF['DateTime'].dt.year
    multivariateDF['Month'] = multivariateDF['DateTime'].dt.month
    multivariateDF['DayOfWeek'] = multivariateDF['DateTime'].dt.dayofweek
    multivariateDF['Date'] = multivariateDF['DateTime'].dt.date
    multivariateDF.set_index('Date', inplace=True)
    global finalCols
    dateCols = ['DateTime','Year','Month','DayOfWeek','AvailableTime']
    finalCols = [col for col in list(multivariateDF.columns) if col not in dateCols  ]
    finalCols = [item for item in finalCols if not 'Unnamed' in item]

    newColsdata = getdata.getNewColumnInfo(data)
    newColsdataDF = pd.DataFrame(newColsdata ,columns = ['Name','Tag'])
    newColsList = newColsdataDF["Name"].values.tolist()
    #Read transformation data
    transdata = getdata.getTransformationDetails(data)
    transDataDf = pd.DataFrame(transdata)
    transformdata = transDataDf['Transformations'].values
    df = pd.DataFrame()
    for i in range(len(transformdata)):
        jsn =  json.loads(transformdata[i])
        df1 = pd.DataFrame(jsn)
        df = pd.concat([df,df1] ,axis = 0)
    df.rename(columns = {'ColumnTag' : 'Tag'} ,inplace = True)
    df['ColumnName'] = df['FileIdentifier'] + '_' + df['ColumnName']
    transDataDf = df
    # Identify Entity field
    entityFile = transDataDf[transDataDf["FileType"] == "Entity"]
    entityField = entityFile["ColumnName"].values[0]
    # Get column to tag mapping
    columnTagsDict = getColumnAndTags(newColsdataDF,transDataDf[['ColumnName','Tag']],finalCols)
    global mp
    mp = MultivariatePlotly(multivariateDF, finalCols, index="Date", domain_name= 'wind', tag_col_dict=columnTagsDict)
    return listToOptions(['box_plot','line_graph','cdf_graph','heatmap_graph','scatter_graph','hexbin_graph']) ,""

@app.callback(Output('multivariategraphComponent','children'),Output("graphloading","children"),
                Input('multivariateTable','active_cell'),
                State('multivariateTable', 'data'))
def getgraph(active,multivariateTable):
    if active is not None : 
        df = pd.DataFrame(multivariateTable)
        cols = list(multivariateDF.columns)
        graphType = df.iloc[active['row'],:]['AnalysisType']
        sel_funcs, relevent_cols, params, fig_list = mp.create__table([graphType])
        for fig in fig_list:
            return dcc.Graph(id = graphType,figure = fig,style={'width': '175vh', 'height': '60vh'})   ,""   
    else : 
        raise PreventUpdate()

@app.callback(  [Output('multivariateTable', 'data'),Output("savemultivariateBtn","disabled")],
                Input('selectgraphBtn','n_clicks'),Input('data', 'children'),
                State('multivariateTable', 'data'),
                State('experimentStore','data'),
                State('multivariateEDA','value')
                 )
def addData(n_clicks,inp1,multivariateTable,storeData,graphList):
    if n_clicks > 0 : 
        if multivariateTable is None : 
            multivariateTable = []
        sel_funcs, relevent_cols, params, fig_list = mp.create__table(graphList)
        for i in range(len(graphList)):
            row = {"AnalysisType": sel_funcs[i] ,"RelevantColumns": str(relevent_cols[i]),"Params": str(params[i]) }
            multivariateTable.append(row)
        return [multivariateTable,False]
    elif "multivariateSelections" in storeData.keys():
        multivariateTable = storeData["multivariateSelections"]
        return [multivariateTable,False]
    else : 
        raise PreventUpdate()

# Save Button for column info
@app.callback( Output("multivariateInfoSaveLoading","children"),Output("saveedaModalBody","children"),
                Output("saveedaModal","is_open"),Input("saveedaModalClose", "n_clicks"),
    Input('savemultivariateBtn', 'n_clicks'),Input('data', 'children'),
    [State('multivariateTable', 'data'),State('experimentStore','data')]
)
def saveNewColumnInformation(edasaveclick,clicks,inp1,multivariateTable,data):
    if  edasaveclick > 0 and ctx.triggered_id == "saveedaModalClose":
        return "","",False
    if clicks > 0 and ctx.triggered_id == "savemultivariateBtn": 
        try:
            # Delete all records in database
            dboperations.executeStoredProcedure(DELETE_MULTIVARIATEEDA_SP,"@ExperimentSetID = ? ",(data["experimentsetid"]),"dbo",0)
            
            # Save timezone details to database
            dboperations.executeStoredProcedure(SAVE_MULTIVARIATEEDA_SP, "@ExperimentSetID = ? ,@GraphSelectionDetails=?",(data["experimentsetid"], json.dumps(multivariateTable)),"dbo",0)
            
            print("Saved column information!")

            return "",DATA_SAVE_MESSAGE,True
        except Exception as ex:
            print(ex)
            raise PreventUpdate()
    else:
        raise PreventUpdate()