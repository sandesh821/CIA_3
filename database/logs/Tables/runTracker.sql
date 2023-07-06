CREATE TABLE [logs].[runTracker] (
    [Id]            INT           IDENTITY (1, 1) NOT NULL,
    [ExperimentSet] VARCHAR (100) NOT NULL,
    [Experiment]    VARCHAR (100) NOT NULL,
    [InternalRunID] VARCHAR (100) NOT NULL,
    [AMLRunId]      VARCHAR (100) NOT NULL,
    [RunStatus]     VARCHAR (50)  NULL,
    [CreatedBy]     VARCHAR (50)  CONSTRAINT [DF_runTracker_CreatedBy] DEFAULT ('admin') NULL,
    [CreatedOn]     DATETIME      CONSTRAINT [DF_runTracker_CreatedOn] DEFAULT (getdate()) NULL,
    [StartDateTime] DATETIME      NULL,
    [EndDateTime]   DATETIME      NULL,
    CONSTRAINT [PK_RunTracker_ExperimentSetExperimentInternalRunId] PRIMARY KEY CLUSTERED ([ExperimentSet] ASC, [Experiment] ASC, [AMLRunId] ASC)
);



