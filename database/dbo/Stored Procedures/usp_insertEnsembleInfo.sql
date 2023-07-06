CREATE PROCEDURE [dbo].usp_insertEnsembleInfo 
@ExperimentSetID int,
@EnsembleDetails NVARCHAR(MAX)
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON
  BEGIN
    INSERT INTO [dbo].[ensembleInfo]
           (
			ExperimentSetID,
			EnsembleDetails)
     VALUES
           (@ExperimentSetID
		   , @EnsembleDetails )
  END
END