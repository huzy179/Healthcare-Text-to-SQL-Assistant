import { Body, Controller, Post } from '@nestjs/common';
import { QueryDto } from './dto/query.dto';
import { TextToSqlService } from './text-to-sql.service';

@Controller('text-to-sql')
export class TextToSqlController {
  constructor(private readonly service: TextToSqlService) {}

  @Post('query')
  async query(@Body() dto: QueryDto) {
    return this.service.answer(dto.question);
  }
}
