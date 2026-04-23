# ✅ Few-Shot Prompting через Knowledge Base

> Мигрировано из PROJECT_MEMORY.md v1 | Категория: НАВЫК

---

## Суть
Выделен `knowledge_base.json` с эталонными ответами. Эталоны пробрасываются в `role: system` как справочник, что исключает ошибки структуры (переход Zero-Shot → Few-Shot).

## Результат
**+44.7 п.п.** точности (с 30.4% до 75.1%). По `document_type`: **+73 п.п.**

## Реализация
```python
# Правильно: эталоны как справочник в system
messages = [
    {"role": "system", "content": PROMPT_SYSTEM + examples_text},
    {"role": "user", "content": text}
]

# НЕПРАВИЛЬНО: фейковые диалоги
messages = [
    {"role": "user", "content": "Извлеки из: Документ Х..."},
    {"role": "assistant", "content": '{"customer": "ООО Ромашка"}'},  # ГАЛЛЮЦИНАЦИЯ!
    {"role": "user", "content": real_text}
]
```

## Подбор примеров
Метод `_get_kb_matching_entries(filename, top_n)` — находит **топ-2** наиболее похожие записи из KB по score, а не первые 3 записи.

---

*Дата открытия: 2026-03-30*
*Подтверждено бенчмарком: 2026-04-01*

### ✅ [2026-04-11 22:00] [Antigravity]
Создан строгий system prompt (.agent/instructions.md) с автоматическим Check-in/Check-out
> ⚠️ УСТАРЕЛО (2026-04-23): Путь .agent/instructions.md больше не основной, используется AGENT_PROTOCOL.md в корне согласно новой структуре.
