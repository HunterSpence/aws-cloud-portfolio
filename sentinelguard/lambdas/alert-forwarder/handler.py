"""SentinelGuard — Alert Forwarder Lambda.

Formats security findings from GuardDuty, Config, and SecurityHub
into human-readable messages and forwards to Slack and email.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any
from urllib.request import Request, urlopen

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ses = boto3.client("ses")

SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK_URL", "")
ALERT_EMAIL = os.environ.get("ALERT_EMAIL", "")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "security@example.com")

SEVERITY_EMOJI = {
    "CRITICAL": "🔴",
    "HIGH": "🟠",
    "MEDIUM": "🟡",
    "LOW": "🔵",
    "INFORMATIONAL": "⚪",
}


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Format and forward security alerts."""
    source = event.get("source", "unknown")
    detail = event.get("detail", {})

    alert = _format_alert(source, detail)

    if SLACK_WEBHOOK:
        _send_slack(alert)
    if ALERT_EMAIL:
        _send_email(alert)

    return {"statusCode": 200, "alert": alert["title"]}


def _format_alert(source: str, detail: dict) -> dict[str, str]:
    """Format a security finding into a standardized alert."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    if "guardduty" in source:
        severity_num = detail.get("severity", 0)
        severity = "CRITICAL" if severity_num >= 8 else "HIGH" if severity_num >= 7 else "MEDIUM" if severity_num >= 4 else "LOW"
        return {
            "title": f"GuardDuty: {detail.get('title', 'Unknown Finding')}",
            "severity": severity,
            "source": "GuardDuty",
            "description": detail.get("description", "No description"),
            "resource": json.dumps(detail.get("resource", {}), indent=2, default=str)[:500],
            "time": now,
            "account": detail.get("accountId", "unknown"),
            "region": detail.get("region", "unknown"),
        }

    elif "config" in source:
        return {
            "title": f"Config: {detail.get('configRuleName', 'Unknown Rule')} — NON_COMPLIANT",
            "severity": "MEDIUM",
            "source": "AWS Config",
            "description": f"Resource {detail.get('resourceId')} is non-compliant with {detail.get('configRuleName')}",
            "resource": f"{detail.get('resourceType', '')} / {detail.get('resourceId', '')}",
            "time": now,
            "account": detail.get("awsAccountId", "unknown"),
            "region": detail.get("awsRegion", "unknown"),
        }

    else:
        findings = detail.get("findings", [{}])
        f = findings[0] if findings else {}
        return {
            "title": f"SecurityHub: {f.get('Title', 'Unknown')}",
            "severity": f.get("Severity", {}).get("Label", "MEDIUM"),
            "source": "SecurityHub",
            "description": f.get("Description", "No description")[:300],
            "resource": str(f.get("Resources", []))[:500],
            "time": now,
            "account": f.get("AwsAccountId", "unknown"),
            "region": f.get("Region", "unknown"),
        }


def _send_slack(alert: dict[str, str]) -> None:
    """Send formatted alert to Slack webhook."""
    emoji = SEVERITY_EMOJI.get(alert["severity"], "⚪")
    blocks = {
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": f"{emoji} {alert['title']}"}},
            {"type": "section", "fields": [
                {"type": "mrkdwn", "text": f"*Severity:* {alert['severity']}"},
                {"type": "mrkdwn", "text": f"*Source:* {alert['source']}"},
                {"type": "mrkdwn", "text": f"*Account:* {alert['account']}"},
                {"type": "mrkdwn", "text": f"*Region:* {alert['region']}"},
            ]},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"```{alert['description']}```"}},
            {"type": "context", "elements": [{"type": "mrkdwn", "text": f"🕐 {alert['time']}"}]},
        ]
    }

    try:
        req = Request(SLACK_WEBHOOK, data=json.dumps(blocks).encode(), headers={"Content-Type": "application/json"})
        urlopen(req, timeout=10)
        logger.info("Slack alert sent")
    except Exception as e:
        logger.error(f"Slack send failed: {e}")


def _send_email(alert: dict[str, str]) -> None:
    """Send alert via SES."""
    emoji = SEVERITY_EMOJI.get(alert["severity"], "")
    try:
        ses.send_email(
            Source=SENDER_EMAIL,
            Destination={"ToAddresses": [ALERT_EMAIL]},
            Message={
                "Subject": {"Data": f"{emoji} SentinelGuard: {alert['title']}"},
                "Body": {"Text": {"Data": (
                    f"Severity: {alert['severity']}\n"
                    f"Source: {alert['source']}\n"
                    f"Account: {alert['account']}\n"
                    f"Region: {alert['region']}\n"
                    f"Time: {alert['time']}\n\n"
                    f"Description:\n{alert['description']}\n\n"
                    f"Resource:\n{alert['resource']}"
                )}},
            },
        )
        logger.info("Email alert sent")
    except Exception as e:
        logger.error(f"Email send failed: {e}")
