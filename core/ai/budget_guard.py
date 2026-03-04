from .cost_tracker import CostTracker


class BudgetGuard:

    def __init__(self, config):
        self.config = config
        self.tracker = CostTracker()

    def is_allowed(self):
        stats = self.tracker.get_stats()
        limit = self.config.get("daily_credit_limit", 1000)

        return stats["total_calls"] < limit

    def should_downgrade(self):
        stats = self.tracker.get_stats()
        limit = self.config.get("daily_credit_limit", 1000)

        if limit == 0:
            return False

        usage_percent = stats["total_calls"] / limit

        return usage_percent >= 0.8