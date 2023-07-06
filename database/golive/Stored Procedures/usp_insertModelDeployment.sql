
-- =============================================
-- Author:      Astha Agarwal
-- Create Date: March 30, 2023
-- Description: Insert go live event configuration details
-- =============================================
CREATE PROCEDURE [golive].usp_insertModelDeployment 
@ExperimentSetID int,
@deploymentManagerConfig VARCHAR(2000)
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON
  BEGIN
    INSERT INTO golive.[modelDeployment]
           (
			ExperimentSetID,
			[deploymentManagerConfig]
			)
     VALUES
           (@ExperimentSetID
		   , @deploymentManagerConfig
		 )
  END
END