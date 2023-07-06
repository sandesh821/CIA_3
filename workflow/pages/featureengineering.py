#Copyright (c) Microsoft. All rights reserved.
import dash
from dash import html , dcc, ctx
from dash.dependencies import Input, Output ,State
import dash_bootstrap_components as dbc
import pandas as pd
from dash import dash_table
from datetime import timedelta, datetime
from dash.exceptions import PreventUpdate
import json
import os
# Import master app object
from workflow.main import app
import ast

### Import utilities ###
from utilities.azure import blobOperations
from utilities.dboperations import dboperations
from workflow.common.common import listToOptions, fileTypeList, getLoadingElement, dropdownTags, btnTags, detect_special_characer, getModalPopup
from workflow.common.config import *
from workflow.common.PrepopulateTransformations import * 
from workflow.common.MissingValueEDA import * 
from workflow.common import getdata
from workflow.common.ColumnAdder import * 
from workflow.common.ColumnCreatorUtils import * 
from workflow.common.InterpolatorMethods import * 

columnCreaterObj = ColumnCreatorUtils()
columnCreator = list(ColumnCreatorUtils.all_funcs.keys())

columnCreatorOptions = listToOptions(columnCreator)


createColsList = ['ColumnCreator','ColumnMethod','ColumnList','Name','InterpolationClass','InterpolationMethod','Tag','Params']
createColsOptions = []
for i in createColsList:
    createColsOptions.append({'name': i,'id': i } )

columnCreatorMethods = {'pandas' : list(columnCreaterObj.pandas_funcs.keys()),'numpy': list(columnCreaterObj.numpy_funcs.keys()) , 'custom': list(columnCreaterObj.custom_funcs.keys()) , 'virtualsensors': list(columnCreaterObj.virtualsensors_funcs.keys())   }

interpolColsList = ['ColumnName','InterpolationClass','InterpolationMethod','Params']
interpolColsOptions = []
for i in interpolColsList:
    interpolColsOptions.append({'name': i,'id': i,'deletable': True,'editable': True } )

interpolateClass = ['pandas','others']
interpolateClassOptions = listToOptions(interpolateClass)
interpolateMethodsObj = InterpolatorMethods()
interpolateMethods = {'pandas' : interpolateMethodsObj.pandas_methods,'others' : interpolateMethodsObj.extra_methhods}

