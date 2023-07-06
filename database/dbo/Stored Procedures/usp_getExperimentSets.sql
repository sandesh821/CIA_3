-- =============================================
-- Author:      Astha Agarwal
-- Create Date: December 12, 2022
-- Description: Get list of experiment sets
-- =============================================
CREATE PROCEDURE [dbo].[usp_getExperimentSets]
@EntityType varchar(50)
AS
BEGIN
    -- SET NOCOUNT ON added to prevent extra result sets from
    -- interfering with SELECT statements.
    SET NOCOUNT ON

    SELECT ExperimentSetID, 
		   ExperimentSetName 
	FROM dbo.experimentSet (NOLOCK)
	WHERE EntityType = @EntityType

END