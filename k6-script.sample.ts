import { ClauseGuardAPIClient } from "./clauseGuardAPI.ts";

const baseUrl = "http://127.0.0.1:8000";
const clauseGuardAPIClient = new ClauseGuardAPIClient({ baseUrl });

export default function () {
  let bodyUploadDocumentApiV1DocumentsPost,
    documentId,
    extractionRequest,
    extractionId,
    askRequest;

  /**
   * Health check endpoint
   */

  const healthCheckApiV1HealthGetResponseData =
    clauseGuardAPIClient.healthCheckApiV1HealthGet();

  /**
   * Upload contract PDF for ingestion
   */
  bodyUploadDocumentApiV1DocumentsPost = {
    file: "deserted",
  };

  const uploadDocumentApiV1DocumentsPostResponseData =
    clauseGuardAPIClient.uploadDocumentApiV1DocumentsPost(
      bodyUploadDocumentApiV1DocumentsPost,
    );

  /**
   * Get document ingestion status and metadata
   */
  documentId = "tenderly";

  const getDocumentApiV1DocumentsDocumentIdGetResponseData =
    clauseGuardAPIClient.getDocumentApiV1DocumentsDocumentIdGet(documentId);

  /**
   * Extract structured clauses from contract
   */
  extractionRequest = {
    document_id: "certification",
    clause_types: [],
    prompt_version: "during",
  };

  const extractClausesApiV1ExtractPostResponseData =
    clauseGuardAPIClient.extractClausesApiV1ExtractPost(extractionRequest);

  /**
   * Get extraction result by ID
   */
  extractionId = "rosin";

  const getExtractionApiV1ExtractExtractionIdGetResponseData =
    clauseGuardAPIClient.getExtractionApiV1ExtractExtractionIdGet(extractionId);

  /**
   * Ask a grounded question about a contract (Server-Sent Events streaming)
   */
  askRequest = {
    document_id: "clearly",
    question: "chatter",
  };

  const askQuestionApiV1AskPostResponseData =
    clauseGuardAPIClient.askQuestionApiV1AskPost(askRequest);
}
