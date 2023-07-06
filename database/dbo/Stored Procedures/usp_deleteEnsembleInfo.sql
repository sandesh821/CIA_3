CREATE PROCEDURE [dbo].usp_deleteEnsembleInfo @ExperimentSetID int
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON

  DELETE FROM [dbo].[ensembleInfo]
		   WHERE [ExperimentSetID] = @ExperimentSetID
END