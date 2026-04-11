# 🔴 Актуальный статус проекта

`[2026-04-11 22:00] [Агент: Antigravity] СТАТУС: Инициализация AGENTS_RULES v2. СЛЕДУЮЩИЙ ШАГ: Миграция знаний из PROJECT_MEMORY.md v1`

---

## Текущая задача
Миграция с AGENTS_RULES v1 → v2 (гибридная система Wiki + Handover Protocol).

## Рабочая среда
- **LLM API:** `http://192.168.47.22:1234/v1` (LM Studio)
- **Модели:** `gemma-4-31b-it` (default), `ministral-3-14b-reasoning` (для ТЗ/ТУ)
- **KB:** `knowledge_base.json` (57 записей, Пакет 1 полностью)
- **Веб-сервер:** http://localhost:5005 (v6)

## Блокеры
1. **[КРИТИЧНО]** Нужны эталоны KB для Пакета 2 (СОШ 10 / ИГДИ)
2. **[ВЫСОКИЙ]** model_router.py — маршрутизация Gemma/Mistral

## Последние изменения
- Fair Benchmark завершён: Gemma 77.5% vs Mistral 68.2% (семантика)
- Cross-model согласие: 98.3% на Пакете 2
- KB: 57 записей, 100% покрытие Пакета 1
