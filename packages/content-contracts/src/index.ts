/** Health contract only. Portfolio/editor contracts are deliberately not implemented. */
export interface HealthResponse {
  schema_version: 1;
  service: "portfolio-api";
  status: "ok" | "unavailable";
}

export function isHealthResponse(value: unknown): value is HealthResponse {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Record<string, unknown>;
  return Object.keys(candidate).length === 3 && candidate.schema_version === 1 && candidate.service === "portfolio-api"
    && (candidate.status === "ok" || candidate.status === "unavailable");
}
