-- =============================================
-- Author: Lokendra Singh Shekhawat
-- Create Date: 16-Jan-2023	
-- Description: This procedure returns the latest successfully finished InternalRunID and respective ExperimentSet from a given Experiment from [logs].[runTracker] table.
-- =============================================
CREATE PROCEDURE usp_getExperimentSetAndInternalRunid
-- CREATE PROCEDURE [ProcedureName]
       @RunStatus VARCHAR(30), 
       @Experiment VARCHAR(100)
											  
AS 
BEGIN 
--returns the latest successfully finished InternalRunID and respective ExperimentSet from a given Experiment
    SET NOCOUNT ON; 

    SELECT MAX(InternalRunID) as InternalRunID, ExperimentSet
	FROM [logs].[runTracker]
	WHERE Experiment = @Experiment
	and RunStatus = @RunStatus
	GROUP BY ExperimentSet;
     
END
-- Calling above procedure in sql server:
-- EXEC [getExperimentSetAndInternalRunid] 'experiment_aggregator1', 'Finished'
