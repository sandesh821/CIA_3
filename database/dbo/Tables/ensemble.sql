CREATE TABLE [dbo].[ensemble] (
    [CreatedOn]           DATETIME      DEFAULT (getdate()) NULL,
    [EnsembleName]        VARCHAR (100) NULL,
    [ExperimentSet]       VARCHAR (100) NULL,
    [ExperimentsName]     VARCHAR (200) NULL,
    [EnsembleMethod]      VARCHAR (100) NULL,
    [Params]              VARCHAR (100) NULL,
    [InterpolationMethod] VARCHAR (100) NULL,
    [InternalRunId]       BIGINT        NULL,
    [Actual]              FLOAT (53)    NULL,
    [Prediction]          FLOAT (53)    NULL,
    [AbsError]            FLOAT (53)    NULL,
    [Error]               FLOAT (53)    NULL,
    [DateTime]            DATETIME      NULL
);

