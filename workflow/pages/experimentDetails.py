#Copyright (c) Microsoft. All rights reserved.

### Import Packages ###
from dash import dash_table
from dash import Dash
from dash import dcc ,html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd

### Import Dash Instance ###
from workflow.main import app
from utilities.azure.blobOperations import getBlobURL
from utilities.azure.azuremlOperations import *
from workflow.common import getdata
from workflow.common.common import getLoadingElement
from workflow.common.config import *

#=========================================CONFIGS======================================================
gridColumns = ["experimenttag","algorithm" ,"ForecastHorizon" , "LookBack", "InternalRunID", "RunStatus"]
outputFolder = 'outputs'
scoreFolder = "scores"
amlcontainer = getAMLContainer()
standardFileMap = {
    "configuration" : "{}.yaml",
    "codeversioninfo" : "codeversiondetails.json",
    "mergeddata" : "data.csv",
    "deepmc_mergeddata" : "deepmc_data.csv",
    "validationmetricfile" : "result_{}.csv",
    "validationresultsdata" : "{}_valResults.csv",
    "hyperparameters" : "params.json",
    "scoringmetricfile" : "eval_metrics.csv",
    "scoringresultsdata" : "{}_valResults.csv"
}

masterData = pd.DataFrame(columns=gridColumns)
#======================================================================================================

#==================================Functions to generate Paths=========================================
def generateAzureBlobLink(linktype,fileName,experimentRow,level2Folder="sourcedata",index=None):
    strAccountName = None
    if linktype == "other":
        if index is not None:
            strAccountName = experimentRow[fileName+"AccountName"].split(",")[index]
            container = experimentRow[fileName+"ContainerName"].split(",")[index]
            path = experimentRow[fileName+"BlobName"].split(",")[index]
        else:
            strAccountName = experimentRow[fileName+"AccountName"]
            container = experimentRow[fileName+"ContainerName"]
            path = experimentRow[fileName+"BlobName"]
    elif linktype == "workflow":
        strAccountName = None
        container = MASTERCONTAINER
        if fileName == MergedFileName:
            folder = MERGED_FOLDER
        path = f'{MASTER_FOLDER}/{experimentRow["ExperimentSetName"]}/{folder}/{fileName}'
    else:
        container = amlcontainer
        baseFolderPath = outputFolder+"/"+experimentRow["ExperimentSetName"]+"/"+experimentRow["experimenttag"]+"/"+str(experimentRow["InternalRunID"])+"/"
        if linktype == "outputs":
            path = baseFolderPath+fileName
        elif linktype == "outputs_level1":
            path = baseFolderPath + experimentRow["algorithm"]+"/"+fileName
        elif linktype == "outputs_level2":
            path = baseFolderPath + experimentRow["algorithm"]+"/"+level2Folder+"/"+fileName
        elif linktype == "scores_level1":
            baseFolderPath = scoreFolder+"/"+experimentRow["ExperimentSetName"]+"/"+experimentRow["experimenttag"]+"/"+str(experimentRow["InternalRunID"])+"/"
            path = baseFolderPath + experimentRow["algorithm"]+"/"+fileName
        elif linktype == "scores_level2":
            level2Folder = "erroranalysis"
            baseFolderPath = scoreFolder+"/"+experimentRow["ExperimentSetName"]+"/"+experimentRow["experimenttag"]+"/"+str(experimentRow["InternalRunID"])+"/"
            path = baseFolderPath + experimentRow["algorithm"]+"/"+level2Folder+"/"+fileName

    url = getBlobURL(container, path, strAccountName)
    return url

def generateLogHyperlinks(logDict):
    if(logDict is not None):
        logsList = []
        for logType in logDict:
            link = logDict[logType]
            hyperlinkObj = getHyperLink(logType.replace("logs/azureml/",""),link)
            logsList.append(hyperlinkObj)
            logsList.append(" ")
        return logsList
    else:
        return "No logs found"
#======================================================================================================

#==================================Functions to generate HTML Objects===================================
# Define HTML objects
def getTable(id_name):
    return dash_table.DataTable([], [{"name": i, "id": i} for i in gridColumns], id=id_name, style_table={'overflow-y':'scroll','height':300},)

