import { Module } from '@nestjs/common';
import { DatabaseModule } from '../database/database.module';
import { LlmModule } from '../llm/llm.module';
import { SqlValidatorModule } from '../sql-validator/sql-validator.module';
import { TextToSqlController } from './text-to-sql.controller';
import { TextToSqlService } from './text-to-sql.service';

@Module({
  imports: [DatabaseModule, LlmModule, SqlValidatorModule],
  controllers: [TextToSqlController],
  providers: [TextToSqlService],
})
export class TextToSqlModule {}
