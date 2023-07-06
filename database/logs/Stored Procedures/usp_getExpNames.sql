-- =============================================
-- Author: Lokendra Singh Shekhawat
-- Create Date: 16-Jan-2023	
-- Description: This procedure returns all the successfully finished Experiment values from a given ExperimentSet from [logs].[runTracker] table.
-- =============================================

CREATE PROCEDURE usp_getExpNames 
-- CREATE PROCEDURE [ProcedureName]

       @RunStatus VARCHAR(30), 
	@ExperimentSet VARCHAR(100)
											  
AS 
BEGIN 

-- Returns all the experiments from a given ExperimentSet having RunStatus as "Finished"
    SET NOCOUNT ON; 

     SELECT  distinct Experiment  FROM [logs].[runTracker] 
	where RunStatus = @RunStatus
	and ExperimentSet = @ExperimentSet;
     
END
-- Calling above procedure in sql server:
-- EXEC [getExpNames] 'Finished', 'DeepMCAggregator'
