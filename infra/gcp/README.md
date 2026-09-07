# Infraestructura Terraform para Travel AI World (GCP)

![Terraform](https://img.shields.io/badge/Terraform-1.6%2B-7B42BC?style=for-the-badge&logo=terraform&logoColor=white)
![Google Cloud](https://img.shields.io/badge/Google%20Cloud-GCP-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white)
![Cloud Run](https://img.shields.io/badge/Cloud%20Run-Serverless-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-316192?style=for-the-badge&logo=postgresql&logoColor=white)

Infraestructura de **Google Cloud** para el backend de Travel AI World, que son **dos servicios** (ver [ADR 0001](../../docs/architecture/adr/0001-backend-split.md)):

| Servicio | Imagen | Qué hace | Accede a |
|---|---|---|---|
| `core_api` | `core-api` | Google auth, usuarios, trips (CRUD) | Cloud SQL por IP privada |
| `ai_api` | `ai-api` | Chat con streaming (NVIDIA) | `core_api` por HTTPS, con el token del usuario |

Cada servicio corre en su propio **Cloud Run**, con su propia cuenta de servicio y acceso **solo a sus secretos**.

## Qué crea Terraform

- APIs de GCP necesarias, VPC, subred y Serverless VPC Access Connector.
- Cloud SQL PostgreSQL 15 privado, base de datos y usuario.
- Un repositorio Docker en Artifact Registry (`${name_prefix}-images`).
- Secretos en Secret Manager: `secret-key`, `google-client-id`, `google-client-secret`, `db-password`, `nvidia-api-key`.
- Dos servicios Cloud Run (módulo `modules/cloud_run_service`):
  - `${name_prefix}-core-api`: recibe DB\_\*, `GOOGLE_*`, `SECRET_KEY`; egress privado a Cloud SQL.
  - `${name_prefix}-ai-api`: recibe `NVIDIA_API_KEY`, `SECRET_KEY`, `CORE_API_URL` (la URL del anterior). Sin VPC.
- Acceso público (`allUsers`) a ambos endpoints.

`SECRET_KEY` es el mismo secreto para los dos: `ai_api` verifica los JWT que emite `core_api`.

## Qué no crea

- El frontend (Next.js estático): publícalo aparte (Firebase Hosting, Cloud Storage + CDN, GitHub Pages).
- Un Load Balancer que unifique los dos servicios bajo un dominio. No hace falta: el frontend acepta dos URLs (`NEXT_PUBLIC_API_URL` y `NEXT_PUBLIC_AI_API_URL`). Añádelo cuando quieras un único dominio.
- Las imágenes Docker: las construye CI (`.github/workflows/backend-images.yml`) y las publica en GHCR; el workflow `deploy-backend.yml` las copia a Artifact Registry.

## Requisitos

- Proyecto de Google Cloud con facturación, `gcloud`, Terraform >= 1.6, Docker.
- Permisos para Cloud Run, Cloud SQL, VPC, Artifact Registry, Secret Manager y cuentas de servicio.

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project TU_PROJECT_ID
```

## Configuración

```bash
cd infra/gcp
cp terraform.tfvars.example terraform.tfvars
```

Rellena `terraform.tfvars` (está en `.gitignore`, nunca se sube):

```hcl
project_id     = "tu-project-id"
region         = "europe-west1"
zone           = "europe-west1-b"
name_prefix    = "travel-ai"
core_api_image = "europe-west1-docker.pkg.dev/tu-project-id/travel-ai-images/core-api:latest"
ai_api_image   = "europe-west1-docker.pkg.dev/tu-project-id/travel-ai-images/ai-api:latest"

db_password          = "una-password-segura"
nvidia_api_key       = "tu-api-key-de-nvidia"
secret_key           = "una-clave-jwt-segura-de-32-bytes-o-mas"
google_client_id     = "tu-client-id.apps.googleusercontent.com"
google_client_secret = "tu-client-secret"

frontend_url         = "https://www.tu-dominio.com"
backend_cors_origins = "[\"https://www.tu-dominio.com\"]"
```

## Despliegue inicial (manual)

1. **Artifact Registry primero**, porque Cloud Run necesita una imagen existente:

   ```bash
   terraform init && terraform validate
   terraform apply -target=google_artifact_registry_repository.backend
   gcloud auth configure-docker europe-west1-docker.pkg.dev
   ```

2. **Construir y subir las dos imágenes** desde `src/backend/` (un solo `Dockerfile`, parametrizado):

   ```bash
   cd ../backend
   REG=europe-west1-docker.pkg.dev/TU_PROJECT_ID/travel-ai-images
   docker build --build-arg SERVICE=core_api -t $REG/core-api:latest .
   docker build --build-arg SERVICE=ai_api   -t $REG/ai-api:latest .
   docker push $REG/core-api:latest && docker push $REG/ai-api:latest
   ```

   Alternativa sin construir: copia las que publica CI en GHCR.
   `docker buildx imagetools create -t $REG/core-api:latest ghcr.io/manupm87/travel-ai-world/core-api:latest`

3. **El resto de la infraestructura**:

   ```bash
   cd ../infra/gcp
   terraform plan && terraform apply
   terraform output core_api_url ai_api_url
   ```

   El `entrypoint.sh` de `core_api` ejecuta las migraciones de Alembic al arrancar. `ai_api` no tiene migraciones.

## Despliegue desde CI

`.github/workflows/deploy-backend.yml` (manual, `workflow_dispatch`) copia las imágenes de GHCR a Artifact Registry y ejecuta `terraform plan` (o `apply` si se marca la casilla). Requiere:

- Un **backend remoto de estado** (bucket GCS) configurado en `versions.tf`.
- Secretos del repositorio: `GCP_PROJECT_ID`, `GCP_WORKLOAD_IDENTITY_PROVIDER`, `GCP_SERVICE_ACCOUNT` y los `TF_VAR_*` listados en la cabecera del workflow.

## Frontend

```bash
cd src/frontend
export NEXT_PUBLIC_API_URL="$(cd ../infra/gcp && terraform output -raw core_api_url)"
export NEXT_PUBLIC_AI_API_URL="$(cd ../infra/gcp && terraform output -raw ai_api_url)"
npm run build
```

Registra el dominio del frontend en Google OAuth y mantén `frontend_url` y `backend_cors_origins` sincronizados con él.

## Migración desde la versión de un solo servicio

Si ya tenías desplegado el antiguo `${name_prefix}-backend`, el `plan` mostrará su destrucción y la creación de `-core-api` y `-ai-api`. Cloud SQL, la red y los secretos no cambian. Actualiza el frontend con las dos URLs nuevas.

## Secretos y estado

- No subas `terraform.tfvars` ni `*.tfstate`. Sí sube `.terraform.lock.hcl`.
- Las variables `sensitive` acaban en el estado: usa un backend remoto con acceso restringido para trabajo en equipo.

## Comandos habituales

```bash
terraform fmt -recursive
terraform validate
terraform plan
terraform apply
terraform destroy   # requiere deletion_protection = false
```