layout = html.Div([
                    dbc.Row([  
                          dbc.Row([
                                dropdownTags('Column Creator Class','columnCreator',2),
                                dropdownTags('Column Creator Method','columnMethod',2),
                                dropdownTags('Columns','ColumnList',2,multi=True),
                                dbc.Col([ 
                                            html.Label('Name'),
                                            dcc.Input( id = 'name',type = 'text',style = {'width': '100%'})
                                        ],width = 2),
                                dropdownTags('Interpolation Class','interpolationClass',2),
                                dropdownTags('Interpolation Method','interpolationMethod',2)
                                ]
                                ),
                        dbc.Row([
                            dropdownTags('Tag','tag',2),
                                dbc.Col([ 
                                    html.Label('Param Value'),
                                    dcc.Input( id = 'paramValue1',type = 'text',style = {'width': '100%'})
                                ],width = 2),
                                dbc.Col([],width=4) , 
                                btnTags("Add",'addColumnsButton',2),
                                btnTags("Save",'saveaddColumnsBtn',2,True)
                            ]),
                   getLoadingElement("columnInfoSaveLoading"),
                   dbc.Row([
                        dbc.Col([
                        dash_table.DataTable(
                            id='ColumnsTable',
                            columns=createColsOptions,
                            editable=False,
                            row_deletable=True,
                            # Styling alternate rows
                            style_data_conditional=[{
                                                    'if': {'row_index': 'odd'},
                                                    'backgroundColor': 'rgb(220, 220, 220)',
                                                     }]
                        )
                        ]) 
                    ]),

                dbc.Row([
                dbc.Col([],width=10) , btnTags("Create New Columns",'createColsBtn',2,disabled=True) ,
                ]),
                getLoadingElement("createcolumnsLoading"),
                getModalPopup("addcolsModal","Alert",""),
                getModalPopup("saveColsModal","Alert",""),
                dbc.Row([
                    dbc.Col([],width=10) , btnTags("Missing Values Analysis",'missingValAnalysisBtn',2) ,
                ]),
                getLoadingElement("missingvalueAnalysisLoading"),
                dbc.Row([ 
                            html.Div(children=[],id = 'missingValuesGraph'),
                             ]),

                dbc.Row([
                    dropdownTags('Interpolate Columns','interpolCols',2,disabled=  True),
                    dbc.Col([ 
                            html.Label('Interpolate Class'),
                            dcc.Input( id = 'interpolClassValue',type = 'text',style = {'width': '100%'} )
                        ],width = 2),
                        
                        dbc.Col([ 
                            html.Label('Interpolate Method'),
                            dcc.Input( id = 'interpolMethodValue',type = 'text',style = {'width': '100%'})
                        ],width = 2),
                    
                    dbc.Col([ 
                            html.Label('Param Value'),
                            dcc.Input( id = 'paramValue',type = 'text',style = {'width': '100%'} )
                        ],width = 2)

                    ]),

                    dbc.Row([
                            dbc.Col([],width=8), 
                            btnTags("Add",'addInterpolCols',2),
                            btnTags("Save",'saveInterpolColsBtn',2,True)
                            ]),

                    getLoadingElement("interpolationInfoSaveLoading"),
                    getModalPopup("saveintercolsModal","Alert",""),
                    getModalPopup("addintercolsModal","Alert",""),
                    dbc.Row([html.Div(id = 'testColsMessage') ]),
                    dbc.Row([
                        dbc.Col([
                        dash_table.DataTable(
                            id='interpolateTable',
                            columns=interpolColsOptions,
                            editable=False,
                            row_deletable=True,
                            # Styling alternate rows
                            style_data_conditional=[{
                                                    'if': {'row_index': 'odd'},
                                                    'backgroundColor': 'rgb(220, 220, 220)',
                                                     }]
                        )
                        ]) 
                    ]),

                dbc.Row([
                dbc.Col([],width=10) , btnTags("Interpolate",'interpolateButton',2) ,
                ]),
                getLoadingElement("interpolatexecuteLoading"),
                

                dbc.Row([
                    dbc.Col([],width=10) , btnTags("Post Missing Value Analysis",'postmissingValAnalysisBtn',2,True) ,
                ]),
                getLoadingElement("postmissingValuesGraphLoading"),
                dbc.Row([ 
                            html.Div(children=[],id = 'postmissingValuesGraph'),
                             ]),

                 getModalPopup("featurepageModal","Alert",""),
             ])
                       
         ], id="featureEngineeringContainer")

def performInterpolation(interpolateTableDF,df):
    im = InterpolatorMethods()
    lst = []
    for i in range(len(interpolateTableDF)):
        dct = {}
        dct['family_func'] = interpolateTableDF.iloc[i,:]['InterpolationClass']
        dct['col'] = interpolateTableDF.iloc[i,:]['ColumnName']
        dct['method'] = interpolateTableDF.iloc[i,:]['InterpolationMethod']
        dct['vals']  = ast.literal_eval(interpolateTableDF.iloc[i,:]['Params'])
        lst.append(dct)
    df = im.interpolate_all(df, lst)

    # Remove timezone info
    if 'AvailableTime' in df.columns : 
        df['AvailableTime'] = df['AvailableTime'].apply(lambda i : str(i)[:-6])
        df['AvailableTime'] = pd.to_datetime(df['AvailableTime'] )
    df.reset_index(inplace = True)
    
    df['DateTime'] = df['DateTime'].astype(str)
    df['DateTime'] = df['DateTime'].apply(lambda i : i[:-6])
    df['DateTime'] = pd.to_datetime(df['DateTime'] )
    df = df.set_index(pd.DatetimeIndex(df['DateTime']) )
    del df['DateTime']
    return df

@app.callback(  [
                Output("featurepageModalBody","children"),
                Output("featurepageModal","is_open"),
                Output("postmissingValAnalysisBtn","disabled"),
                Output("interpolatexecuteLoading","children"),
                Output('tab-7','disabled'),Output('tab-8','disabled')],
                Input("featurepageModalClose", "n_clicks"),
                Input('interpolateButton','n_clicks'),
                Input('data', 'children'),
                State('interpolateTable', 'data'),
                State('experimentStore','data')
                 )
