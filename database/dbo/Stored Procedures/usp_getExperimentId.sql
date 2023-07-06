-- =============================================
-- Author: Vaibhav Hiwase
-- Create Date: 23-Mar-2023	
-- Description: This procedure returns experiment id for the given experiment name.
-- =============================================

CREATE PROCEDURE usp_getExperimentId
@ExperimentSetName VARCHAR(100)											  
AS 
BEGIN 
    SET NOCOUNT ON; 
    SELECT  distinct ExperimentSetID  FROM [dbo].[experimentSet] 
	WHERE ExperimentSetName = @ExperimentSetName;
END