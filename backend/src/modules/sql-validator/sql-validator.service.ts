import { BadRequestException, Injectable } from '@nestjs/common';

const BLOCKED_KEYWORDS = [
  'insert',
  'update',
  'delete',
  'drop',
  'alter',
  'create',
  'truncate',
  'copy',
  'grant',
  'revoke',
];

@Injectable()
export class SqlValidatorService {
  validate(sql: string): string {
    const normalized = sql.trim().replace(/;+\s*$/, '');
    const lowered = normalized.toLowerCase();

    if (!lowered.startsWith('select')) {
      throw new BadRequestException('Only SELECT queries are allowed.');
    }

    if (lowered.includes(';')) {
      throw new BadRequestException('Multiple SQL statements are not allowed.');
    }

    for (const keyword of BLOCKED_KEYWORDS) {
      if (new RegExp(`\\b${keyword}\\b`, 'i').test(normalized)) {
        throw new BadRequestException(`Blocked SQL keyword: ${keyword}`);
      }
    }

    return this.addDefaultLimit(normalized);
  }

  private addDefaultLimit(sql: string): string {
    const lowered = sql.toLowerCase();

    if (lowered.includes(' limit ')) {
      return sql;
    }

    if (/\bcount\s*\(|\bsum\s*\(|\bavg\s*\(|\bmin\s*\(|\bmax\s*\(/i.test(sql)) {
      return sql;
    }

    return `${sql} LIMIT 100`;
  }
}
