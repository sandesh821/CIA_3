CREATE TABLE [golive].[modelDeployment] (
    [ID]                      INT            IDENTITY (1, 1) NOT NULL,
    [ExperimentSetID]         INT            NULL,
    [deploymentManagerConfig] VARCHAR (1000) NULL,
    [CreatedBy]               VARCHAR (100)  DEFAULT (suser_sname()) NULL,
    [CreatedOn]               DATETIME       DEFAULT (getdate()) NULL
);