def addInterpolateButtonAction(closeClicks,n_clicks,data,interpolateTable,experimentStore):
    validMesage = ''
    if closeClicks > 0 and ctx.triggered_id == "featurepageModalClose":
        return  [validMesage, False,True,"",dash.no_update,dash.no_update]
    if n_clicks > 0 : 
        interpolateTableDF = getdata.getInterpolationInfo(experimentStore)
        interpolateTableDF = pd.DataFrame(interpolateTableDF)
        if len(interpolateTableDF) < 1 :
            validMesage = 'Column Interpolation is not configured'
            return  [validMesage, True,True,"",dash.no_update,dash.no_update]
        df = performInterpolation(interpolateTableDF,columnAddedDF)
        # Create and Save PreprocessedFile to Blob
        experimentSetName = experimentStore['experimentsetname']
        path = f'{MASTER_FOLDER}/{experimentSetName}/{MERGED_FOLDER}'#
        df.to_csv(os.path.join(path,PreprocessedFileName) ,index_label = 'DateTime')
        blobOperations.uploadBlob(os.path.join(path,PreprocessedFileName))   
        return ["Interpolation completed!",False,False,"",False,False]
    elif "interpolationInfo" in experimentStore.keys():
        return [dash.no_update,dash.no_update,dash.no_update,dash.no_update,False,False]
    else :
        raise PreventUpdate()

@app.callback(  [Output('interpolateTable', 'data'),
                Output("saveInterpolColsBtn","disabled"),
                Output("addintercolsModalBody","children"),
                Output("addintercolsModal","is_open")],
                Input("addintercolsModalClose", "n_clicks"),
                Input('addInterpolCols','n_clicks'),
                Input('data', 'children'),
                State('interpolateTable', 'data'),
                State('interpolCols', 'value'),
                State('interpolClassValue', 'value'),
                State('interpolMethodValue', 'value'),
                State('paramValue', 'value'),
                State('experimentStore','data')
                 )
def addInterpolateData(addintercolClick,n_clicks,inp1,interpolateTable,interpolCols,interpolClassValue,interpolMethodValue,paramValue,storeData):
    
    validMesage  =''
    if interpolateTable is None :
        interpolateTable = []
    if addintercolClick > 0 and ctx.triggered_id == "addintercolsModalClose":
        return [interpolateTable,True,validMesage, False]
    if n_clicks > 0 : 
        validationValues = [interpolCols,interpolClassValue,interpolMethodValue,paramValue]
        for value in validationValues :
            if value == '' or  value is None :
                validMesage =  "All Fields Are Mandatory"
                return [interpolateTable,True,validMesage, True]
        row = {"ColumnName": interpolCols,"InterpolationClass": interpolClassValue,"InterpolationMethod": interpolMethodValue ,"Params": paramValue }
        interpolateTable.append(row) 
        return [interpolateTable, False,validMesage, False]
    elif "interpolationInfo" in storeData.keys():
        columnTable = storeData["interpolationInfo"]
        return [columnTable,False,validMesage, False]
    else : 
        raise PreventUpdate()

# Save Button for interpolation info
@app.callback( Output("interpolationInfoSaveLoading","children"),
                Output("saveintercolsModalBody","children"),
                Output("saveintercolsModal","is_open"),
    Input('saveInterpolColsBtn', 'n_clicks'),Input('data', 'children'),Input("saveintercolsModalClose", "n_clicks"),
    [State('interpolateTable', 'data'),State('experimentStore','data')]
)
def saveInterpolationInformation(clicks,inp1,closeClicks,interpolateTable,data):
    if closeClicks > 0 and ctx.triggered_id == "saveintercolsModalClose":
        return dash.no_update,"",False
    if clicks > 0:
        try:
            # Delete all records in database
            dboperations.executeStoredProcedure(DELETE_INTERPOLATIONINFO_SP,"@ExperimentSetID = ? ",(data["experimentsetid"]),"dbo",0) 
            # Save timezone details to database
            dboperations.executeStoredProcedure(SAVE_INTERPOLATIONINFO_SP ,"@ExperimentSetID = ? ,@ColumnDetails=?",(data["experimentsetid"], json.dumps(interpolateTable)),"dbo",0)
            print("Saved column information!")
            return "", DATA_SAVE_MESSAGE, True
        except Exception as ex:
            print(ex)
            raise PreventUpdate()
    else:
        raise PreventUpdate()

