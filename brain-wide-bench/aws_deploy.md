# AWS Deployment — brain-wide-bench (us-east-1)

**Global conventions (apply to every step):**
- All `aws` commands use `--profile ucl` and target `--region us-east-1`.
- Tag every newly created resource with `Key=Project,Value=wg-brain-wide-bench`.

GitHub repo: https://github.com/int-brain-lab/app-brain-wide-bench  
Ansible playbook: `iblsre/brain-wide-bench/ansible/setup_brainwidebench_server.yaml`

---

## Status

| Step | Status |
|---|---|
| 0. ibl-benchmark dependency | ⚠️ Deferred — rsynced manually; publish to PyPI before production |
| GitHub repo | ✅ https://github.com/int-brain-lab/app-brain-wide-bench (public) |
| 1. S3 bucket | ✅ `brainwidebench-submissions` |
| 2. Upload ground truth | ✅ 232 files |
| 3. IAM role | ✅ `brainwidebench-ec2-role` |
| 4. Security group | ✅ `sg-0c77cd3f815a48d3a` |
| 5. EC2 key pair | ✅ `~/.ssh/brainwidebench-key.pem` |
| 6. Launch EC2 | ✅ `i-0b15a5ba8ccdc2ebd` |
| 7. Elastic IP | ✅ `52.2.174.198` |
| 8. Server bootstrap (Ansible) | ✅ Docker, `/srv/app-brain-wide-bench`, aliases |
| 8b. First deploy | ✅ `{"status":"ok"}` at `https://brainwidebench.iblcore.org/health` |
| 9. Auth0 | ✅ tenant `dev-dmv00yvt1n0i036m.us.auth0.com` |
| 9b. DNS (Cloudflare) | ✅ `brainwidebench.iblcore.org → 52.2.174.198` |
| 10. CI/CD (GitHub Actions + SSM) | ✅ push-to-main deploys automatically |
| 11. SSL | ✅ Let's Encrypt via Cloudflare DNS-01; nginx terminates TLS on 443 |
| 12. Auth0 callback URLs | ✅ Updated to `https://brainwidebench.iblcore.org` |
| Frontend served | ✅ FastAPI StaticFiles at `/`; `index.html` at root |
| ORCID social login | ⏳ Deferred — requires Auth0 Developer plan |

---

## 0. Note on `ibl-benchmark` dependency

`ibl-benchmark` is a private repo consumed as an editable path (`../ibl-benchmark`).
On the server it lives at `/srv/ibl-benchmark` and was placed there via:

```bash
rsync -az --exclude='.git' --exclude='__pycache__' --exclude='*.egg-info' --exclude='.venv' \
  <local>/ibl-benchmark/ \
  -e "ssh -i ~/.ssh/brainwidebench-key.pem" \
  ubuntu@52.2.174.198:/srv/ibl-benchmark/
```

This must be repeated whenever `ibl-benchmark` changes, until it is published to PyPI and
pinned in `pyproject.toml`.

---

## 1. S3 bucket for submissions

```bash
aws s3api create-bucket \
  --bucket brainwidebench-submissions \
  --region us-east-1 \
  --profile ucl

# CORS — required for browser direct-upload via presigned PUT URL
cat > /tmp/cors.json <<'EOF'
{
  "CORSRules": [{
    "AllowedOrigins": ["*"],
    "AllowedMethods": ["PUT"],
    "AllowedHeaders": ["Content-Type"],
    "MaxAgeSeconds": 3000
  }]
}
EOF
aws s3api put-bucket-cors \
  --bucket brainwidebench-submissions \
  --cors-configuration file:///tmp/cors.json \
  --profile ucl

aws s3api put-bucket-tagging \
  --bucket brainwidebench-submissions \
  --tagging 'TagSet=[{Key=Project,Value=wg-brain-wide-bench}]' \
  --profile ucl
```

> **Note:** The UCL org SCP blocks `PutBucketPublicAccessBlock` at the bucket level and no
> account-level block is set. The bucket is private by default (no public ACL or policy).
> Raise with the UCL cloud team to enable account-level S3 Block Public Access.

