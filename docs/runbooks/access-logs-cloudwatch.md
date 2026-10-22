# HTTP access logs and dashboard

The `travel-ai-access-logs` dashboard complements the
[service](service-dashboard-cloudwatch.md) and
[infrastructure](infrastructure-dashboard-cloudwatch.md) dashboards. Its name derives from
`name_prefix`; the resource and the switch live in `infra/aws/access_logs.tf`.
The [decision](../architecture/adr/0035-structured-http-access-logs.md) documents the
semantics and the privacy boundary.

## Enabling and rolling back

`ACCESS_LOG_ENABLED` is false by default in `CommonSettings`. For local testing, set
`ACCESS_LOG_ENABLED=true` in the service's `.env` and restart it.
Terraform passes `ACCESS_LOG_ENABLED` to both Lambdas from `access_logs_enabled`
(true by default). The deployed images must contain the access-log middleware: changing
only the environment of an older image produces no records.

Follow the [deploy runbook](deploy.md): build the images from the reviewed commit, review
the plan and deploy. Do not apply changes unrelated to this one. Check
`access_logs_dashboard_url` and real traffic before calling a production rollout done.
No historical records are created.

To stop the extra ingestion, set `access_logs_enabled=false`, review the plan and deploy
the updated environment. Existing records stay subject to their group's retention.
`access_logs_dashboard_enabled=false` removes only the dashboard once the plan is applied;
on its own it does not stop the application logs. While the observer is active, the
entrypoint turns off Uvicorn's access log so that raw URLs and query strings are not
logged twice.

## Contract and limits

One log line with the `access_log=` prefix followed by compact JSON, version 1.
The usual logging format may add the date, level and logger name before the marker.
Do not parse the whole line as JSON: extract the payload first.

| Field | Meaning |
|---|---|
| route | Router template; `__unmatched__` for routes that do not resolve |
| method | Standard HTTP method; unknown ones are grouped |
| status | Status sent, or 500 if it fails before the response starts |
| duration_ms | Time until the terminal ASGI message is ready |
| request_id | Validated Lambda invocation UUID; null when not available |
| cold_start | First Lambda request seen by the process; does not measure Init Duration |
| outcome | `response_ready` or `interrupted` |
| version | 1 |

It carries no full URL, parameters, headers, body, identity, email or token.
The Lambda context contributes only the validated UUID; it is never logged whole. This
privacy boundary applies to these access lines only: it does not redefine other existing
audit or exception logs.

The record is emitted before the last body/trailers are handed to the server, so that
Lambda does not freeze the work after responding. For SSE it includes the time spent
generating the stream, without measuring final delivery to the browser or the first
token. A failure sending the terminal message can happen after the `response_ready`
record: that value means the response was ready, not that the client received it.
An earlier interruption keeps the status already sent; an interrupted 200 response is
not counted as a 5xx. Internal readiness probes without an invocation context do not
consume the first-Lambda-request marker.

## Queries and verification

Each widget in the JSON at `infra/aws/metric/cloudwatch/access_logs.json.tftpl` holds a
query you can copy. In Logs Insights, select the service's group explicitly and leave out
the widget's SOURCE line when using the console's group selector.

Route summary for a selected group:

```text
filter @message like /access_log=/
| parse @message "access_log=*" as payload
| fields jsonParse(payload) as a
| filter a.version = 1
| stats count(*) as peticiones,
    sum(if(a.status >= 500 and a.status < 600, 1, 0)) as respuestas_5xx,
    pct(a.duration_ms, 95) as p95_ms by a.method, a.route
| sort peticiones desc
| limit 50
```

Lambda initialisations from the runtime report:

```text
filter @type = "REPORT"
| stats count(*) as invocaciones_reportadas,
    count(@initDuration) as arranques_con_init,
    pct(@initDuration, 95) as init_p95_ms
```

REPORT/Init Duration is independent of the access events and is available even before the
middleware is deployed. With no samples, the percentiles stay empty. To verify access
records, use the application normally and query a short window; check that routes appear
as templates and that no concrete identifiers show up. An empty table before the
deployment proves neither an outage nor the absence of errors. The summaries show the 50
busiest routes; past that limit they do not cover every route.

## Cost

The dashboard runs six queries: HTTP summary, traffic/5xx per 5 minutes and REPORT
initialisation, for each service. It opens on a three-hour window by default, without
auto-refresh. Every open or refresh scans the group's data in that window; the
`access_log=` filter does not avoid scanning the group's other messages. Close the tab
after use and do not turn on periodic refresh.

The existing groups are kept, with their default 14-day retention. There are no custom
metrics, metric filters, agents, exporters or alarms. The dashboards and logs free tier
is shared with the rest of the account; it does not guarantee zero cost. Ingestion and
queries are billed at the [current regional price](https://aws.amazon.com/cloudwatch/pricing/).

References: [Logs Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax.html),
[JSON and conditional functions](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax-operations-functions.html)
and [widget format](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Dashboard-Body-Structure.html).
