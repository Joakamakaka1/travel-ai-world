# Infrastructure dashboard in CloudWatch

`travel-ai-infrastructure-metrics` complements the
[service dashboard](service-dashboard-cloudwatch.md). The name derives from
`name_prefix`. The resource lives in `infra/aws/infrastructure_dashboard.tf` and its
body in `infra/aws/metric/cloudwatch/infrastructure_metrics.json.tftpl`.

## Metrics and scope

| Area | Metrics and statistic | Dimensions |
|---|---|---|
| DynamoDB, consumption | ConsumedReadCapacityUnits / ConsumedWriteCapacityUnits, Sum/min | TableName of core and interactions |
| DynamoDB, throttled events | ReadThrottleEvents / WriteThrottleEvents, Sum/min | TableName, and GlobalSecondaryIndexName for GSI1/GSI2 |
| DynamoDB, throttled requests | ThrottledRequests, Sum/min per operation | TableName and Operation |
| CloudFront, traffic | Requests, BytesDownloaded, BytesUploaded, Sum/min | DistributionId and Region=Global |
| CloudFront, errors | 4xxErrorRate / 5xxErrorRate, Average | DistributionId and Region=Global |
| Lambda | 100 × Sum(Errors) / Sum(Invocations) per minute | FunctionName of each service |

CloudFront metrics are queried in `us-east-1`, while DynamoDB and Lambda use the
resources' region. The CloudFront rates already come as percentages: do not multiply
them by a hundred again. The Lambda series are computed only when there are
invocations; with no activity no zero is invented.

The tables use on-demand (pay-per-request) billing. Consumed units are shown per minute,
not as a percentage of a provisioned capacity that does not exist. Consumption is that of
the base tables and does not add the indexes'. Table and GSI throttled events are shown
separately: one event is not the same as one request.

ThrottledRequests covers ten operations: GetItem, PutItem, UpdateItem, DeleteItem,
Query, Scan, BatchGetItem, BatchWriteItem, TransactGetItems and TransactWriteItems. If
the code starts using other APIs, add their dimensions explicitly and recount the
metrics. For batch operations, ThrottledRequests only increments when every operation
in the batch is throttled; the read/write throttle events catch partial throttling.

## Publishing and verification

Terraform reads the table, function and distribution names from the existing resources.
Review the plan before applying, following the [AWS runbook](../../infra/aws/README.md).
Do not deploy changes unrelated to the dashboard.

If the dashboard already exists in the account because it was created from the console,
import it into the same production state before applying, keeping its name:

```bash
terraform import 'aws_cloudwatch_dashboard.infrastructure[0]' travel-ai-infrastructure-metrics
```

Then review the plan and check the `infrastructure_dashboard_url` output.
`infrastructure_dashboard_enabled=false` removes the dashboard through a later plan; it
does not delete the underlying metrics.

In the console, pick three hours and refresh by hand after using the website and the
planner normally. DynamoDB capacity and CloudFront traffic reflect the activity once AWS
publishes the samples. The throttling series can be empty when nothing was throttled;
do not load production to show them. Compare the tables and distribution with the
account's real resources. Lambda errors are execution errors, not every HTTP 5xx.

## Budget

This dashboard holds 45 references to native metrics and turns on no additional
CloudFront metrics, Contributor Insights, alarms, probes, new logs or Logs Insights
queries. Manual refresh; initial range of three hours. Together with the service
dashboard it makes two custom dashboards. AWS publishes a free tier of up to three
dashboards with up to 50 metrics each: check the account's total usage and the current
terms in the [official pricing](https://aws.amazon.com/cloudwatch/pricing/) before adding
more. The project's normal usage keeps its own costs, and billing can lag.

References: [DynamoDB](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/metrics-dimensions.html),
[CloudFront](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/monitoring-using-cloudwatch.html)
and [Lambda](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics-types.html).
