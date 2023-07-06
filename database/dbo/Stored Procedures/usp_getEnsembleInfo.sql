CREATE PROCEDURE [dbo].[usp_getEnsembleInfo] @ExperimentSetID int
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON

		SELECT
			EnsembleDetails
		FROM [dbo].[ensembleInfo]
		WHERE [ExperimentSetID] = @ExperimentSetID
END