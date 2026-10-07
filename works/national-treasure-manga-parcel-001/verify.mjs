import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';

function fail(message) { throw new Error(message); }
function sha256(bytes) { return createHash('sha256').update(bytes).digest('hex'); }

function canonical(value) {
  if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
  if (value && typeof value === 'object') {
    return '{' + Object.keys(value).sort().map((k) => JSON.stringify(k) + ':' + canonical(value[k])).join(',') + '}';
  }
  return JSON.stringify(value);
}

function pngDimensions(bytes) {
  if (bytes.subarray(0, 8).toString('hex') !== '89504e470d0a1a0a') fail('SOURCE_NOT_PNG');
  if (bytes.subarray(12, 16).toString('ascii') !== 'IHDR') fail('PNG_IHDR_MISSING');
  return { width: bytes.readUInt32BE(16), height: bytes.readUInt32BE(20) };
}

const [manifestPath, sourcePath, relatteSpecPath] = process.argv.slice(2);
if (!manifestPath || !sourcePath || !relatteSpecPath) {
  fail('usage: node verify.mjs parcel.json source.png relatte-opaque-organ-spec.json');
}

const manifest = JSON.parse(await readFile(manifestPath, 'utf8'));
const source = await readFile(sourcePath);
const relatte = JSON.parse(await readFile(relatteSpecPath, 'utf8'));

if (manifest.schema !== 'lemonpress.manga-parcel/v0') fail('BAD_SCHEMA');

const sourceHash = sha256(source);
if (sourceHash !== manifest.source.sha256) fail('SOURCE_SHA256_MISMATCH');
if (source.length !== manifest.source.byte_length) fail('SOURCE_BYTE_LENGTH_MISMATCH');

const dimensions = pngDimensions(source);
if (dimensions.width !== manifest.source.pixel_dimensions.width ||
    dimensions.height !== manifest.source.pixel_dimensions.height) {
  fail('SOURCE_DIMENSIONS_MISMATCH');
}

const planHash = sha256(Buffer.from(canonical(manifest.issue_plan), 'utf8'));
if (planHash !== manifest.plan_sha256) fail('PLAN_SHA256_MISMATCH');

const parcelIdentity = sha256(Buffer.from(
  manifest.schema + '\n' + manifest.source.sha256 + '\n' + manifest.plan_sha256,
  'utf8'
));
if (manifest.parcel_id !== 'manga-parcel:' + parcelIdentity) fail('PARCEL_ID_MISMATCH');

for (const page of manifest.issue_plan.pages) {
  const r = page.source_region_px;
  if (r.x < 0 || r.y < 0 || r.width <= 0 || r.height <= 0 ||
      r.x + r.width > dimensions.width || r.y + r.height > dimensions.height) {
    fail('PAGE_REGION_OUT_OF_BOUNDS:' + page.page);
  }
}

const refs = new Map(relatte.payload_refs.map((x) => [x.role, x.address]));
if (relatte.schema !== 'relatte.opaque-organ-spec/v0') fail('BAD_RELATTE_SPEC_SCHEMA');
if (relatte.family_ref !== 'organ:lemonpress/manga-parcel') fail('BAD_RELATTE_FAMILY');
if (relatte.source_particular !== manifest.parcel_id) fail('RELATTE_PARTICULAR_MISMATCH');
if (refs.get('source-pixels') !== 'sha256:' + sourceHash) fail('RELATTE_SOURCE_REF_MISMATCH');
if (refs.get('issue-plan') !== 'sha256:' + planHash) fail('RELATTE_PLAN_REF_MISMATCH');
if (relatte.donor_claims.plan_sha256 !== planHash) fail('RELATTE_PLAN_CLAIM_MISMATCH');
if (relatte.requested_effect?.authority !== 'receiver-local') fail('RELATTE_AUTHORITY_COLLAPSE');

console.log(JSON.stringify({
  ok:true,
  parcel_id:manifest.parcel_id,
  source_sha256:sourceHash,
  plan_sha256:planHash,
  dimensions,
  virtual_pages:manifest.issue_plan.pages.length,
  relatte_family:relatte.family_ref
}, null, 2));
