CREATE TABLE [logs].[clusterDetails] (
    [Id]          INT           IDENTITY (1, 1) NOT NULL,
    [ClusterName] VARCHAR (100) NOT NULL,
    [Cores]       INT           NOT NULL,
    [Ram]         INT           NOT NULL
);

