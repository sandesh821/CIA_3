-- =============================================
-- Author: Astha
-- Create Date: 19-Apr-2023	
-- Description: This procedure Inserts the Model Drifts Values for data run for dataDrift [dbo].[dataDrift] table.
-- =============================================
CREATE PROCEDURE golive.[usp_InsertTargetDriftAnalysisMetrics]
	@ExperimentSetId INT,
    @TargetDrift varchar(8000)
AS
BEGIN
  INSERT INTO golive.[dataDrift](
			[ExperimentSetId],
            [DriftResponse],
			[Type]
			) 
  VALUES(@ExperimentSetId,
      @TargetDrift,
	  'Target'
	  )
END