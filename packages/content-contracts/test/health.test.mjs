import test from 'node:test';
import assert from 'node:assert/strict';
import { isHealthResponse } from '../src/index.ts';

test('accepts ready and unavailable health documents', () => {
  for (const status of ['ok', 'unavailable']) {
    assert.equal(isHealthResponse({schema_version:1,service:'portfolio-api',status}),true);
  }
});
test('rejects invalid, incomplete and future documents', () => {
  for (const value of [null, [], {}, {schema_version:2,service:'portfolio-api',status:'ok'}, {schema_version:1,service:'other',status:'ok'}, {schema_version:1,service:'portfolio-api',status:'ready'}]) {
    assert.equal(isHealthResponse(value),false);
  }
});
test('rejects extra fields consistently with the canonical schema', () => {
  assert.equal(isHealthResponse({schema_version:1,service:'portfolio-api',status:'ok',extra:true}),false);
});