---

## 2. Upload ground truth to S3

Local source: `~/Documents/datadisk/brain-wide-bench/ts1`

```bash
aws s3 sync \
  ~/Documents/datadisk/brain-wide-bench/ts1 \
  s3://brainwidebench-submissions/ground-truth/ts1 \
  --profile ucl --no-progress
```

S3 structure: `ground-truth/ts1/<task_name>/<session_id>/causal/ground_truth.safetensors`

---

## 3. IAM roles

### EC2 instance role

```bash
cat > /tmp/ec2-trust.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [{"Effect":"Allow","Principal":{"Service":"ec2.amazonaws.com"},"Action":"sts:AssumeRole"}]
}
EOF

aws iam create-role \
  --role-name brainwidebench-ec2-role \
  --assume-role-policy-document file:///tmp/ec2-trust.json \
  --tags Key=Project,Value=wg-brain-wide-bench \
  --profile ucl

# S3 access
cat > /tmp/s3-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["s3:PutObject","s3:GetObject","s3:DeleteObject","s3:ListBucket"],
    "Resource": ["arn:aws:s3:::brainwidebench-submissions","arn:aws:s3:::brainwidebench-submissions/*"]
  }]
}
EOF
aws iam put-role-policy \
  --role-name brainwidebench-ec2-role \
  --policy-name brainwidebench-s3-access \
  --policy-document file:///tmp/s3-policy.json \
  --profile ucl

# SSM (required for GitHub Actions deploy)
aws iam attach-role-policy \
  --role-name brainwidebench-ec2-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore \
  --profile ucl

aws iam create-instance-profile \
  --instance-profile-name brainwidebench-ec2-profile \
  --tags Key=Project,Value=wg-brain-wide-bench \
  --profile ucl
aws iam add-role-to-instance-profile \
  --instance-profile-name brainwidebench-ec2-profile \
  --role-name brainwidebench-ec2-role \
  --profile ucl
```

### GitHub Actions role (OIDC — no stored credentials)

```bash
# One-time: create the GitHub OIDC provider
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 \
  --profile ucl

# Trust policy: only this repo
cat > /tmp/github-trust.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Federated": "arn:aws:iam::537761737250:oidc-provider/token.actions.githubusercontent.com"},
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {"token.actions.githubusercontent.com:aud": "sts.amazonaws.com"},
      "StringLike": {"token.actions.githubusercontent.com:sub": "repo:int-brain-lab/app-brain-wide-bench:*"}
    }
  }]
}
EOF
aws iam create-role \
  --role-name brainwidebench-github-actions-role \
  --assume-role-policy-document file:///tmp/github-trust.json \
  --tags Key=Project,Value=wg-brain-wide-bench \
  --profile ucl

# SSM send-command on this instance only
cat > /tmp/github-ssm-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "ssm:SendCommand",
      "Resource": [
        "arn:aws:ec2:us-east-1:537761737250:instance/i-0b15a5ba8ccdc2ebd",
        "arn:aws:ssm:us-east-1::document/AWS-RunShellScript"
      ]
    },
    {"Effect":"Allow","Action":["ssm:GetCommandInvocation","ssm:DescribeInstanceInformation"],"Resource":"*"}
  ]
}
EOF
aws iam put-role-policy \
  --role-name brainwidebench-github-actions-role \
  --policy-name brainwidebench-ssm-deploy \
  --policy-document file:///tmp/github-ssm-policy.json \
  --profile ucl
```

---

## 4. Security group

SSH is restricted to the `developers` managed prefix list (16 IBL developer IPs).
To add a developer IP, update **both** `pl-0eb789aa874fc1952` (us-east-1) and
`pl-05d04791174282256` (eu-west-2).