def getListItem(header,content):
    return html.Li(
            [
                html.Span(header, className="listHeaders"),
                html.Span(content)
            ]
            , className="listItem"
        )

def getHyperLink(text,link):
    if text:
        text = text.replace("'","")
        return html.A(
            children = [text],
            href = link
        )

def getHyperLinkFromObj(experimentName,field,linktype,masterData,text=None,index=None):
    obj = masterData[masterData["experimenttag"] == experimentName]
    objDict = obj.to_dict(orient='records')[0]
    if linktype == "other":
        if index is not None:
            fieldVal = objDict[field+"BlobName"].split(",")[index]
            link = generateAzureBlobLink(linktype,field,objDict,None,index)
        else:
            fieldVal = objDict[field+"BlobName"]
            link = generateAzureBlobLink(linktype,field,objDict)
        text = fieldVal
        fileName = fieldVal
        
    elif linktype == "workflow":
        link = generateAzureBlobLink(linktype,field,objDict)
    else:
        if text is None:
            fieldVal = objDict[field]
            text = fieldVal
            fileName = fieldVal
        else:
            key = text.replace(" ","").lower()
            
            if("DeepMC" == objDict["algorithm"]):
                if "Merged" in text:
                    key = "deepmc_mergeddata"
            fileName = standardFileMap.get(key)
            
            if key == "configuration":
                fileName = fileName.replace("{}",experimentName)
            elif key == "validationresultsdata" or key == "validationmetricfile" or key == "scoringresultsdata":
                fileName = fileName.replace("{}",objDict["algorithm"])

        if("DeepMC" == objDict["algorithm"]):
            if("Params" in text or field == "algorithm"):
                fileName = ""
        elif field == "algorithm":
            fileName = fileName+ ".pkl"

        link = generateAzureBlobLink(linktype,fileName,objDict)
    return getHyperLink(text,link)

def getAMLEnvironmentVersion(algo,property):
    algo = algo.values[0]
    if algo == "DeepMC":
        env = "deepmcFrameworkEnvironment"
    else:
        env = "frameworkEnvironment"
    if property == "version":
        return getEnvironmentVersion(env)
    elif property == "name":
        return env
    else:
        return getEnvironmentDetails(env)

def generateListofLinks(experimentName,field,linktype,masterData):
    obj = masterData[masterData["experimenttag"] == experimentName]
    objDict = obj.to_dict(orient='records')[0]
    fileList = objDict[field+"BlobName"]
    lsHyperlink=[]
    index = 0
    while index < len(fileList.split(",")):
        lsHyperlink.append("[")
        lsHyperlink.append(getHyperLinkFromObj(experimentName,field,linktype,masterData,None,index))
        lsHyperlink.append("] ")
        index = index + 1
    return lsHyperlink

