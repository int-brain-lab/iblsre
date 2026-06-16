# Cazettes Lab — Deployment Summary

**Deployed:** 2026-06-16  
**Deployed by:** olivier.winter@internationalbrainlab.org

---

## Access

| | |
|---|---|
| **URL** | https://cazettes.iblcore.org/admin/ |
| **Admin login** | `root` / *(see password manager)* |

---

## AWS Resources

| Resource | Value |
|---|---|
| **EC2 instance** | `i-0a9ae0bd57840b9e5` (t3.small, Ubuntu 24.04, eu-west-2) |
| **Elastic IP** | `16.60.20.132` |
| **Security group** | `sg-0f5d7e8c3b2d6bcd0` (`alyx-cazettes-sg`) |
| **S3 bucket** | `cazettes-alyx-uploaded` (eu-west-2) |
| **IAM user** | `cazettes-alyx-s3` |
| **RDS** | `openlayx.clfrcwlvymbw.eu-west-2.rds.amazonaws.com` (shared, no new instance) |
| **Database** | `cazettes_alyx` on existing `openlayx` RDS |
| **DNS** | Cloudflare A record `cazettes.iblcore.org → 16.60.20.132` (DNS-only, no proxy) |

All resources tagged `Project=2026-cazettes`.

---

## TLS Certificate

Issued by Let's Encrypt via Cloudflare DNS-01 challenge (`python3-certbot-dns-cloudflare`).  
Auto-renews via `/etc/letsencrypt/renewal-hooks/deploy/restart-alyx.sh` (restarts `alyx_apache` on renewal).

---

## Server Layout

```
/home/ubuntu/Documents/PYTHON/iblsre/   ← iblsre repo
alyx/containers/deploy-web/
  docker-compose.yaml                   ← main compose file
  .env                                  ← secrets (not committed)
/etc/letsencrypt/                       ← mounted :ro into container
```

---

## Known Issue — SSL on First Boot

On the initial container start, `a2enmod ssl` runs inside `alyx_issue_ssl.sh` but Apache's
`-DFOREGROUND` process does not reload the module. OpenSSL does not appear in the Apache
banner until a graceful restart is triggered manually:

```bash
docker exec alyx_apache apache2ctl graceful
```

**Workaround applied:** graceful restart was run after first boot. The instance is in the
correct state. A permanent fix would be to add `apache2ctl graceful` at the end of
`alyx_issue_ssl.sh`, or run `docker restart alyx_apache` after first launch.

---

## Update Procedure

```bash
cd ~/Documents/PYTHON/iblsre/alyx/containers/deploy-web
git pull
docker compose pull
docker compose down
docker compose up -d
docker exec -it alyx_apache python manage.py migrate
```

If disk is tight before pulling:
```bash
docker system prune --all --force
```

---

## Cost

| Resource | $/month |
|---|---|
| EC2 t3.small | ~$15 |
| RDS (existing, shared) | $0 incremental |
| S3 (few GB) | <$1 |
| Elastic IP (attached) | Free |
| **Total** | **~$16** |

Track via AWS Cost Explorer → Filter → Tag → `Project = 2026-cazettes`.