```bash
aws ec2 create-security-group \
  --group-name brainwidebench-sg \
  --description "brain-wide-bench web server" \
  --region us-east-1 --profile ucl

# HTTP — public
aws ec2 authorize-security-group-ingress \
  --group-id sg-0c77cd3f815a48d3a \
  --protocol tcp --port 80 --cidr 0.0.0.0/0 \
  --region us-east-1 --profile ucl

# SSH — IBL developers prefix list only
aws ec2 authorize-security-group-ingress \
  --group-id sg-0c77cd3f815a48d3a \
  --ip-permissions '[{"IpProtocol":"tcp","FromPort":22,"ToPort":22,"PrefixListIds":[{"PrefixListId":"pl-0eb789aa874fc1952","Description":"IBL developers"}]}]' \
  --region us-east-1 --profile ucl
```

> GitHub Actions deploys via SSM (no inbound port 22 needed from GitHub runners).

---

## 5. EC2 key pair

```bash
aws ec2 create-key-pair \
  --key-name brainwidebench-key \
  --query 'KeyMaterial' --output text \
  --tag-specifications 'ResourceType=key-pair,Tags=[{Key=Project,Value=wg-brain-wide-bench}]' \
  --region us-east-1 --profile ucl > ~/.ssh/brainwidebench-key.pem
chmod 400 ~/.ssh/brainwidebench-key.pem
```

---

## 6. Launch EC2 instance

```bash
# Find latest Ubuntu 24.04 LTS AMI
aws ec2 describe-images \
  --owners 099720109477 \
  --filters "Name=name,Values=ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*" \
            "Name=state,Values=available" \
  --query 'sort_by(Images, &CreationDate)[-1].ImageId' \
  --output text --region us-east-1 --profile ucl

aws ec2 run-instances \
  --image-id <ami-id> \
  --instance-type t3.small \
  --key-name brainwidebench-key \
  --security-group-ids sg-0c77cd3f815a48d3a \
  --iam-instance-profile Name=brainwidebench-ec2-profile \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":30,"VolumeType":"gp3"}}]' \
  --tag-specifications \
    'ResourceType=instance,Tags=[{Key=Name,Value=brainwidebench},{Key=Project,Value=wg-brain-wide-bench}]' \
    'ResourceType=volume,Tags=[{Key=Project,Value=wg-brain-wide-bench}]' \
  --region us-east-1 --profile ucl
```

---

## 7. Elastic IP

```bash
aws ec2 allocate-address \
  --domain vpc \
  --tag-specifications 'ResourceType=elastic-ip,Tags=[{Key=Project,Value=wg-brain-wide-bench},{Key=Name,Value=brainwidebench}]' \
  --region us-east-1 --profile ucl

aws ec2 associate-address \
  --instance-id <instance-id> \
  --allocation-id <eipalloc-id> \
  --region us-east-1 --profile ucl
```

---

## 8. Server bootstrap (Ansible)

Run once after launching a fresh instance.

```bash
ssh -i ~/.ssh/brainwidebench-key.pem ubuntu@52.2.174.198

# On the instance:
sudo apt-get update && sudo apt-get install -y ansible git
# iblsre is private — scp the playbook directly instead:
# (from local) scp -i ~/.ssh/brainwidebench-key.pem \
#   iblsre/brain-wide-bench/ansible/setup_brainwidebench_server.yaml \
#   ubuntu@52.2.174.198:/tmp/
ansible-playbook /tmp/setup_brainwidebench_server.yaml
```

The playbook installs Docker, clones `app-brain-wide-bench` to `/srv/app-brain-wide-bench`
(with `/srv/app` as a symlink), creates a 1 GB spacer file, and adds `bwb` shell aliases.

Then from local, rsync `ibl-benchmark` and copy `.env`:

```bash
rsync -az --exclude='.git' --exclude='__pycache__' --exclude='*.egg-info' --exclude='.venv' \
  <local>/ibl-benchmark/ \
  -e "ssh -i ~/.ssh/brainwidebench-key.pem" \
  ubuntu@52.2.174.198:/srv/ibl-benchmark/

scp -i ~/.ssh/brainwidebench-key.pem .env ubuntu@52.2.174.198:/srv/app-brain-wide-bench/.env
```

