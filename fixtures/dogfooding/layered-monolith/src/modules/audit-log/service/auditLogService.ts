export function normalizeAuditFilters(raw: Record<string, string | undefined>) {
  return {
    actor: raw.actor?.trim(),
    action: raw.action?.trim()
  };
}
