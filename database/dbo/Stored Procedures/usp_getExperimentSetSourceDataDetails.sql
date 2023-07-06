-- =============================================
-- Author:      Astha Agarwal
-- Create Date: January 03, 2023
-- Description: Get experiment set source data details
-- =============================================
CREATE PROCEDURE [dbo].[usp_getExperimentSetSourceDataDetails] @ExperimentSetID int
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON

		SELECT
			[FileType] ,
			[AccountName] ,
			[ContainerName] ,
			[BlobName] ,
			[Tags] AS Tag,
			[FileIdentifier]
		FROM [dbo].[experimentSetSourceDataDetails]
		WHERE [ExperimentSetID] = @ExperimentSetID
		order by [RowID]
END