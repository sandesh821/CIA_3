CREATE PROCEDURE [golive].[usp_getScheduledExperimentNameForRetraining]
@ExperimentSetID int,
@ExperimentTag VARCHAR(100)
AS
BEGIN
	SELECT TOP 1 * FROM dbo.scheduledExperimentsList
	WHERE ExperimentSetID = @ExperimentSetID
	AND experimenttag = @ExperimentTag
	order by id ASC
END