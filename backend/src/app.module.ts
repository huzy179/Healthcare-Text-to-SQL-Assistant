import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { DatabaseModule } from './modules/database/database.module';
import { LlmModule } from './modules/llm/llm.module';
import { SqlValidatorModule } from './modules/sql-validator/sql-validator.module';
import { TextToSqlModule } from './modules/text-to-sql/text-to-sql.module';

@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true }),
    DatabaseModule,
    LlmModule,
    SqlValidatorModule,
    TextToSqlModule,
  ],
})
export class AppModule {}
