CREATE PROCEDURE [dbo].[usp_deleteErrorAnalysisData] 
       @ModelName VARCHAR(100), 
       @ExperimentSet VARCHAR(100), 
       @Experiment VARCHAR(100),
	   @InternalRunId BIGINT						  
AS 
BEGIN 
     SET NOCOUNT ON 

	 DELETE FROM dbo.errorAnalysis
	 WHERE ExperimentSet = @ExperimentSet AND Experiment = @Experiment AND InternalRunId = @InternalRunId AND ModelName = @ModelName

END