`.env` values (do **not** set `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` — instance role handles auth):

| Variable | Value |
|---|---|
| `DATABASE_URL` | `postgresql+psycopg://brainwidebench:<pw>@db:5432/brainwidebench` |
| `POSTGRES_USER` | `brainwidebench` |
| `POSTGRES_PASSWORD` | *(strong random password — store in password manager)* |
| `REDIS_URL` | `redis://redis:6379/0` |
| `AUTH0_DOMAIN` | `dev-dmv00yvt1n0i036m.us.auth0.com` |
| `AUTH0_AUDIENCE` | `https://brainwidebench.iblcore.org` |
| `AWS_REGION` | `us-east-1` |
| `S3_BUCKET` | `brainwidebench-submissions` |
| `S3_GT_PREFIX` | `ground-truth/ts1` |
| `CORS_ORIGINS` | `*` |

First deploy:

```bash
ssh -i ~/.ssh/brainwidebench-key.pem ubuntu@52.2.174.198
cd /srv/app-brain-wide-bench
docker compose up -d --build
docker compose exec -T web uv run alembic upgrade head
curl http://localhost/health   # → {"status":"ok"}
```

---

## 9. Auth0 tenant setup

**Tenant:** `dev-dmv00yvt1n0i036m.us.auth0.com`  
**SPA Client ID:** `jYERzEVe5MWl0r8SKGshQLRvxswseQlS`  
**API audience:** `https://brainwidebench.iblcore.org`

Steps performed in the Auth0 dashboard:
1. Tenant created.
2. SPA application created; Allowed Callback/Logout/Web Origins set to `http://52.2.174.198`.
3. API created with identifier `https://brainwidebench.iblcore.org` (RS256).
4. Google and Microsoft social logins enabled.
5. ORCID: deferred (requires Auth0 Developer plan).

Once DNS propagates, add `http://brainwidebench.iblcore.org` to the Auth0 SPA settings
alongside the IP. Update both entries to `https://` once SSL is provisioned.

---

## 9b. DNS — Cloudflare

A record added to the `iblcore.org` zone:

| Type | Name | Content | Proxy |
|---|---|---|---|
| A | `brainwidebench` | `52.2.174.198` | DNS only (grey cloud) |

Enable Cloudflare proxy only after SSL is configured — the proxy interferes with HTTP-01
Let's Encrypt challenges.

---

## 10. CI/CD — GitHub Actions + SSM

Every push to `main` triggers `.github/workflows/deploy.yml`:

1. Authenticates to AWS via **GitHub OIDC** (no stored credentials — role `brainwidebench-github-actions-role`).
2. Sends `/srv/app-brain-wide-bench/scripts/deploy.sh` to the EC2 instance via **AWS SSM** (no inbound port 22 needed from GitHub).
3. Polls until the command succeeds or fails, then surfaces the exit code.

The deploy script on the server:
```bash
# /srv/app-brain-wide-bench/scripts/deploy.sh
sudo -u ubuntu bash -c '
  cd /srv/app-brain-wide-bench
  git pull
  docker compose up -d --build
  docker compose exec -T web uv run alembic upgrade head
'
# Health check with retry (30s)
for i in $(seq 1 10); do
  curl -sf http://localhost/health | grep -q '"status":"ok"' && echo "Deploy complete." && exit 0
  sleep 3
done
exit 1
```

GitHub Actions secrets in the repo:

| Secret | Purpose |
|---|---|
| `AWS_ROLE_ARN` | `arn:aws:iam::537761737250:role/brainwidebench-github-actions-role` |
| `EC2_HOST` | `52.2.174.198` (retained for manual SSH) |
| `EC2_SSH_KEY` | Private key (retained for manual SSH) |

---

## Summary of AWS resources

