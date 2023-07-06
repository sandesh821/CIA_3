CREATE PROCEDURE usp_getExperimentsOutputs
	@ExperimentSetName VARCHAR(50),
    @ExperimentNames VARCHAR(100)
AS
BEGIN
    SELECT t.*
    FROM [dbo].[errorAnalysis] t
    WHERE t.Experiment IN (SELECT value FROM STRING_SPLIT(@ExperimentNames, ','))
	AND t.[experimentSet] = @ExperimentSetName
END