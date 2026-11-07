# Titan logger

`logger.py` is an administration helper for watermarked flags and the central
issuance log.

```bash
python3 logger.py registry
python3 logger.py verify <nickname> 'CTF{...}'
python3 logger.py trace 'CTF{...}'
python3 logger.py tail 50
```

By default it reads `../data/user_registry.csv`, `../data/watermark.key` and
`../logs/flag_issuance.log` relative to the `CTFd/` folder.  Override the
paths with `TITAN_DATA_DIR`, `TITAN_REGISTRY`, `TITAN_WATERMARK_SECRET_FILE`
and `TITAN_LOG_PATH`.

The `trace` command checks both the registry and every address in
`10.8.0.10–10.8.0.250`, so a leaked flag can still be attributed if the
registry was restored from an older backup.
