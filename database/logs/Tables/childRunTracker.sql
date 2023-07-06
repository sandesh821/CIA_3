CREATE TABLE [logs].[childRunTracker] (
    [Id]            INT           IDENTITY (1, 1) NOT NULL,
    [Experiment]    VARCHAR (100) NOT NULL,
    [ModelName]     VARCHAR (100) NOT NULL,
    [InternalRunId] VARCHAR (100) NOT NULL,
    [ChildAMLRunId] VARCHAR (100) NULL,
    [CreatedOn]     DATETIME      CONSTRAINT [DF_childRunTracker_CreatedOn] DEFAULT (getdate()) NULL,
    [StartDateTime] DATETIME      NULL,
    [EndDateTime]   DATETIME      NULL
);



