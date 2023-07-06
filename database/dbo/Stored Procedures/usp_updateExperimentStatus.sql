-- =============================================
-- Author:      Astha Agarwal
-- Create Date: January 23, 2023
-- Description: Update Experiment status to running
-- =============================================
CREATE PROCEDURE [dbo].[usp_updateExperimentStatus] @ExperimentSetName varchar(100), @ExperimentTag Varchar(100), @Status INT NULL
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON

		UPDATE [dbo].[scheduledExperimentsList] 
		SET [Status] = ISNULL(@Status,1)
		WHERE ExperimentSetName = @ExperimentSetName
		AND experimenttag = @ExperimentTag
		AND [Status] != 5 -- Dont update status for already completed pipelines
END