# Package Migration

The Python package has been renamed from `cyberzard` to `cyberzard`.

Current status:
- `cyberzard` acts as a compatibility layer re-exporting from `cyberzard`.
- Internal imports will be gradually updated to reference `cyberzard` directly.
- External users should switch to `import cyberzard`.

Planned steps:
1. Update all internal imports to new package path.
2. Provide deprecation warnings when importing `cyberzard` (optional future step).
3. Remove alias layer after one stable release.
