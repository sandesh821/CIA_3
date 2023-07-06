-- =============================================
-- Author:      Astha Agarwal
-- Create Date: March 20, 2023
-- Description: Get Top 3 models by RMSE
-- 
-- =============================================
CREATE PROCEDURE [dbo].[usp_getTopModels] 
    @ExperimentSetID int
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT TOP 3 Experiment, InternalRunId, ModelName, MAE, MSE, MAPE,RMSE
    FROM (Select DISTINCT experimentset,experiment,ModelName,
	FIRST_VALUE(InternalRunId) OVER(PARTITION BY experimentset,experiment,ModelName ORDER BY InternalRunId DESC) InternalRunId,
	FIRST_VALUE(MAE) OVER(PARTITION BY experimentset,experiment,ModelName ORDER BY InternalRunId DESC) MAE,
	FIRST_VALUE(MSE) OVER(PARTITION BY experimentset,experiment,ModelName ORDER BY InternalRunId DESC) MSE,
	FIRST_VALUE(MAPE) OVER(PARTITION BY experimentset,experiment,ModelName ORDER BY InternalRunId DESC) MAPE,
	FIRST_VALUE(RMSE) OVER(PARTITION BY experimentset,experiment,ModelName ORDER BY InternalRunId DESC) RMSE
from [dbo].[errorAnalysisMetrics])EAM
	INNER JOIN [dbo].[experimentSet] ES
	ON ES.ExperimentSetName = EAM.ExperimentSet
    WHERE ES.[ExperimentSetID] = @ExperimentSetID
    ORDER BY CONVERT(FLOAT,RMSE) ASC --CONVERT(INT,REPLACE(experiment,'experiment','')) DESC   --
END