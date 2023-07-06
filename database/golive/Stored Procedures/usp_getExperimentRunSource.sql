--EXEC [golive].[usp_getExperimentRunSource] 'solarewbrown','experiment8' 
CREATE PROCEDURE [golive].[usp_getExperimentRunSource]
@ExperimentSet VARchar(100),
@Experiment VARCHAR(100)
AS
BEGIN
	SELECT TOP 1 ExperimentSetId, CreatedSource FROM dbo.scheduledExperimentsList
	WHERE ExperimentSetName = @ExperimentSet
	AND experimenttag = @Experiment
	AND Status != 5
	order by id DESC
END