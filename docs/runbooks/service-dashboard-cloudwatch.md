# Service dashboard in CloudWatch

The native `travel-ai-service-metrics` dashboard complements the Grafana business
metrics for demos. Its name uses `name_prefix`; the name above is the default prefix's.
It reads native metrics only: no middleware, custom metrics or log queries. Per-route
latency and 5xx and cold starts are in the [access logs dashboard](access-logs-cloudwatch.md);
DynamoDB and CloudFront in the [infrastructure dashboard](infrastructure-dashboard-cloudwatch.md).

## Create and open

The resource lives in `infra/aws/dashboard.tf`; its body in
`infra/aws/metric/cloudwatch/service_metrics.json.tftpl`. Terraform reads the real names
of the functions and of the stage from the existing resources. If the dashboard already
exists in the production account, import that same dashboard into the production state
(command below) before managing it with Terraform. Do not create a second dashboard
under another name.

From `infra/aws`, with the AWS session and the Terraform backend set up as in the
[infrastructure runbook](../../infra/aws/README.md):

```bash
terraform plan -out=service-dashboard.tfplan
terraform show service-dashboard.tfplan
# apply only a reviewed plan: do not deploy changes unrelated to the dashboard
terraform apply service-dashboard.tfplan
terraform output -raw service_dashboard_url
```

The plan
must add only `aws_cloudwatch_dashboard.service[0]`. If other changes show up, resolve them
before applying. Do not change the Lambda images to create the dashboard.
`service_dashboard_enabled=false` removes it through a later plan without deleting the
source metrics or touching the applications.

It can also be created from CloudWatch → Dashboards → Create dashboard by pasting the
rendered JSON into Actions → View/edit source. The `.tftpl` template needs its five
variables resolved before pasting. If you create it by hand, import it into Terraform
before the next apply, with the same name and configuration:

```bash
terraform import 'aws_cloudwatch_dashboard.service[0]' travel-ai-service-metrics
```

Access needs an AWS session with permission to create/view dashboards and read the
metrics. The dashboard stays private in the AWS console.

## What it shows

| Signal | Source and statistic | Scope |
|---|---|---|
| Invocations | Lambda `Invocations`, Sum/min | Each function |
| Duration p50/p95 | Lambda `Duration`, percentiles, ms | Each function, without cold start |
| Execution failures | Lambda `Errors`, Sum/min | Each function; not every HTTP 5xx |
| Throttles | Lambda `Throttles`, Sum/min | Each function |
| Concurrency | Lambda `ConcurrentExecutions`, Maximum/min | Not an exact HTTP gauge |
| Requests/s | API Gateway `Count`, SampleCount / period | Whole stage |
| HTTP 4xx/5xx | API Gateway, Sum/min | Whole stage |
| Latency p50/p95 | API Gateway `Latency`, ms | Whole stage |
| HTTP 5xx (%) | 100 × 5xx / requests per minute | Only when there are requests |

It uses the `FunctionName` and `ApiName, Stage` dimensions. Detailed per-method/route
metrics are not turned on. Names and statistics follow the
[Lambda](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics-types.html)
and [API Gateway](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-metrics-and-dimensions.html)
documentation.

Availability is not inferred from the absence of errors: there is no synthetic probe.
Percentiles need enough traffic. Missing series are not turned into zeros. API Gateway
latency and Lambda duration are not the time to first token nor the whole browser
experience; SSE requests can last the whole stream.

## Demo script

1. Open the dashboard and pick the last 3 hours.
2. Browse trips in the application to generate `core_api` activity.
3. Generate an itinerary to show `ai_api` activity and duration.
4. Wait a few minutes for the metrics to be published and refresh by hand.
5. Explain traffic, duration and concurrency. Show real errors if there are any;
   do not cause production failures or present missing data as success.

If it is empty, check the account, region, dimensions and time window. No traffic does not
prove an outage. Confirm that the calls go through the `prod` stage and that you are not
testing local services.

## Cost

It reuses native metrics. No custom metrics, alarms, probes, detailed API Gateway metrics
or Logs Insights scans are created. The dashboard holds 19 metric references, under the
50 per dashboard of the free tier AWS publishes (up to 3 custom dashboards a month).
Before adding more, check the account's usage and the
[CloudWatch pricing](https://aws.amazon.com/cloudwatch/pricing/). A zero total bill is not
guaranteed: the application's normal traffic and the other resources keep their costs.
Keep manual refresh for the demo.
