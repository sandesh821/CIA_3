
-- =============================================
-- Author:      Astha Agarwal
-- Create Date: March 28, 2023
-- Description: Delete notification config
-- =============================================
CREATE PROCEDURE [golive].[usp_deleteNotificationConfig] @ExperimentSetID int
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON

		DELETE
		FROM [golive].[NotificationConfig]
		WHERE [ExperimentSetID] = @ExperimentSetID
END