def getDataForSection(experimentName,sectionName, masterData):
    obj = []
    if sectionName == "config":
        # 1. Algorithm
        # 2. Past covariates
        # 3. Future covariates
        # 4. Tags
        # 5. Configuration file reference link
        # 6. Pipeline (reference link to pipeline)
        obj = [
            html.Div(
                html.Ul(
                    children=[
                        getListItem("Algorithm: ", masterData[masterData["experimenttag"] == experimentName]["algorithm"]) ,
                        getListItem("Past Covariates: " , masterData[masterData["experimenttag"] == experimentName]["PastCovariates"].values[0][1:-1]),
                        getListItem("Future Covariates: " , masterData[masterData["experimenttag"] == experimentName]["FutureCovariates"].values[0][1:-1]),
                        getListItem("Entity: " , masterData[masterData["experimenttag"] == experimentName]["Entity"].values[0]),
                        getListItem("Configuration YAML: " , getHyperLinkFromObj(experimentName,"","outputs",masterData,"Configuration"))
                    ],
                    className="left"
                ),
                className="leftDiv"
            ),
            html.Div(
                html.Ul(
                    children=[
                        getListItem("Training Start: " , masterData[masterData["experimenttag"] == experimentName]["TrainStart"]),
                        getListItem("Training End: " , masterData[masterData["experimenttag"] == experimentName]["TrainEnd"]),
                        getListItem("Validation Start: " , masterData[masterData["experimenttag"] == experimentName]["ValStart"]),
                        getListItem("Validation End: " , masterData[masterData["experimenttag"] == experimentName]["ValEnd"]),
                        getListItem("Test Start: " , masterData[masterData["experimenttag"] == experimentName]["TestStart"]),
                        getListItem("Test End: " , masterData[masterData["experimenttag"] == experimentName]["TestEnd"])
                    ],
                    className="left"
                ),
                className="rightDiv"
            )
            
        ]
    elif sectionName == "data":
        obj = [
            html.Div(
                html.Ul(
                    children=[
                        getListItem("Source Files (Past Covariates): " , generateListofLinks(experimentName,"PastCovariates","other",masterData)),
                        getListItem("Source Files (Future Covariates): " , generateListofLinks(experimentName,"FutureCovariates","other",masterData)),
                        getListItem("Source Files (Entity): " , generateListofLinks(experimentName,"Entity","other",masterData)),
                        getListItem("Merged and cleaned file: " , getHyperLinkFromObj(experimentName,MergedFileName,"workflow",masterData,"Merged Data"))
                    ],
                    className="left"
                ),
                className="leftDiv"
            )
            
        ]
    elif sectionName == "code":
        obj = [
            html.Div(
                html.Ul(
                    children=[
                        getListItem("Detailed code version details: " , getHyperLinkFromObj(experimentName,"","outputs",masterData,"Code Version Info")),
                        getListItem("Pipeline reference (Framework Run ID): " , masterData[masterData["experimenttag"] == experimentName]["InternalRunID"]),
                        getListItem("AML Pipeline Run ID: " , masterData[masterData["experimenttag"] == experimentName]["AMLRunId"]),
                        getListItem("Pipeline logs: " , generateLogHyperlinks(getAMLPipelineLogs(masterData[masterData["experimenttag"] == experimentName].iloc[0]["AMLRunId"])))
                    ],
                    className="left"
                ),
                className="leftDiv"
            )
        ]
    elif sectionName == "env":
        obj = [
            html.Div(
                html.Ul(
                    children=[
                        getListItem("Python version: " , pythonVersion), 
                        getListItem("AML Environment: " , getAMLEnvironmentVersion(masterData[masterData["experimenttag"] == experimentName]["algorithm"], "name")), 
                        getListItem("AML Environment Image: " , getHyperLink("Environment",getAMLEnvironmentVersion(masterData[masterData["experimenttag"] == experimentName]["algorithm"], "image"))), 
                        getListItem("Environment version: " , getAMLEnvironmentVersion(masterData[masterData["experimenttag"] == experimentName]["algorithm"], "version"))
                    ],
                    className="left"
                ),
                className="leftDiv"
            )
        ]
    elif sectionName == "training":
        obj = [
            html.Div(
                html.Ul(
                    children=[
                        getListItem("Model: " , getHyperLinkFromObj(experimentName,"algorithm","outputs_level1",masterData)),
                        getListItem("Hyper Parameters: " , getHyperLinkFromObj(experimentName,"algorithm","outputs_level1",masterData)),
                        getListItem("Validation Metric: " , getHyperLinkFromObj(experimentName,"","outputs",masterData,"Validation Metric File")),
                        getListItem("Validation results: " , getHyperLinkFromObj(experimentName,"","outputs_level1",masterData,"Validation Results Data")),
                        getListItem("Experiment Tags: " , getExperimentTags(masterData[masterData["experimenttag"] == experimentName].iloc[0]["ExperimentSetName"],masterData[masterData["experimenttag"] == experimentName].iloc[0]["AMLRunId"]))
                    ],
                    className="left"
                ),
                className="leftDiv"
            )
        ]
    elif sectionName == "score":
        obj = [
            html.Div(
                [
                    html.Ul(
                        children=[
                            getListItem("Scoring Metric: " , getHyperLinkFromObj(experimentName,"","scores_level2",masterData,"Scoring Metric File")),
                            getListItem("Scoring results: " , getHyperLinkFromObj(experimentName,"","scores_level1",masterData,"Scoring Results Data"))
                        ],
                        className="left"
                    )
                ],
                className="leftDiv"
            ),
            html.Div(
                [
                    html.Button("Error Analysis Dashboard", disabled=True, id="errorAnalysisButtonProvenance") #TODO: To be implemented
                ],
                className="leftDiv"
            )
        ]
    return obj

