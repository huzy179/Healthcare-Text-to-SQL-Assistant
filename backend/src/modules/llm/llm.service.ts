import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';

@Injectable()
export class LlmService {
  constructor(private readonly config: ConfigService) {}

  async generateSql(question: string, schema: string): Promise<string> {
    const baseUrl = this.config.get<string>('VLLM_BASE_URL');
    const model = this.config.get<string>('VLLM_MODEL');

    if (!baseUrl || !model) {
      return this.fallbackSql(question);
    }

    const response = await fetch(`${baseUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.config.get<string>('VLLM_API_KEY') ?? 'local'}`,
      },
      body: JSON.stringify({
        model,
        temperature: 0,
        messages: [
          {
            role: 'system',
            content:
              'You generate one safe PostgreSQL SELECT query. Return SQL only.',
          },
          {
            role: 'user',
            content: `Schema:\n${schema}\n\nQuestion:\n${question}\n\nSQL:`,
          },
        ],
      }),
    });

    if (!response.ok) {
      throw new Error(`LLM request failed with status ${response.status}`);
    }

    const data = (await response.json()) as {
      choices?: Array<{ message?: { content?: string } }>;
    };

    return data.choices?.[0]?.message?.content?.trim() ?? '';
  }

  private fallbackSql(question: string): string {
    const normalized = question.toLowerCase();

    if (normalized.includes('giới tính') || normalized.includes('gender')) {
      return 'SELECT gender, COUNT(*) AS total FROM patients GROUP BY gender ORDER BY total DESC;';
    }

    if (normalized.includes('bệnh') || normalized.includes('condition')) {
      return 'SELECT description, COUNT(*) AS total FROM conditions GROUP BY description ORDER BY total DESC LIMIT 10;';
    }

    return 'SELECT COUNT(*) AS total_patients FROM patients;';
  }
}
