CREATE TABLE [dbo].[experimentSet] (
    [ExperimentSetID]   INT           IDENTITY (1, 1) NOT NULL,
    [ExperimentSetName] VARCHAR (100) NOT NULL,
    [EntityType]        VARCHAR (50)  NOT NULL,
    [CreatedBy]         VARCHAR (50)  DEFAULT ('admin') NULL,
    [CreatedOn]         DATETIME      DEFAULT (getdate()) NULL,
    PRIMARY KEY CLUSTERED ([ExperimentSetID] ASC)
);

