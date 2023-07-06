-- =============================================
-- Author: Lokendra Singh Shekhawat
-- Create Date: 16-Jan-2023	
-- Description: This procedure returns a list of error values for a given set of values of ExperimentSet, Experiment, InternalRunID from [dbo].[errorAnalysis] table.
-- =============================================
CREATE PROCEDURE usp_getErrors
-- CREATE PROCEDURE [ProcedureName]
	@InternalRunId BIGINT,
       @ExperimentSet VARCHAR(100),
       @Experiment VARCHAR(50)
											  
AS 
BEGIN 
--returns a list of error values for a given set of (ExperimentSet, Experiment, InternalRunID)
    SET NOCOUNT ON; 

     SELECT Error FROM [dbo].[errorAnalysis]
	where ExperimentSet= @ExperimentSet 
	and Experiment = @Experiment 
	and InternalRunId = @InternalRunId;
     
END
-- Calling above procedure in sql server:
-- EXEC [getErrors] 'DeepMCAggregator', 'experiment_aggregator1', '20221228093602'