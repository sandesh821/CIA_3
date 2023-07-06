CREATE TABLE [logs].[statusTracker] (
    [Id]                  INT           IDENTITY (1, 1) NOT NULL,
    [Status]              VARCHAR (100) NULL,
    [TotalEpoch]          INT           NULL,
    [CreatedOn]           DATETIME      CONSTRAINT [DF_statusTracker_CreatedOn] DEFAULT (getdate()) NULL,
    [AMLRunId]            VARCHAR (100) NULL,
    [InternalModelNumber] INT           NULL,
    [N_Trials]            INT           NULL,
    [Trial_Number]        INT           NULL,
    [ChildAMLRunId]       VARCHAR (100) NULL,
    [Horizon]             INT           NULL,
    PRIMARY KEY CLUSTERED ([Id] ASC)
);



