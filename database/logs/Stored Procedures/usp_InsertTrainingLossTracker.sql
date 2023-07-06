-- =============================================
-- Author: Vaibhav Hiwase
-- Create Date: 16-Jan-2023	
-- Description: This procedure insert values into [logs].[runTrainingLossTracker] table. Values are specified in the procedure parameters.
-- =============================================

CREATE PROCEDURE [logs].[usp_InsertTrainingLossTracker]
-- CREATE PROCEDURE [SchemaName].[Prefix_ProcedureName]
-- Prefix: usp = UserStoredProcedure 

(
@EpochLoss FLOAT(53),
@EpochValLoss FLOAT(53),
@Epoch INT,
@AMLRunId VARCHAR (100),
@InternalModelNumber INT,
@StartDateTime DATETIME,
@EndDateTime DATETIME
)
AS
BEGIN
-- Insert all the passed values into the [logs].[runTrainingLossTracker] table

    INSERT INTO [logs].[runTrainingLossTracker] ([EpochLoss], [EpochValLoss], [Epoch], [AMLRunId], [InternalModelNumber], [StartDateTime], [EndDateTime])
    VALUES (@EpochLoss, @EpochValLoss, @Epoch, @AMLRunId, @InternalModelNumber, @StartDateTime, @EndDateTime)
END

-- Calling above procedure in sql server:
-- EXEC [logs].[usp_InsertTrainingLossTracker] 0.443967431783676, 0.361863404512405, 10, 'c1f9c126-7df8-4825-bc7c-3d943e08f5b2', -1, '2023-01-11 06:23:25.720', '2023-01-11 06:23:26.757'