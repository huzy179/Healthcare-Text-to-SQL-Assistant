# Architecture

```text
User
-> Frontend
-> NestJS Backend
-> Schema Service
-> Prompt Builder
-> vLLM or Base LLM
-> SQL Validator
-> PostgreSQL
-> Result Formatter
-> Response
```

The MVP can use a base LLM with schema prompting before any fine-tuning work.
