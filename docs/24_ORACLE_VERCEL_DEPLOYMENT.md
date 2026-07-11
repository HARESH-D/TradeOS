# Oracle And Vercel Deployment Runbook

This runbook deploys the TradeOS frontend to Vercel and the read-only FastAPI backend to an Oracle Cloud VM with a reserved public IPv4. PostgreSQL and Caddy run on the VM through Docker Compose.

## 1. Final Topology

```text
Trader browser
    -> https://your-project.vercel.app
    -> https://api.yourdomain.com
    -> Caddy :443
    -> FastAPI :8000 on private Docker network
    -> PostgreSQL :5432 on private Docker network
    -> Angel One through the OCI reserved public IPv4
```

Only ports 80 and 443 are public application ports. PostgreSQL and FastAPI are not published directly by the production Compose file.

## 2. Prerequisites

- Oracle Cloud account with Always Free capacity
- Vercel account
- GitHub repository containing TradeOS
- A hostname for the backend, such as `api.example.com`
- DNS access for that hostname

The backend hostname must resolve publicly for Caddy to obtain an HTTPS certificate. A custom domain is preferred. A stable HTTPS subdomain may be used for a development deployment.

## 3. Create The Oracle VM

In the Oracle Cloud Console:

1. Select the home region carefully; Always Free compute is provisioned there.
2. Create an Ubuntu VM using an Always Free-eligible shape.
3. Prefer an Ampere A1 Flex VM with enough memory for API, PostgreSQL, and Caddy.
4. Place it in a public subnet.
5. Add your SSH public key.
6. Permit inbound TCP 22 from your own IP only.
7. Permit inbound TCP 80 and TCP/UDP 443 from the internet.
8. Do not open 5432 or 8000.

## 4. Reserve The Public IPv4

Convert the VM public IPv4 to an OCI reserved public IP or create and assign a reserved public IP. Record the address; this is the candidate Angel One Primary Static IP.

Create an `A` DNS record:

```text
api.example.com -> OCI_RESERVED_IPV4
```

Wait until this resolves from a public DNS resolver:

```bash
dig +short api.example.com
```

## 5. Prepare The VM

Connect over SSH and clone the repository:

```bash
ssh ubuntu@OCI_RESERVED_IPV4
git clone https://github.com/HARESH-D/TradeOS.git
cd TradeOS
```

Install Docker and configure the host firewall:

```bash
sudo ./deploy/oracle/bootstrap-ubuntu.sh
```

Sign out and reconnect after the script adds the user to the Docker group.

## 6. Prepare The Backend Environment

From the repository root:

```bash
chmod +x deploy/oracle/*.sh
./deploy/oracle/init-env.sh
```

The script requests:

- Backend hostname without `https://`
- Final Vercel frontend origin
- OCI reserved public IPv4

It generates independent PostgreSQL, JWT, and Fernet secrets in `deploy/oracle/.env.production`. The file is ignored by Git and must be backed up securely.

If the Vercel URL is not known yet, create the frontend deployment first using the next section, then run or update the environment file.

## 7. Deploy The Frontend To Vercel

Push the repository to GitHub, then in Vercel:

1. Select **Add New Project**.
2. Import the TradeOS GitHub repository.
3. Set **Root Directory** to `frontend`.
4. Vercel detects Vite using `frontend/vercel.json`.
5. Add the production environment variable:

```text
VITE_API_URL=https://api.example.com/api
```

6. Deploy and record the stable production URL, for example:

```text
https://tradeos-your-team.vercel.app
```

Use the production URL, not a per-commit preview URL, as `FRONTEND_ORIGIN` on the backend.

## 8. Deploy The Backend

Ensure `deploy/oracle/.env.production` contains the final Vercel origin, then run:

```bash
./deploy/oracle/deploy.sh
```

The script validates Compose, builds the API image, starts PostgreSQL, FastAPI, and Caddy, waits for HTTPS health, and prints service state.

Check logs:

```bash
docker compose \
  --env-file deploy/oracle/.env.production \
  -f deploy/oracle/docker-compose.prod.yml \
  logs --tail=100 api caddy db
```

## 9. Verify The Static Egress IP

Run from the Oracle VM:

```bash
./deploy/oracle/verify-egress-ip.sh
```

The configured and observed IPv4 addresses must match exactly. Do not register the IP with Angel One until this passes.

## 10. Create The First User

Production does not seed the known demo account. Open the Vercel application and select **Create a new account**. Registration returns a signed-in session and creates the first user in PostgreSQL.

## 11. Register The Angel One Application

Use:

```text
App Name:
TradeOS

Redirect URL:
https://api.example.com/api/broker/angel-one/callback

Post back URL:
[blank]

Primary Static IP:
OCI_RESERVED_IPV4

Secondary Static IP:
[blank]
```

The callback currently returns the browser to the TradeOS broker page. The active connection workflow uses API key, client code, PIN, and current TOTP; PIN and TOTP are never persisted.

## 12. Connect Angel One

In TradeOS:

1. Open **Broker Sync**.
2. Select **Live account**.
3. Enter the generated API key, Angel client code, PIN, and current TOTP.
4. Connect the account.
5. Run a manual sync.
6. Verify profile, holdings, trades, positions, and funds counts.

## 13. Database Backups

Create an immediate backup:

```bash
./deploy/oracle/backup-database.sh
```

The script keeps local compressed dumps for 14 days. Copy backups to encrypted off-machine storage. A local backup does not protect against VM or account loss.

Example daily cron entry:

```cron
15 2 * * * /home/ubuntu/TradeOS/deploy/oracle/backup-database.sh >> /home/ubuntu/tradeos-backup.log 2>&1
```

## 14. Updates

After pushing a new release:

```bash
cd ~/TradeOS
git pull --ff-only
./deploy/oracle/deploy.sh
```

Vercel automatically deploys frontend changes from the configured production branch. The backend update rebuilds and replaces only changed containers while retaining PostgreSQL and Caddy volumes.

## 15. Recovery

If the OCI VM is replaced, retain or reassign the reserved public IPv4 so the Angel One registration does not change. Restore the Git repository, `.env.production`, Docker volumes or a database dump, then run `deploy.sh`.

## 16. Security Checklist

- `SEED_DEMO=false` in production
- Strong generated JWT and encryption keys
- Database and API ports not publicly exposed
- OCI security list and host firewall agree
- SSH restricted to your IP or a managed bastion
- Caddy HTTPS health check passes
- Egress verification matches the registered Angel One IP
- `.env.production` is not in Git
- Backups are encrypted and stored off the VM
- Operating system and containers are updated regularly

## 17. Current External Blockers

Repository preparation can be completed locally, but creating the live resources requires authenticated user accounts:

- Vercel project authorization or CLI login
- Oracle Cloud account, VM, reserved IP, and DNS configuration
- A stable backend hostname

Do not share account passwords, private SSH keys, TOTP seeds, or broker PINs. Use provider-generated access controls and enter broker secrets only in the deployed TradeOS form.

