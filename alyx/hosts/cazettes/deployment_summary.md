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
| **Security group** | `sg-0f5d7e8c3b2d6bcd0` (`alyx-cazettes-sg`) — SSH port 22 open to `sg-0aadda61e701d7681` (SSH developers) |
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
Host-side certbot is set up by `cazettes_setup.yaml`; the base compose mounts `/etc/letsencrypt` into the
container, and `alyx_issue_ssl.sh` skips issuance because the certificate already exists.

---

## Server Layout

Deployed by `alyx/ansible/ansible_deploy_alyx.yaml` (inventory host `cazettes`), same as the other servers.
`~/app` is managed by ansible and is not a git checkout.

```
/home/ubuntu/app/
  docker-compose.yaml            ← fetched from the cortex-lab/alyx release tag
  docker-compose.scripts.yaml    ← fleet-wide scripts mount
  docker-compose.host.yaml       ← from alyx/hosts/cazettes/ (RDS: local postgres disabled)
  .env                           ← decrypted from alyx/hosts/cazettes/env (see below)
  scripts/                       ← synced from alyx/scripts/
/etc/letsencrypt/                ← host certbot (Cloudflare DNS-01), mounted into the container
```

The IBL overlay (`docker-compose.ibl.yaml`) is disabled for this host (`alyx_apply_ibl_overlay: false`):
no iblalyx mounts, no `~/iblalyx` clone.

### Secrets

`alyx/hosts/cazettes/env` is the sops-encrypted `.env` (KMS key in the UCL account). The playbook never
creates `~/app/.env`; place it on the server before the first deploy, and again after any change:

```bash
# from alyx/ on a machine with the `ucl` AWS profile
AWS_PROFILE=ucl sops -d --input-type json --output-type binary hosts/cazettes/env \
  | ssh alyx-cazettes 'umask 077; mkdir -p ~/app && cat > ~/app/.env'
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

From the control node (mbox), in `alyx/ansible`:

```bash
git -C ../.. pull
ansible-playbook ansible_deploy_alyx.yaml -e alyx_version=<tag> --limit cazettes
```

The playbook takes a per-database `pg_dump` of `cazettes_alyx` first (not an RDS snapshot: the `openlayx`
instance is shared with openalyx), pulls the image, recreates the containers, runs `migrate` and the
post-deploy checks. Rollback dumps are kept in `~/backups/alyx`.

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
