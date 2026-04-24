# ❌ Переполнение контекстного окна (Context Overflow)

> Мигрировано из PROJECT_MEMORY.md v1 | Категория: ОШИБКА

---

## Проблема
При одновременной инъекции KB примеров и длинных текстов (>15000 символов), LM Studio возвращает:
```
"The number of tokens to keep from the initial prompt is greater than the context size"
```

## Причина
Суммарный размер `system prompt + KB examples + document text` превышает контекстное окно модели (4096 токенов для некоторых моделей).

## Решение
Динамически уменьшать `text_limit` если используется KB:
```python
text_limit = 4000 if kb_examples else 15000
```
> ✅ ИСПРАВЛЕНО (2026-04-24)

## Связанная проблема: KiloCode instructions
Маска `./Dlua_Windsurf/**/*.md` в `kilo.json` загружала файл review_changes (~126 КБ, ~170K токенов). Превышало лимит 202K токенов.

**Решение:** В `instructions` включать ТОЛЬКО лёгкие файлы (`./AGENTS_RULES/**/*.md`, ~5 КБ). Тяжёлые логи — читать по запросу.
> ✅ ИСПРАВЛЕНО (2026-04-24)

---

*Дата обнаружения: 2026-04-01*
*Последнее столкновение: 2026-04-07*