@app.callback(
            Output('interpolClassValue','value'),
            Output('interpolMethodValue','value'),
             Input('interpolCols', 'value'),
                State('ColumnsTable','data'),
                State('experimentStore','data'))   
def getparamTags(interpolCols,ColumnsTable,data):

    if interpolCols is not None : 
        transdata = getdata.getTransformationDetails(data)
        transData = pd.DataFrame(transdata)
        transformdata = transData['Transformations'].values
        df = pd.DataFrame()
        for i in range(len(transformdata)):
            jsn =  json.loads(transformdata[i])
            df1 = pd.DataFrame(jsn)
            df = pd.concat([df,df1] ,axis = 0)
        df = df[['ColumnName','InterpolationMethod','InterpolationClass']]
        if ColumnsTable is not None : 
            columnsTableDF = pd.DataFrame(ColumnsTable)
            columnsTableDF.rename(columns= {'Name':'ColumnName'},inplace = True)
            columnsTableDF = columnsTableDF[['ColumnName','InterpolationMethod','InterpolationClass']]
            combineDF = pd.concat([df,columnsTableDF],axis = 0 )
            if interpolCols in columnsTableDF['ColumnName'].unique() :
                getOldColName = interpolCols
            else : 
                getOldColName = interpolCols[interpolCols.find('_')+1:]
        elif ColumnsTable is  None : 
            combineDF = df.copy()
            getOldColName = interpolCols[interpolCols.find('_')+1:]
        interpolationclass = combineDF[combineDF['ColumnName'] == getOldColName ]['InterpolationClass'].values[0]
        interpolationmethod = combineDF[combineDF['ColumnName'] == getOldColName ]['InterpolationMethod'].values[0]
            # print(columnsTableDF['Name'].values[0])
        return interpolationclass,interpolationmethod
    else : 
        raise PreventUpdate()

# Add button callback for add column info
@app.callback(  [Output('ColumnsTable', 'data'),
                Output("saveaddColumnsBtn","disabled"),
                Output("addcolsModalBody","children"),
                Output("addcolsModal","is_open")],
                Input("addcolsModalClose", "n_clicks"),
                Input('addColumnsButton','n_clicks'),
                Input('data', 'children'),
                State('ColumnsTable', 'data'),
                State('columnCreator', 'value'),
                State('columnMethod', 'value'),
                State('ColumnList', 'value'),
                State('name', 'value'),
                State('interpolationClass', 'value'),
                State('interpolationMethod', 'value'),
                State('tag', 'value'),
                State('paramValue1', 'value'),
                State('experimentStore','data')
                 )
def addColumnInfoData(popupclick,n_clicks,inp1,columnTable,ColumnCreator,ColumnMethod, Columns,Name,InterpolationClass,InterpolationMethod,Tag,params,storeData):
    validMesage = ''
    if columnTable is None : 
        columnTable = []
    if popupclick > 0 and ctx.triggered_id == "addcolsModalClose":
        return [columnTable,True,validMesage, False]
    if n_clicks > 0 : 
        validationValues = [ColumnCreator,ColumnMethod, Columns,Name,InterpolationClass,InterpolationMethod,Tag,params]   
        for value in validationValues :
            # add more validations
            if value == '' or  value is None :
                validMesage =  "All Fields Are Mandatory"
                return [columnTable,True,validMesage, True]
        row = {"ColumnCreator": ColumnCreator,"ColumnMethod": ColumnMethod,"ColumnList": str(Columns) ,"Name": Name ,"InterpolationClass": InterpolationClass,"InterpolationMethod": InterpolationMethod ,"Tag": Tag,"Params": str(params) }
        columnTable.append(row) 
        return [columnTable,False,validMesage, False]
    elif "newColumnInfo" in storeData.keys():
        columnTable = storeData["newColumnInfo"]
        return [columnTable,False,validMesage, False]
    else : 
        raise PreventUpdate()


@app.callback(Output('columnMethod','options'),
                Input('columnCreator','value') )
def getinterpolationMethod(columnCreator):
    if columnCreator is not None : 
        options = listToOptions( columnCreatorMethods[columnCreator])
        return options
    else :
        raise PreventUpdate()


