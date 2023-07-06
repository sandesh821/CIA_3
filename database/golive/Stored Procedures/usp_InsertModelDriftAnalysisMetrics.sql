-- =============================================
-- Author: Sneha R More
-- Create Date: 19-Apr-2023	
-- Description: This procedure Inserts the Model Drifts Values for data run for dataDrift [dbo].[dataDrift] table.
-- =============================================

CREATE PROCEDURE golive.[usp_InsertModelDriftAnalysisMetrics]
@ExperimentSetId INT,
          @ModelDrift varchar(8000)
AS
BEGIN
  Insert into golive.[dataDrift](
			[ExperimentSetId],
            [DriftResponse],
			[Type]
			) 
  values(@ExperimentSetId,
      @ModelDrift,
	  'Model'
	  )

END