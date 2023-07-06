-- =============================================
-- Author:      Vaibhav Hiwase
-- Create Date: March 15, 2023
-- Description: Get experiment set details
-- =============================================
CREATE PROCEDURE [dbo].[usp_getExperimentSet]
@ExperimentSetID int
AS
BEGIN
    -- SET NOCOUNT ON added to prevent extra result sets from
    -- interfering with SELECT statements.
    SET NOCOUNT ON

    SELECT ExperimentSetID, 
           ExperimentSetName, 
	   EntityType 
    FROM dbo.experimentSet (NOLOCK)
    WHERE ExperimentSetID = @ExperimentSetID

END