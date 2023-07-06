CREATE PROCEDURE usp_getCorrectionFactors
(
    @ExperimentSetName VARCHAR(255),
    @ExperimentName VARCHAR(255),
    @Ops VARCHAR(10),
    @ConditionalColumns VARCHAR(255)
)
AS
BEGIN
    SET NOCOUNT ON;

    SELECT ConditionValue, Biascorrectionfactors
    FROM [dbo].[biascorrectionFactors]
    WHERE ExperimentSetName = @ExperimentSetName
        AND ExperimentName = @ExperimentName
        AND Ops = @Ops
        AND ConditionalColumns = @ConditionalColumns
END