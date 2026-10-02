# Canonical schema source

These three unchanged generated schemas are vendored from howlcipher/howldream
commit 705019e1502e1896fbf589911ea4d0b09513b6ad, schemas/.
Verified byte-for-byte against that commit during the repair. Dream remains the
canonical owner; update the pin explicitly whenever consuming contract changes.

`howlwriter.copy_package.v1.schema.json` is vendored from howlcipher/howlwriter
merge commit 6c03d8fe796e6c903860b9acddbdf28160e69ca5,
`src/howlwriter/schemas/`. Writer remains the canonical owner. Create validates
Writer packages against this copy and does not import Writer.
