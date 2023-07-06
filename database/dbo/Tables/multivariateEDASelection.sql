CREATE TABLE [dbo].[multivariateEDASelection] (
    [ID]                    INT            IDENTITY (1, 1) NOT NULL,
    [ExperimentSetID]       INT            NULL,
    [GraphSelectionDetails] NVARCHAR (MAX) NOT NULL,
    [CreatedBy]             VARCHAR (100)  DEFAULT (suser_sname()) NULL,
    [CreatedOn]             DATETIME       DEFAULT (getdate()) NULL
);

