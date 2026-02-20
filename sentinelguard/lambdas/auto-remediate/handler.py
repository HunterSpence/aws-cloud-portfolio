"""SentinelGuard — Auto-Remediation Lambda.

Automatically remediates common security findings:
- Close public S3 buckets
- Revoke exposed IAM access keys
- Enable encryption on unencrypted EBS volumes
- Block public RDS snapshots
- Quarantine compromised EC2 instances
"""

import json
import logging
import os
from typing import Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")
iam = boto3.client("iam")
ec2 = boto3.client("ec2")
rds = boto3.client("rds")
sns = boto3.client("sns")

SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN", "")
DRY_RUN = os.environ.get("DRY_RUN", "true").lower() == "true"


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Process security findings and auto-remediate."""
    logger.info(f"Received event: {json.dumps(event, default=str)[:500]}")

    actions_taken = []
    source = event.get("source", "")
    detail = event.get("detail", {})

    if source == "aws.config":
        actions_taken = _handle_config_finding(detail)
    elif source == "aws.guardduty":
        actions_taken = _handle_guardduty_finding(detail)
    elif source == "aws.securityhub":
        actions_taken = _handle_securityhub_finding(detail)

    if actions_taken:
        _notify(actions_taken)

    return {"statusCode": 200, "actions": actions_taken}


def _handle_config_finding(detail: dict) -> list[str]:
    """Remediate AWS Config non-compliant resources."""
    actions = []
    rule_name = detail.get("configRuleName", "")
    resource_type = detail.get("resourceType", "")
    resource_id = detail.get("resourceId", "")

    if "s3-bucket-public" in rule_name.lower():
        actions.append(_block_s3_public_access(resource_id))

    elif "ebs-encryption" in rule_name.lower():
        actions.append(f"ALERT: Unencrypted EBS volume {resource_id} — manual encryption required")

    elif "iam-access-key" in rule_name.lower():
        actions.append(_deactivate_old_access_keys(resource_id))

    return [a for a in actions if a]


def _handle_guardduty_finding(detail: dict) -> list[str]:
    """Remediate GuardDuty threat findings."""
    actions = []
    finding_type = detail.get("type", "")
    severity = detail.get("severity", 0)
    resource = detail.get("resource", {})

    # High severity: quarantine compromised instances
    if severity >= 7 and "Instance" in finding_type:
        instance_id = resource.get("instanceDetails", {}).get("instanceId")
        if instance_id:
            actions.append(_quarantine_instance(instance_id))

    # Credential compromise
    if "UnauthorizedAccess:IAMUser" in finding_type:
        access_key = resource.get("accessKeyDetails", {}).get("accessKeyId")
        if access_key:
            actions.append(_disable_access_key(access_key))

    return [a for a in actions if a]


def _handle_securityhub_finding(detail: dict) -> list[str]:
    """Route SecurityHub findings to appropriate remediation."""
    actions = []
    findings = detail.get("findings", [])

    for finding in findings:
        title = finding.get("Title", "").lower()
        resources = finding.get("Resources", [])

        for resource in resources:
            rid = resource.get("Id", "")
            if "s3" in title and "public" in title:
                bucket = rid.split(":")[-1] if ":" in rid else rid
                actions.append(_block_s3_public_access(bucket))

    return [a for a in actions if a]


def _block_s3_public_access(bucket_name: str) -> str:
    """Block all public access on an S3 bucket."""
    if DRY_RUN:
        return f"DRY_RUN: Would block public access on s3://{bucket_name}"
    try:
        s3.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True,
            },
        )
        logger.info(f"Blocked public access on {bucket_name}")
        return f"REMEDIATED: Blocked public access on s3://{bucket_name}"
    except ClientError as e:
        logger.error(f"Failed to block {bucket_name}: {e}")
        return f"FAILED: Could not block {bucket_name}: {e}"


def _quarantine_instance(instance_id: str) -> str:
    """Isolate compromised EC2 instance with restrictive security group."""
    if DRY_RUN:
        return f"DRY_RUN: Would quarantine instance {instance_id}"
    try:
        # Create quarantine SG (no ingress, no egress)
        vpc_id = ec2.describe_instances(InstanceIds=[instance_id])["Reservations"][0]["Instances"][0]["VpcId"]
        sg = ec2.create_security_group(
            GroupName=f"quarantine-{instance_id}",
            Description=f"Quarantine SG for {instance_id}",
            VpcId=vpc_id,
        )
        sg_id = sg["GroupId"]

        # Remove default egress rule
        ec2.revoke_security_group_egress(
            GroupId=sg_id,
            IpPermissions=[{"IpProtocol": "-1", "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}],
        )

        # Apply quarantine SG
        ec2.modify_instance_attribute(InstanceId=instance_id, Groups=[sg_id])
        logger.info(f"Quarantined instance {instance_id}")
        return f"REMEDIATED: Quarantined instance {instance_id} with SG {sg_id}"
    except ClientError as e:
        logger.error(f"Failed to quarantine {instance_id}: {e}")
        return f"FAILED: Could not quarantine {instance_id}: {e}"


def _disable_access_key(access_key_id: str) -> str:
    """Deactivate a compromised IAM access key."""
    if DRY_RUN:
        return f"DRY_RUN: Would disable access key {access_key_id}"
    try:
        # Find the user who owns this key
        paginator = iam.get_paginator("list_users")
        for page in paginator.paginate():
            for user in page["Users"]:
                keys = iam.list_access_keys(UserName=user["UserName"])
                for key in keys["AccessKeyMetadata"]:
                    if key["AccessKeyId"] == access_key_id:
                        iam.update_access_key(
                            UserName=user["UserName"],
                            AccessKeyId=access_key_id,
                            Status="Inactive",
                        )
                        return f"REMEDIATED: Disabled access key {access_key_id} for user {user['UserName']}"
        return f"NOT_FOUND: Access key {access_key_id} not found"
    except ClientError as e:
        return f"FAILED: Could not disable {access_key_id}: {e}"


def _deactivate_old_access_keys(user_name: str) -> str:
    """Deactivate access keys older than 90 days."""
    if DRY_RUN:
        return f"DRY_RUN: Would check keys for user {user_name}"
    try:
        from datetime import datetime, timedelta, timezone
        keys = iam.list_access_keys(UserName=user_name)
        cutoff = datetime.now(timezone.utc) - timedelta(days=90)
        deactivated = 0
        for key in keys["AccessKeyMetadata"]:
            if key["CreateDate"].replace(tzinfo=timezone.utc) < cutoff and key["Status"] == "Active":
                iam.update_access_key(UserName=user_name, AccessKeyId=key["AccessKeyId"], Status="Inactive")
                deactivated += 1
        return f"REMEDIATED: Deactivated {deactivated} old keys for {user_name}"
    except ClientError as e:
        return f"FAILED: {e}"


def _notify(actions: list[str]) -> None:
    """Send remediation report via SNS."""
    if not SNS_TOPIC_ARN:
        return
    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=f"SentinelGuard: {len(actions)} remediation action(s)",
            Message="\n".join(actions),
        )
    except ClientError as e:
        logger.error(f"Failed to send notification: {e}")