| Resource | Name / ID |
|---|---|
| S3 bucket | `brainwidebench-submissions` |
| IAM EC2 role | `brainwidebench-ec2-role` |
| IAM instance profile | `brainwidebench-ec2-profile` |
| IAM GitHub Actions role | `brainwidebench-github-actions-role` |
| GitHub OIDC provider | `arn:aws:iam::537761737250:oidc-provider/token.actions.githubusercontent.com` |
| Security group | `brainwidebench-sg` (`sg-0c77cd3f815a48d3a`) |
| Developers prefix list (us-east-1) | `pl-0eb789aa874fc1952` (mirrors eu-west-2 `pl-05d04791174282256`) |
| Key pair | `brainwidebench-key` |
| EC2 instance | `i-0b15a5ba8ccdc2ebd` (t3.small, Ubuntu 24.04, `ami-0f8a61b66d1accaee`) |
| Elastic IP | `52.2.174.198` (`eipalloc-03675f0d4d99b63bc`) |
| Region | `us-east-1` |

---

## Ongoing costs (approximate)

| Resource | $/month |
|---|---|
| EC2 t3.small | ~$15 |
| EBS 30 GB gp3 | ~$2.50 |
| Elastic IP (attached) | $0 |
| S3 (~1 GB) | <$0.50 |
| SSM / IAM / OIDC | $0 |
| **Total** | **~$18** |

---

## 11. SSL — Let's Encrypt via Cloudflare DNS challenge

nginx is already in `docker-compose.yml` as a reverse proxy. SSL is provisioned in two steps:
a local CLI command to open port 443, then an Ansible playbook on the server.

### a) Open port 443 in the security group (run from local)

```bash
aws ec2 authorize-security-group-ingress \
  --group-id sg-0c77cd3f815a48d3a \
  --protocol tcp --port 443 --cidr 0.0.0.0/0 \
  --region us-east-1 --profile ucl
```

### b) Run the SSL Ansible playbook on the EC2 instance

Copy the playbook to the server and run it:

```bash
scp -i ~/.ssh/brainwidebench-key.pem \
  iblsre/brain-wide-bench/ansible/setup_ssl.yaml \
  ubuntu@52.2.174.198:/tmp/

ssh -i ~/.ssh/brainwidebench-key.pem ubuntu@52.2.174.198

# On the instance:
sudo ansible-playbook /tmp/setup_ssl.yaml \
  -i localhost, --connection=local \
  --extra-vars "cloudflare_api_token=<token>"
```

The playbook:
- Installs certbot + `python3-certbot-dns-cloudflare`
- Issues a cert for `brainwidebench.iblcore.org` (DNS-01 challenge — no port 80 needed)
- Sets `/etc/letsencrypt/live` and `/archive` permissions to 755 for Docker
- Writes a renewal hook (`/etc/letsencrypt/renewal-hooks/deploy/restart-nginx.sh`) that reloads nginx
- Writes `/srv/app-brain-wide-bench/docker-compose.override.yaml` to mount `/etc/letsencrypt` into the nginx container

### c) Restart the stack

```bash
cd /srv/app-brain-wide-bench
docker compose down
docker compose up -d
```

Verify:
```bash
curl -I https://brainwidebench.iblcore.org/health
# HTTP/2 200, {"status":"ok"}
```

---

## 12. Auth0 callback URL update

Once HTTPS is confirmed working, update the SPA application in the Auth0 dashboard:

**Tenant:** `dev-dmv00yvt1n0i036m.us.auth0.com`  
**SPA Client ID:** `jYERzEVe5MWl0r8SKGshQLRvxswseQlS`

In **Applications → brainwidebench → Settings**, replace every occurrence of
`http://52.2.174.198` with `https://brainwidebench.iblcore.org` in:
- **Allowed Callback URLs**
- **Allowed Logout URLs**
- **Allowed Web Origins**

Save changes. The `AUTH0_AUDIENCE` in `.env` (`https://brainwidebench.iblcore.org`) is already correct.

---

## Pending / future work

- **`ibl-benchmark` on PyPI** — remove the manual rsync step; pin a version in `pyproject.toml`.
- **ORCID social login** — requires Auth0 Developer plan.
