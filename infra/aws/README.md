# Infraestructura Terraform para Travel AI World (AWS)

![Terraform](https://img.shields.io/badge/Terraform-1.6%2B-7B42BC?style=for-the-badge&logo=terraform&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-ECS%20Fargate-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-RDS-316192?style=for-the-badge&logo=postgresql&logoColor=white)

Infraestructura de **AWS** para el backend de Travel AI World, que son **dos servicios** (ver [ADR 0001](../../docs/architecture/adr/0001-backend-split.md)):

| Servicio | Imagen | Qué hace | Ruta en el ALB |
|---|---|---|---|
| `core_api` | `core-api` | Google auth, usuarios, trips (CRUD), RDS | todo lo demás (acción por defecto) |
| `ai_api` | `ai-api` | Chat con streaming (NVIDIA) | `/api/v1/ai/*` |

El **Application Load Balancer** hace de API gateway: un solo origen público y enrutado por prefijo. El frontend solo necesita `NEXT_PUBLIC_API_URL`.

## Qué crea Terraform

- VPC, subredes públicas y grupos de seguridad (ALB → ECS:8000 → RDS:5432).
- RDS PostgreSQL privado.
- Dos repositorios ECR: `${name_prefix}-core-api` y `${name_prefix}-ai-api`.
- Secretos en Secrets Manager: `secret-key`, `google-client-id`, `google-client-secret`, `db-password`, `nvidia-api-key`.
- Un clúster ECS y dos servicios Fargate (módulo `modules/ecs_service`), cada uno con su rol de ejecución limitado a **sus** secretos:
  - `core-api`: DB\_\*, `GOOGLE_*`, `SECRET_KEY`.
  - `ai-api`: `NVIDIA_API_KEY`, `SECRET_KEY`, `CORE_API_URL` (la URL del ALB).
- ALB con dos target groups, healthchecks en `/api/v1/health/` y `/api/v1/ai/health/`, y `idle_timeout` de 300 s para las respuestas en streaming.

`SECRET_KEY` es el mismo secreto para los dos: `ai_api` verifica los JWT que emite `core_api`.

## Requisitos

- Cuenta de AWS, AWS CLI autenticada, Terraform >= 1.6, Docker.

```bash
aws configure           # o variables AWS_PROFILE / AWS_ACCESS_KEY_ID...
aws sts get-caller-identity
```

## Configuración

```bash
cd infra/aws
cp terraform.tfvars.example terraform.tfvars
```

```hcl
region         = "eu-west-1"
name_prefix    = "travel-ai"
core_api_image = "123456789012.dkr.ecr.eu-west-1.amazonaws.com/travel-ai-core-api:latest"
ai_api_image   = "123456789012.dkr.ecr.eu-west-1.amazonaws.com/travel-ai-ai-api:latest"

db_password          = "una-password-segura"
nvidia_api_key       = "tu-api-key-de-nvidia"
secret_key           = "una-clave-jwt-segura-de-32-bytes-o-mas"
google_client_id     = "tu-client-id.apps.googleusercontent.com"
google_client_secret = "tu-client-secret"

frontend_url         = "https://www.tu-dominio.com"
backend_cors_origins = "[\"https://www.tu-dominio.com\"]"
```

## Despliegue inicial (manual)

1. **ECR primero**:

   ```bash
   terraform init && terraform validate
   terraform apply -target=aws_ecr_repository.services
   ```

2. **Construir y subir las dos imágenes** desde `src/backend/`:

   ```bash
   AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
   REG="$AWS_ACCOUNT_ID.dkr.ecr.eu-west-1.amazonaws.com"
   aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin "$REG"

   cd ../backend
   docker build --build-arg SERVICE=core_api -t $REG/travel-ai-core-api:latest .
   docker build --build-arg SERVICE=ai_api   -t $REG/travel-ai-ai-api:latest .
   docker push $REG/travel-ai-core-api:latest && docker push $REG/travel-ai-ai-api:latest
   ```

   Alternativa sin construir: copia las que publica CI en GHCR con `docker buildx imagetools create`.

3. **El resto de la infraestructura**:

   ```bash
   cd ../infra/aws
   terraform plan && terraform apply
   terraform output -raw backend_url
   ```

   `core_api` ejecuta las migraciones de Alembic al arrancar.

## Despliegue desde CI

`.github/workflows/deploy-backend.yml` (manual) copia las imágenes de GHCR a ECR y ejecuta `terraform plan` (o `apply`). Requiere un **backend remoto de estado** (S3) en `versions.tf` y los secretos `AWS_REGION`, `AWS_ROLE_TO_ASSUME` (OIDC) y los `TF_VAR_*` listados en la cabecera del workflow.

## Frontend

```bash
cd src/frontend
export NEXT_PUBLIC_API_URL="$(cd ../infra/aws && terraform output -raw backend_url)"
npm run build
```

Para producción añade un certificado ACM y un listener HTTPS al ALB antes de publicar el dominio.

## Migración desde la versión de un solo servicio

El `plan` destruirá el servicio `${name_prefix}-backend`, su target group, su repositorio ECR y sus roles, y creará los recursos `-core-api` y `-ai-api`. RDS, la red y los secretos no cambian.

## Secretos y estado

- No subas `terraform.tfvars` ni `*.tfstate`. Sí sube `.terraform.lock.hcl`.
- Las variables `sensitive` acaban en el estado: usa un backend remoto (S3 + bloqueo) para trabajo en equipo.
