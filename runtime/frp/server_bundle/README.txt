Upload this whole folder to the ECS Windows desktop.

Then do:
1. Open the ECS security group for TCP 7000 and TCP 18787.
2. Run open_firewall.ps1 on the ECS host.
3. Run start_frps.bat and keep it open.
4. On the local PC, run runtime\\frp\\local_bundle\\start_frpc.bat.
5. Open this URL on the phone:
   http://114.55.225.26:18787/?token=dd2e15efa3da24d8c55967fd37a0db1b
