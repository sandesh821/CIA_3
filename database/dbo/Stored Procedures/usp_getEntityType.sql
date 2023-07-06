-- =============================================
-- Author:      Hariprasad
-- Create Date: Feb 15, 2023
-- Description: Get entity type
-- =============================================
CREATE PROCEDURE [dbo].[usp_getEntityType] @ExperimentSetID int
AS
BEGIN
  SET NOCOUNT ON

		SELECT
			[EntityType] 
		FROM [dbo].[experimentSet]
		WHERE [ExperimentSetID] = @ExperimentSetID
END