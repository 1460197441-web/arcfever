frp remote access bundle for `gold_strategy_alert`

Public ECS IP:
- `114.55.225.26`

Access URL after both sides start:
- `http://114.55.225.26:18787/?token=dd2e15efa3da24d8c55967fd37a0db1b`

Ports to allow on ECS security group:
- `7000/TCP` for `frps`
- `18787/TCP` for the exposed control panel

Workflow:
1. Upload everything in `server_bundle` to the ECS desktop.
2. On ECS, run `open_firewall.ps1`, then run `start_frps.bat`.
3. On this local PC, run `local_bundle\\start_frpc.bat`.
4. Open the URL above on your phone.

Notes:
- The app control server now listens only on `127.0.0.1:8787`.
- Access is protected by the app token in the URL.
- `frp` tunnel auth token is separate from the app token.
