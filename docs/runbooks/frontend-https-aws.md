# Runbook — frontend HTTPS on AWS (S3 + CloudFront + Route 53)

Terraform owns every resource on this page (`infra/aws/frontend.tf`,
[ADR 0010](../architecture/adr/0010-domain-roots-in-terraform.md)): the bucket, the
distribution and the DNS records are created by it, and the ACM certificate and the hosted
zone are imported into its state. Deploys go through [deploy.md](deploy.md). This page is the
console walk-through of the same setup, for reference when reading the Terraform or the
console; do not apply it by hand on top of the Terraform-managed resources.

## Architecture

```text
User → Route 53 (kyrian-world.com) → CloudFront (HTTPS) → S3 (private, OAC)
                ↓
         ACM Certificate (us-east-1)
```

## Resources

| Resource | Name/ID | Region |
|:---|:---|:---|
| ACM certificate | `kyrian-world.com` + `*.kyrian-world.com` | us-east-1 |
| CloudFront distribution | `d30ecrvgx9jgud.cloudfront.net` | Global |
| S3 bucket | `kyrian-world.com` | eu-west-1 |
| Route 53 hosted zone | `kyrian-world.com` | Global |

---

## Step 1: request the ACM certificate

**Important:** the certificate must live in `us-east-1` (N. Virginia) to work with CloudFront.

1. Open **AWS Certificate Manager (ACM)** in the console.
2. Switch the region to **US East (N. Virginia) `us-east-1`**.
3. **Request certificate** → **Request a public certificate**.
4. **Fully qualified domain name:**
   - `kyrian-world.com`
   - `*.kyrian-world.com` (or `www.kyrian-world.com`)
5. **Validation method:** DNS validation.
6. **Request** → open the certificate → **Create records in Route 53**.
7. Wait for the status to become **Issued** (2-10 minutes).

---

## Step 2: the S3 bucket

1. In **S3**, the bucket:
   - **Bucket name:** `kyrian-world.com`
   - **Object Ownership:** ACLs disabled
   - **Block all public access:** on
2. Its content is `src/frontend/out/` (with `index.html` at the root).

---

## Step 3: the CloudFront distribution

1. **CloudFront** → **Create distribution**.
2. Pick the **Free plan (0$)**.
3. Initial settings:
   - **Distribution name:** `kyrian-world.com-frontend`
   - **Description:** Travel AI World Frontend
   - **Distribution type:** Single website configuration
   - **Domain:** leave empty (set later)
4. **Origin:**
   - **Origin domain:** the bucket `kyrian-world.com.s3.eu-west-1.amazonaws.com`
   - **Origin access:** Origin access control settings (recommended) → **Create new OAC** → Sign requests (recommended)
5. **Settings:**
   - **Price class:** Use all edge locations (or only N. America/Europe to save; Terraform's `cloudfront_price_class`)
   - **Default root object:** `index.html`
   - **Alternate domain name (CNAME):** `kyrian-world.com` (Terraform also adds `www.kyrian-world.com`)
   - **Custom SSL certificate:** the ACM certificate for `kyrian-world.com`
   - **Security policy:** `TLSv1.2_2021 (recommended)`
6. **Create distribution**.

---

## Step 4: the default behavior

1. In the distribution, the **Behaviors** tab.
2. `Default (*)` → **Edit**.
3. **Viewer protocol policy:** **Redirect HTTP to HTTPS**.
4. **Allowed HTTP methods:** `GET, HEAD`.
5. **Save changes**.

Terraform adds a second behavior for `/api/*` (HTTPS only, every method, caching disabled,
no compression so SSE streams chunk by chunk) that sends the API to API Gateway on the same origin.

---

## Step 5: routes of the static export

Next.js exports static files, so an inner route such as `/trips/` has to resolve to
`/trips/index.html`. A CloudFront Function on the default behavior's viewer request
(`aws_cloudfront_function.directory_index`) does that rewrite. Do not use distribution-wide
error pages that answer 403/404 with `/index.html` and 200: they apply to the whole
distribution and turn the API's 403/404 into HTML.

There is one narrow custom error response: the 403 S3 returns for a path that does not exist
is served as `404.html` with status 404 and no error caching. The API's JSON 404s pass
through untouched, and an API 403 reaches the client as 404 (the frontend treats both as
"not found"). See also [deploy.md](deploy.md).

---

## Step 6: the bucket policy (OAC)

CloudFront generates the policy. In S3 it looks like this:

1. **S3** → bucket `kyrian-world.com` → **Permissions** → **Bucket policy**.
2. It holds a statement like:

   ```json
   {
     "Effect": "Allow",
     "Principal": { "Service": "cloudfront.amazonaws.com" },
     "Action": "s3:GetObject",
     "Resource": "arn:aws:s3:::kyrian-world.com/*",
     "Condition": {
       "ArnLike": {
         "AWS:SourceArn": "arn:aws:cloudfront::<ACCOUNT_ID>:distribution/<DISTRIBUTION_ID>"
       }
     }
   }
   ```

3. **Block all public access** stays on for the bucket.

---

## Step 7: Route 53

1. **Route 53** → **Hosted zones** → `kyrian-world.com`.
2. No A record may point at an S3 website endpoint (`s3-website-...`); delete one if it exists.
3. **Create record**:
   - **Record name:** empty (root domain)
   - **Record type:** `A - Routes traffic to an IPv4 address and some AWS resources`
   - **Alias:** on
   - **Route traffic to:** **Alias to CloudFront distribution** → `d30ecrvgx9jgud.cloudfront.net`
   - **Create records**
4. An identical `AAAA` record for IPv6. Terraform also creates the `www` A record.

---

## Verification

```bash
# check that the DNS resolves to CloudFront (not to S3)
nslookup kyrian-world.com

# it must return CloudFront IPs (13.224.x.x, 99.84.x.x, etc.)
```

**In the browser:**

- `http://kyrian-world.com` redirects to `https://kyrian-world.com`
- The TLS padlock is valid
- The Kyrian World app loads

---

## Settings the frontend depends on (backend)

| Setting | Description |
|:---|:---|
| `NEXT_PUBLIC_API_URL` | The frontend is built with the API's URL (see [deploy.md](deploy.md)) |
| Backend CORS | `https://kyrian-world.com` is in `BACKEND_CORS_ORIGINS` |
| Google OAuth | `https://kyrian-world.com` is an authorized origin |

---

## Notes

- **Estimated cost:** ~0$ (CloudFront free tier: 1 TB + 10M requests/month for 12 months).
- **DNS propagation:** immediate in Route 53; globally it can take up to 48h (usually minutes).
- **Cache invalidation:** after a frontend update, invalidate `/*` in CloudFront (the deploy
  workflow does it).
