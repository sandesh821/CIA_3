-- =============================================
-- Author: Vaibhav Hiwase
-- Create Date: 16-Jan-2023	
-- Description: This procedure takes Experiment and InternalRunId as parameters and use them to get a row from [logs].[runTracker] table.
-- =============================================

CREATE PROCEDURE [logs].[usp_getAMLRunTrackerRow] 
-- CREATE PROCEDURE [SchemaName].[Prefix_ProcedureName]
-- Prefix: usp = UserStoredProcedure 

@Experiment VARCHAR(100),
@InternalRunId BIGINT
AS

BEGIN
-- Get a row that match the parameters

    SELECT * FROM [logs].[runTracker]
    WHERE [logs].[runTracker].[Experiment] = @Experiment
    AND [logs].[runTracker].[InternalRunId] = @InternalRunId
END

-- Calling above procedure in sql server:
-- EXEC [logs].[usp_getAMLRunTrackerRow] 'experiment11_exp2', '20230111054520'