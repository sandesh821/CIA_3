-- =============================================
-- Author: Lokendra Singh Shekhawat
-- Create Date: 16-Jan-2023	
-- Description: This procedure returns the latest successfully finished InternalRunID from a given Experiment from [logs].[runTracker] table.
-- =============================================
CREATE PROCEDURE usp_getInternalRunID 
-- CREATE PROCEDURE [ProcedureName]
     
       @RunStatus VARCHAR(30), 
       @Experiment VARCHAR(50)
											  
AS 
BEGIN 
-- Returns the latest InternalRunID from an experiment having RunStatus as "Finished"
    SET NOCOUNT ON; 

     select max(InternalRunID) from [logs].[runTracker]
		where RunStatus = @RunStatus
		and Experiment = @Experiment;
     
END
-- Calling above procedure in sql server:
-- EXEC [getInternalRunID] 'Finished', 'experiment_aggregator1'