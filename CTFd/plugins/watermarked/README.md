# Operation Titan — watermarked CTFd flag

This plugin registers the `watermarked` flag type.  A flag is accepted only
when it matches the VPN address that the VPN portal assigned to the logged-in
CTFd user.

Every incorrect submission is forwarded to the internal watermark service,
which records a `CHEAT_DETECTED` line in `../logs/flag_issuance.log`.

The plugin is mounted into the CTFd container by `../docker-compose.yml`.
