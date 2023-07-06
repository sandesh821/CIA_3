
-- =============================================
-- Author:      Astha Agarwal
-- Create Date: March 30, 2023
-- Description: Get data ingestion
-- =============================================
CREATE PROCEDURE [golive].[usp_getDataIngestion] @ExperimentSetID int
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON

		SELECT
			[SourceDataDetails], [DataRefreshDetails], [ApiMapping]
		FROM golive.dataIngestion
		WHERE [ExperimentSetID] = @ExperimentSetID
END