# Error response format

Every handler returns errors in this shape:

```json
{ "error": { "code": "<MACHINE_CODE>", "message": "<human readable>" } }
```

- 400 for bad input, 404 for missing records, 500 for anything else.
