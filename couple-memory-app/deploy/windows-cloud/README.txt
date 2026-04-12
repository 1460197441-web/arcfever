Windows cloud deployment bundle for Couple Memory App

Files:
- dist/                exported Expo web build
- server.cjs           zero-dependency static server with SPA fallback
- start-server.bat     starts the site on port 8080

Quick steps on the cloud computer:
1. Install Node.js 18 or newer if Node is not installed.
2. Open PowerShell in this folder.
3. Run: node .\server.cjs
4. Open Windows Firewall and the cloud security group for TCP 8080.
5. Visit: http://YOUR_SERVER_IP:8080

If you want another port:
- PowerShell: $env:PORT=18080; node .\server.cjs
- CMD: set PORT=18080 && node server.cjs
