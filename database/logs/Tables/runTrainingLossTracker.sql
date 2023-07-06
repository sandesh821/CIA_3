CREATE TABLE [logs].[runTrainingLossTracker] (
    [Id]            		INT             IDENTITY (1, 1) NOT NULL,
    [CreatedOn]     		DATETIME        CONSTRAINT [DF_runTrainingLossTracker_CreatedOn] DEFAULT (getdate()) NULL,
    [EpochLoss]      		FLOAT(53)       NULL,
    [EpochValLoss]      	FLOAT(53)       NULL,
    [Epoch]      		    INT             NULL,
    [AMLRunId]              VARCHAR (100)   NULL,
    [InternalModelNumber]   INT             NULL,
    [StartDateTime] 		DATETIME        NULL,
    [EndDateTime]   		DATETIME        NULL,
);