def getSectionHTML(experimentName, internalRunID, sectionName, header, masterData):
    return html.Section(
            children = [
                html.Div(html.H6(header), className="headerDiv"),
                html.Div(
                    getDataForSection(experimentName,sectionName, masterData),
                    id= experimentName+"_"+ str(internalRunID) +"_" + sectionName
                )
            ],
            id = experimentName+"_" + sectionName + "_wrapper",
            className="detailSection"
    )  

def prepareDetailedHTML(experimentName, internalRunID, masterData, Status):
    print("prepareDetailedHTML invoked")
    elements =  [
        getSectionHTML(experimentName, internalRunID,"config","Configuration Details", masterData),
        html.Div(className = "clear"),
        getSectionHTML(experimentName, internalRunID,"data","Data Version Details",masterData),
        html.Div(className = "clear")
    ]
    if Status not in ["To be executed"]:
        elements = elements + [getSectionHTML(experimentName, internalRunID,"code","Code Version Details", masterData),
        html.Div(className = "clear"),
        getSectionHTML(experimentName, internalRunID,"env","Environment Details", masterData),
        html.Div(className = "clear")]
    if Status not in ["To be executed","Failed","Started","Running","Cancelled"]:
        elements = elements + [getSectionHTML(experimentName, internalRunID,"training","Training and Model Details", masterData),
            html.Div(className = "clear")]
    if Status in ["Batch Scoring Finished"]:
        elements = elements + [getSectionHTML(experimentName, internalRunID,"score","Batch scoring Details", masterData)]
    return elements
#========================================================================================================

### Experiment Details Layout and Callback ###
layout = html.Div(
    children=[
        html.H3(
            children='Experiment Details',
            className="pageHeader"
        ),
        html.H6("" , id="pageHeader"),
        html.Div(
            id = "experimentListTable",
            children= [
                getTable("experimentList"),
                html.Div(
                    id = "detailedSection",
                    children=[
                        html.Div(
                                id="detailDiv",
                                className="detailsDiv"
                            )
                    ]
                )
            ]
        ),
        dcc.Store(id='experimentDetailsStore', storage_type='session'),
        getLoadingElement("experimentDetailsLoading"),
        html.Link(
            rel='stylesheet',
            href='/static/provenancestylesheet.css?v=10'
        )        
    ]
)

# On page load
@app.callback([Output('experimentDetailsStore','data'), Output("pageHeader","children"), Output("experimentList","data")],
              Input('page-content','children'),
              [State("newExperiment","data"),State("existingExperiment","data")],
              prevent_initial_call=False)
def render_content(inpt1,data1,data2):
    # Load experiment set id from session and save it in master store
    if data1 is not None:
        data = data1
    elif data2 is not None:
        data = data2
    masterData = getdata.getAllScheduledExperiments(data)
    data["masterData"] = masterData
    return [data,"Experiment Set: " + data["experimentsetname"],masterData]

# Define all callbacks
@app.callback(
    Output('detailDiv','children'),Output("experimentDetailsLoadingOutput","children"),
    [Input("experimentList",'active_cell')],
    State('experimentDetailsStore','data')
)
def renderExperimentDetails(cell,experimentDetailsStore):
    print("Loading provenance")
    if "masterData" in experimentDetailsStore.keys():
        masterData = experimentDetailsStore["masterData"]
    masterData = pd.DataFrame(masterData)
    masterData = masterData.filter(items = [cell["row"]], axis=0)
    masterData.reset_index(inplace=True)
    return prepareDetailedHTML(masterData.iloc[0]["experimenttag"],masterData.iloc[0]["InternalRunID"],masterData,masterData.iloc[0]["RunStatus"]), ""