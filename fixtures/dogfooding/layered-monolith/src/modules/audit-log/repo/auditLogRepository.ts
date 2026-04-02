export function buildAuditLogQuery(filters: { actor?: string; action?: string }) {
  return {
    where: filters
  };
}
