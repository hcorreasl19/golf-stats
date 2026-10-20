import {test} from 'node:test';
import assert from 'node:assert/strict';
import {safeNext} from '../lib/redirect-path';
test('auth callback keeps local destinations and rejects external/control-character destinations',()=>{
 assert.equal(safeNext('/conta?modo=redefinir'),'/conta?modo=redefinir');
 for(const path of ['https://example.test','//example.test','/\n/example.test','/\\example.test','javascript:alert(1)',null]) assert.equal(safeNext(path),'/partidas');
});
