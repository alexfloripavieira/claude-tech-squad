import test from "node:test";
import assert from "node:assert/strict";

import { normalizeAuditFilters } from "../src/modules/audit-log/service/auditLogService";

test("normalize audit filters trims string input", () => {
  assert.deepEqual(normalizeAuditFilters({ actor: " alice ", action: " LOGIN " }), {
    actor: "alice",
    action: "LOGIN"
  });
});
