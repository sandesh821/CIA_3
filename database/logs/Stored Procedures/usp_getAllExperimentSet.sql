-- =============================================
-- Author: Lokendra Singh Shekhawat
-- Create Date: 16-Jan-2023	
-- Description: This procedure returns all the distinct values of ExperimentSet from [logs].[runTracker] table.
-- =============================================
CREATE PROCEDURE usp_getAllExperimentSet
 -- CREATE PROCEDURE [ProcedureName]    											  
AS 
BEGIN 
-- Returns all the experimentSets' name
    SET NOCOUNT ON; 

     SELECT distinct ExperimentSet FROM [logs].[runTracker];
     
END
-- Calling above procedure in sql server:
-- EXEC [getAllExperimentSet] 