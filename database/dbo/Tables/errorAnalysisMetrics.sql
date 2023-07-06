CREATE TABLE [dbo].[errorAnalysisMetrics] (
    [CreatedOn]     DATETIME      DEFAULT (getdate()) NULL,
    [ModelName]     VARCHAR (100) NULL,
    [ExperimentSet] VARCHAR (100) NULL,
    [Experiment]    VARCHAR (100) NULL,
    [InternalRunId] BIGINT        NULL,
    [MAE]           FLOAT (53)    NULL,
    [MSE]           FLOAT (53)    NULL,
    [MAPE]          FLOAT (53)    NULL,
    [RMSE]          FLOAT (53)    NULL,
    [nRMSE]         FLOAT (53)    NULL
);

