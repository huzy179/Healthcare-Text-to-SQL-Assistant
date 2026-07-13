import json
import urllib.request


class LlmClient:
    def __init__(
        self,
        base_url: str | None,
        model: str | None,
        api_key: str,
        prompt_template: str,
        schema_context: str,
    ) -> None:
        self.base_url = base_url
        self.model = model
        self.api_key = api_key
        self.prompt_template = prompt_template
        self.schema_context = schema_context

    def generate_sql(self, question: str) -> str:
        if not self.base_url or not self.model:
            return self.fallback_sql(question)

        prompt = self.prompt_template.replace("{{schema}}", self.schema_context.strip()).replace(
            "{{question}}",
            question.strip(),
        )
        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {
                    "role": "system",
                    "content": "You generate safe PostgreSQL SELECT queries. Return SQL only.",
                },
                {"role": "user", "content": prompt},
            ],
        }
        request = urllib.request.Request(
            self.base_url.rstrip("/") + "/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()

    def fallback_sql(self, question: str) -> str:
        normalized = question.lower()
        if "giới tính" in normalized or "gender" in normalized:
            return "SELECT gender, COUNT(*) AS total FROM patients GROUP BY gender ORDER BY total DESC;"
        if "diabetes" in normalized:
            return "SELECT COUNT(DISTINCT patient) AS total_patients FROM conditions WHERE description ILIKE '%diabetes%';"
        if "bệnh" in normalized or "chẩn đoán" in normalized or "condition" in normalized:
            return "SELECT description, COUNT(*) AS total FROM conditions GROUP BY description ORDER BY total DESC LIMIT 10;"
        if "lượt khám" in normalized or "encounter" in normalized:
            return "SELECT encounterclass, COUNT(*) AS total_encounters FROM encounters GROUP BY encounterclass ORDER BY total_encounters DESC;"
        return "SELECT COUNT(*) AS total_patients FROM patients;"
