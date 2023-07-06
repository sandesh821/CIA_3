-- =============================================
-- Author:      Astha Agarwal
-- Create Date: December 12, 2022
-- Description: Insert new experiment set
-- =============================================
CREATE PROCEDURE [dbo].[usp_insertExperimentSets]
@ExperimentSet VARCHAR(100),
@EntityType varchar(50)
AS
BEGIN
    -- SET NOCOUNT ON added to prevent extra result sets from
    -- interfering with SELECT statements.
    SET NOCOUNT ON

	IF EXISTS (SELECT 1 FROM dbo.experimentSet WHERE ExperimentSetName = @ExperimentSet AND EntityType = @EntityType)
		SELECT -1
	ELSE
		BEGIN
		-- Insert statements for procedure here
		INSERT INTO dbo.experimentSet(ExperimentSetName,EntityType)
		VALUES(@ExperimentSet,@EntityType)

		SELECT @@IDENTITY
	END
END