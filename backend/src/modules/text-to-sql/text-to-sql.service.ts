import { BadRequestException, Injectable } from '@nestjs/common';
import { DatabaseService } from '../database/database.service';
import { LlmService } from '../llm/llm.service';
import { SqlValidatorService } from '../sql-validator/sql-validator.service';

@Injectable()
export class TextToSqlService {
  constructor(
    private readonly database: DatabaseService,
    private readonly llm: LlmService,
    private readonly validator: SqlValidatorService,
  ) {}

  async answer(question: string) {
    if (!question?.trim()) {
      throw new BadRequestException('Question is required.');
    }

    const startedAt = Date.now();
    const generatedSql = await this.llm.generateSql(question, this.schemaPrompt());
    const sql = this.validator.validate(generatedSql);
    const rows = await this.database.query(sql);

    return {
      question,
      sql,
      rows,
      row_count: rows.length,
      execution_time_ms: Date.now() - startedAt,
      explanation: 'Query đã được validate và thực thi trên PostgreSQL.',
    };
  }

  private schemaPrompt(): string {
    return [
      'patients(id, birthdate, deathdate, gender, city, state, first_name, last_name)',
      'encounters(id, start, stop, patient, organization, provider, payer, encounterclass, description, total_claim_cost)',
      'conditions(start, stop, patient, encounter, code, description)',
      'medications(start, stop, patient, payer, encounter, code, description, totalcost)',
      'observations(date, patient, encounter, category, code, description, value, units, type)',
      'procedures(start, stop, patient, encounter, code, description, base_cost)',
      'claims(id, patientid, providerid, servicedate, status1, outstanding1)',
      'providers(id, organization, name, gender, speciality)',
      'organizations(id, name, city, state, revenue, utilization)',
      'payers(id, name, ownership, amount_covered, amount_uncovered, revenue)',
      'relationships: encounters.patient = patients.id; conditions.patient = patients.id; conditions.encounter = encounters.id; medications.patient = patients.id; medications.encounter = encounters.id; observations.patient = patients.id; procedures.patient = patients.id',
    ].join('\n');
  }
}
