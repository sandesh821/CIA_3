CREATE TABLE [dbo].[errorAnalysis] (
    [CreatedOn]      DATETIME      DEFAULT (getdate()) NULL,
    [ModelName]      VARCHAR (100) NULL,
    [ExperimentSet]  VARCHAR (100) NULL,
    [Experiment]     VARCHAR (100) NULL,
    [InternalRunId]  BIGINT        NULL,
    [Actual]         FLOAT (53)    NULL,
    [Prediction]     FLOAT (53)    NULL,
    [AbsError]       FLOAT (53)    NULL,
    [Error]          FLOAT (53)    NULL,
    [DateTime]       DATETIME      NULL,
    [Quantile]       VARCHAR (200) NULL,
    [BiasCorrection] VARCHAR (255) NULL
);


