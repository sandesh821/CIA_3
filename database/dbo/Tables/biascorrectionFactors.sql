CREATE TABLE [dbo].[biascorrectionFactors] (
    [ID]                    INT           IDENTITY (1, 1) NOT NULL,
    [ExperimentSetName]     VARCHAR (255) NOT NULL,
    [ExperimentName]        VARCHAR (255) NOT NULL,
    [Ops]                   VARCHAR (255) NOT NULL,
    [ConditionalColumns]    VARCHAR (255) NOT NULL,
    [Biascorrectionfactors] VARCHAR (MAX) NOT NULL,
    [ConditionValue]        VARCHAR (255) NOT NULL
);

