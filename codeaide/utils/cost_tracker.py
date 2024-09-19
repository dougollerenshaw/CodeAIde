from datetime import datetime


class CostTracker:
    def __init__(self):
        self.cost_log = []
        self.cost_per_1k_tokens = 0.03  # Update this with actual pricing

    def log_request(self, response):
        # The new API doesn't provide direct access to prompt tokens
        # We'll estimate based on the response tokens
        completion_tokens = response.usage.output_tokens
        # Estimate prompt tokens (this is not accurate, but it's a rough estimate)
        estimated_prompt_tokens = completion_tokens // 2
        total_tokens = estimated_prompt_tokens + completion_tokens
        estimated_cost = (total_tokens / 1000) * self.cost_per_1k_tokens

        self.cost_log.append(
            {
                "timestamp": datetime.now(),
                "estimated_prompt_tokens": estimated_prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "estimated_cost": estimated_cost,
            }
        )

    def get_total_cost(self):
        return sum(entry["estimated_cost"] for entry in self.cost_log)

    def print_summary(self):
        total_cost = self.get_total_cost()
        total_tokens = sum(entry["total_tokens"] for entry in self.cost_log)
        print(f"\nTotal estimated cost: ${total_cost:.4f}")
        print(f"Total tokens used: {total_tokens}")
        print(f"Number of API calls: {len(self.cost_log)}")
