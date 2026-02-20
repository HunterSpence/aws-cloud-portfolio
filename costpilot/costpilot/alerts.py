"""CostPilot — Budget Alert System."""

import logging
from typing import Any
import boto3
from .config import Config

logger = logging.getLogger(__name__)


class AlertManager:
    def __init__(self, config: Config) -> None:
        self.session = config.get_session()
        self.budgets = self.session.client("budgets")
        self.sts = self.session.client("sts")

    def create_budget_alert(self, budget: float, email: str) -> None:
        account_id = self.sts.get_caller_identity()["Account"]
        thresholds = [50, 75, 90, 100]

        notifications = [
            {
                "Notification": {
                    "NotificationType": "ACTUAL",
                    "ComparisonOperator": "GREATER_THAN",
                    "Threshold": t,
                    "ThresholdType": "PERCENTAGE",
                },
                "Subscribers": [{"SubscriptionType": "EMAIL", "Address": email}],
            }
            for t in thresholds
        ]

        self.budgets.create_budget(
            AccountId=account_id,
            Budget={
                "BudgetName": "CostPilot-Monthly-Budget",
                "BudgetLimit": {"Amount": str(budget), "Unit": "USD"},
                "TimeUnit": "MONTHLY",
                "BudgetType": "COST",
            },
            NotificationsWithSubscribers=notifications,
        )
        logger.info(f"Budget alert created: ${budget}/month with alerts at {thresholds}")
