-- =============================================
-- Author: Vaibhav Hiwase
-- Create Date: 16-Jan-2023	
-- Description: This stored procedure is used to insert or update a row in the statusTracker table. Values for the row are specified in the procedure parameters.
--              It first checks if the InternalModelNumber parameter is not null before proceeding with the insertion or update.
--              If the InternalModelNumber is not null and the AMLRunId does not already exist, it will insert a new row into the statusTracker table at the beginning of the model training.
--              If the AMLRunId already exists, it will update the Status and TotalEpoch columns for the corresponding AMLRunId and InternalModelNumber.
--              If the InternalModelNumber is not present, then the value of InternalModelNumber should be -1.
-- =============================================

CREATE PROCEDURE [logs].[usp_InsertStatusTracker]
(
    @AMLRunId VARCHAR(100),
    @Status VARCHAR(100),
    @TotalEpoch INT,
    @InternalModelNumber INT,
    @N_Trials INT, 
    @Trial_Number INT, 
    @ChildAMLRunId VARCHAR (100),
    @Horizon INT
)
AS
BEGIN
    -- Check if the InternalModelNumber is not null before inserting a new row
    IF @InternalModelNumber IS NOT NULL
    BEGIN
        -- Insert a new row into the statusTracker table if the AMLRunId does not already exist         
		INSERT INTO [logs].[statusTracker] ([AMLRunId], [Status], [TotalEpoch], [InternalModelNumber],[N_Trials],[Trial_Number],[ChildAMLRunId],[Horizon])
        SELECT @AMLRunId, @Status, @TotalEpoch, @InternalModelNumber, @N_Trials, @Trial_Number, @ChildAMLRunId, @Horizon
        WHERE NOT EXISTS (SELECT 1 FROM [logs].[statusTracker] WHERE [AMLRunId] = @AMLRunId AND [InternalModelNumber] = @InternalModelNumber)
    END
    -- Update the Status, TotalEpoch column for the corresponding AMLRunId when InternalModelNumber is not null     
	UPDATE [logs].[statusTracker]
    SET [Status] = @Status, [TotalEpoch] = @TotalEpoch, [InternalModelNumber] = ISNULL(@InternalModelNumber, [InternalModelNumber]), [N_Trials] = @N_Trials, [Trial_Number] = @Trial_Number, [ChildAMLRunId] = @ChildAMLRunId, [Horizon] = @Horizon
    WHERE [AMLRunId] = @AMLRunId AND [InternalModelNumber] = @InternalModelNumber 
END