# Save Button for column info
@app.callback( Output("columnInfoSaveLoading","children"),Output('createColsBtn','disabled'),
    Input('saveaddColumnsBtn', 'n_clicks'),Input('data', 'children'),
    [State('ColumnsTable', 'data'),State('experimentStore','data')]
)
def saveNewColumnInformation(clicks,inp1,ColumnsTable,data):
    if clicks > 0:
        try:
            # Delete all records in database
            dboperations.executeStoredProcedure(DELETE_NEWCOLUMNINFO_SP,"@ExperimentSetID = ? ",(data["experimentsetid"]),"dbo",0)
            
            # Save timezone details to database
            dboperations.executeStoredProcedure(SAVE_NEWCOLUMNINFO_SP ,"@ExperimentSetID = ? ,@ColumnDetails=?",(data["experimentsetid"], json.dumps(ColumnsTable)),"dbo",0)
            
            print("Saved column information!")

            return "", False
        except Exception as ex:
            print(ex)
            raise PreventUpdate()
    else:
        raise PreventUpdate()


# page load method
@app.callback(Output('columnCreator','options'),
                Output('ColumnList','options'),
                Output('interpolationClass','options'),
                Output('tag','options'),
                [Input('data', 'children')],
              State('experimentStore','data'))
def onTabLoad(inp1, data):
    global mergeDF
    # Download the Merged file if already exists
    fileName = MergedFileName
    EntityTypeList = getdata.getEntityType(data)
    EntityType = EntityTypeList[0]['EntityType']
    expDetails =getdata.getExperimentDetails(data)
    if EntityType == 'wind' :
        siteCapacity = expDetails['SiteCapacity']
    elif EntityType == 'solar' : 
        siteCapacity = expDetails['overallcapacity']
    experimentSetName = data["experimentsetname"]
    path = f'{MASTER_FOLDER}/{experimentSetName}/{MERGED_FOLDER}'#
    try:
        if not os.path.exists(path):
            os.makedirs(path)
        blobOperations.downloadBlob(f'{path}/{fileName}',"")
    except Exception as ex:
        print("Merged File doesn't exist")
        print(ex)

    print("Executing tab 6 page load")
    mergeDF = pd.read_csv(os.path.join(path,'MergedFile.csv'), parse_dates = True,index_col='DateTime')
    columns = list(mergeDF.columns)
    if 'AvailableTime'  in columns : 
        columns.remove("AvailableTime")
    columns = listToOptions(columns)
    print(mergeDF.head(3))
    pt = PrepopulateTransformations({}, "SCADA", EntityType, capacity=siteCapacity)
    columnOptions = listToOptions(pt.accepted_tags)
    return columnCreatorOptions,columns,interpolateClassOptions,columnOptions


@app.callback(Output('interpolationMethod','options'),
                Input('interpolationClass','value') )
def getinterpolationMethod(interpolationClass):
    if interpolationClass is not None : 
        options = listToOptions( interpolateMethods[interpolationClass])
        return options
    else :
        raise PreventUpdate()

def columnCreation(storeData,mergeDF):
    columnsTableDF = getdata.getNewColumnInfo(storeData)
    columnsTableDF = pd.DataFrame(columnsTableDF)

    dictValue = {}
    for row in range(len(columnsTableDF)):
        ColumnCreator = columnsTableDF.iloc[row,:]['ColumnCreator']
        ColumnMethod = columnsTableDF.iloc[row,:]['ColumnMethod']
        ColumnList = columnsTableDF.iloc[row,:]['ColumnList']
        Name = columnsTableDF.iloc[row,:]['Name']
        InterpolationMethod = columnsTableDF.iloc[row,:]['InterpolationMethod']
        Tag = columnsTableDF.iloc[row,:]['Tag']
        Params = columnsTableDF.iloc[row,:]['Params']
        dictValue[Name] = {'selected_columns': ast.literal_eval(ColumnList), 'interpolation_method': InterpolationMethod,'func_family':ColumnCreator, 'func':ColumnMethod, 'params':ast.literal_eval(Params)} 
    column_creator_dict = OrderedDict(dictValue)
    ca = ColumnAdder(mergeDF)
    df,newColDetails = ca.create_columns(column_creator_dict)
    return df, newColDetails

@app.callback(
                Output("saveColsModalBody","children"),
                Output("saveColsModal","is_open"),
                Output("createcolumnsLoading","children"),
                Input('createColsBtn','n_clicks') ,
                Input("saveColsModalClose", "n_clicks"),
                State('ColumnsTable','data'),
                State('experimentStore','data')
                 )
