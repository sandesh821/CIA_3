-- =============================================
-- Author: Lokendra Singh Shekhawat
-- Create Date: 16-Jan-2023	
-- Description: This procedure returns all the distinct values of Experiment from [logs].[runTracker] table.
-- =============================================

CREATE PROCEDURE usp_getAllExperiment 
-- CREATE PROCEDURE [ProcedureName]


AS 
BEGIN 
-- Returns all the experiments' name

    SET NOCOUNT ON; 

     SELECT  DISTINCT Experiment
                FROM [logs].[runTracker]
     
END
-- Calling above procedure in sql server:
-- EXEC [get_expList] 

