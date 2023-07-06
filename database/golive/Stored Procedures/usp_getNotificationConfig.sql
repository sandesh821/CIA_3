
-- =============================================
-- Author:      Astha Agarwal
-- Create Date: March 30, 2023
-- Description: Get Notification Config
-- =============================================
CREATE PROCEDURE [golive].[usp_getNotificationConfig] @ExperimentSetID int
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON

		SELECT
			[notificationConfig]
		FROM golive.NotificationConfig
		WHERE [ExperimentSetID] = @ExperimentSetID
END