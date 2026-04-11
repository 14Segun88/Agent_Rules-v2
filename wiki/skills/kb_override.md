# ✅ KB Override

> Мигрировано из PROJECT_MEMORY.md v1 | Категория: НАВЫК

---

## Суть
Если в KB найдено совпадение по названию документа (>60%), поля `purpose`, `content_summary` и `document_type` берутся напрямую из KB, исключая перефразирование LLM.

## Механизм
```python
def _get_kb_direct_fields(filename: str) -> dict:
    """Возвращает поля из KB если score > 60%."""
    score = _calculate_score(filename, kb_title)
    if score > 0.60:
        return {
            "purpose": kb_entry["purpose"],
            "content_summary": kb_entry["content_summary"],
            "document_type": kb_entry["document_type"]
        }
    return {}
```

## Визуализация на сайте
| Badge | Условие |
|-------|---------|
| ✓ KB Override | score ≥ 90% |
| ⚠ KB Match | score 60-89% |
| ✗ Regex | score < 60% |

## Критически важно
- Метод `_calculate_score()` должен использоваться ЕДИНООБРАЗНО во всех местах (KB Override, Semantic Matching, подбор примеров).
- Раньше `_get_kb_direct_fields()` пересчитывал score БЕЗ boost'ов → override не срабатывал. Это было исправлено.

---

*Дата создания: 2026-04-07*
