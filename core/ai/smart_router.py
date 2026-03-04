import time
from .provider_router import ProviderRouter
from .cost_tracker import CostTracker
from .budget_guard import BudgetGuard


class SmartRouter:

    def __init__(self, config):
        self.config = config
        self.router = ProviderRouter(config)
        self.cost_tracker = CostTracker()
        self.guard = BudgetGuard(config)

    def generate(self, system_prompt, user_prompt, task_type="general"):

        if not self.guard.is_allowed():
            return "⚠ Daily AI limit reached."

        model = self._select_model(task_type)

        if self.guard.should_downgrade():
            model = "gpt-4o-mini"

        start = time.time()

        try:
            response = self.router.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model_override=model
            )

            duration = round(time.time() - start, 3)

            self.cost_tracker.track(
                model=model,
                task_type=task_type,
                duration=duration
            )

            return response

        except Exception as e:
            print("SmartRouter error:", e)
            return "⚠ AI temporarily unavailable."

    def _select_model(self, task_type):

        if task_type == "niche":
            return "gpt-4.1"

        return self.config.get("model", "gpt-4o")