CREATE TABLE [dbo].[transformationFileTimezoneDetails] (
    [ID]              INT            IDENTITY (1, 1) NOT NULL,
    [ExperimentSetID] INT            NULL,
    [TimeZoneDetails] NVARCHAR (MAX) NULL,
    [CreatedBy]       VARCHAR (100)  DEFAULT (suser_sname()) NULL,
    [CreatedOn]       DATETIME       DEFAULT (getdate()) NULL
);