def createandSaveColumns(n_clicks,closeClicks,columnsTable,storeData):
    if closeClicks > 0 and ctx.triggered_id == "saveColsModalClose":
        return "",False,dash.no_update
    if n_clicks > 0  : 
        df,newColDetails = columnCreation(storeData,mergeDF)
        # Created new column in MergedFile csv
        fileName = MergedFileName
        experimentSetName = storeData["experimentsetname"]
        path = f'{MASTER_FOLDER}/{experimentSetName}/{MERGED_FOLDER}'#
        df.to_csv(os.path.join(path,fileName),index_label = 'DateTime')

        blobOperations.uploadBlob(os.path.join(path,fileName))
        return "Columns Added successfully!", True , ""
    else :
        raise PreventUpdate()


def getGraph(graphname,fig):
    return dcc.Graph(id = graphname,figure = fig,style={'width': '100vh', 'height': '50vh'})


#This should be at page load as well?????
@app.callback( Output('interpolCols','disabled'),Output('interpolCols','options'),Output('missingValuesGraph','children'),
                Output("missingvalueAnalysisLoading","children"),
                Input('createColsBtn','n_clicks'),
                Input('missingValAnalysisBtn','n_clicks') ,
                State('ColumnsTable','data'),
                State('experimentStore','data')
                 )
def missingValueAnalysis(newcolsClick,n_clicks,columnsTable,storeData):
    global columnAddedDF
    if newcolsClick >0 and ctx.triggered_id == 'createColsBtn' :
        return True,interpolateClassOptions, html.Div([ html.Label('') ]) ,""
    if n_clicks > 0  and ctx.triggered_id == 'missingValAnalysisBtn'  : 
        experimentSetName = storeData['experimentsetname']
        path = f'{MASTER_FOLDER}/{experimentSetName}/{MERGED_FOLDER}'#
        try :
            blobOperations.downloadBlob(f'{path}/{MergedFileName}',"")
            columnAddedDF = pd.read_csv(os.path.join(path,MergedFileName) , parse_dates= True,index_col = 'DateTime')
            colList = [col for col in  list(columnAddedDF.columns) if col not in ['AvailableTime','DateTime']]
            me = MissingvalueEDA(columnAddedDF[colList])
            continuousMissingFig = []
            for col in colList:
                fig = me.continuous_missing_distribution(col)
                continuousMissingFig.append(getGraph(f'{col}_continuousMissingValuesPlot',fig))
            fig = me.missing_heatmap()
            missingValuesFig = getGraph('missingValuesPlot',fig)

        except FileNotFoundError :
            print('Merged File Not Found')
        intepolOptions =  listToOptions(colList)
        graphChildren = continuousMissingFig+[missingValuesFig]
        return False, intepolOptions, graphChildren,""
    else :
        raise PreventUpdate()


#This should be at page load as well?????
@app.callback(Output('postmissingValuesGraph','children'),Output('postmissingValuesGraphLoading','children'),
                Input('postmissingValAnalysisBtn','n_clicks') ,
                State('experimentStore','data')
                 )
def getpostmissingvaluenalysis(n_clicks,storeData):
    if n_clicks > 0  : 
        experimentSetName = storeData['experimentsetname']
        path = f'{MASTER_FOLDER}/{experimentSetName}/{MERGED_FOLDER}'#
        try :
            postcolumnAddedDF = pd.read_csv(os.path.join(path,PreprocessedFileName) ,parse_dates= True ,index_col= 0)
            
            colList = [col for col in list(postcolumnAddedDF.columns) if col not in ['AvailableTime','DateTime']]
            me = MissingvalueEDA(postcolumnAddedDF[colList])
            continuousMissingFig = []
            for col in colList:
                fig = me.continuous_missing_distribution(col)
                continuousMissingFig.append(getGraph(f'{col}_postcontinuousMissingValuesPlot',fig))
            fig = me.missing_heatmap()
            missingValuesFig = getGraph('postmissingValuesPlot',fig)

        except FileNotFoundError :
            print('Merged File Not Found')
        intepolOptions =  listToOptions(colList)
        graphChildren = continuousMissingFig+[missingValuesFig]

        return  graphChildren , ""
    else :
        raise PreventUpdate()