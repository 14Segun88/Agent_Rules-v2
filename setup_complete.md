# ✅ AGENTS_RULES v2 — Setup Complete

> Дата установки: 2026-04-11 22:00  
> Установлено: Antigravity (Claude Opus 4.6)

---

## Что создано

### Структура
```
AGENTS_RULES-v2/
├── .agent/instructions.md          ✅ System prompt для всех агентов
├── .gitignore                      ✅ Игнорирование __pycache__, PID и т.д.
├── rules_general.md                ✅ Единые правила для всех моделей
├── session_handover.md             ✅ Протокол Check-in / Check-out
├── shared_status.md                ✅ Краткий статус (< 2KB)
├── index.md                        ✅ Карта знаний с ссылками
├── compile.py                      ✅ Компилятор raw → wiki (LLM + rules fallback)
├── watcher.py                      ✅ Следит за raw/ и запускает compile
├── raw/                            ✅ Директория для сырых логов
├── wiki/
│   ├── architecture.md             ✅ Архитектура проекта
│   ├── llm_integration.md          ✅ Настройки LLM
│   ├── benchmark_history.md        ✅ История бенчмарков
│   ├── errors/
│   │   ├── context_overflow.md     ✅ Ошибки контекстного окна
│   │   ├── hallucinations.md       ✅ Галлюцинации моделей
│   │   └── kb_conflicts.md         ✅ Конфликты KB matching
│   └── skills/
│       ├── few_shot_prompting.md   ✅ Техники Few-Shot
│       ├── xml_structure_hints.md  ✅ XML хинты
│       ├── semantic_matching.md    ✅ Семантический matching
│       └── kb_override.md          ✅ KB Override
└── setup_complete.md               ✅ Этот файл
```

### Мигрировано из v1
- Все знания из `PROJECT_MEMORY.md` (45KB, 516 строк) разбиты на **12 тематических страниц**
- Handover Protocol сохранён и улучшен (добавлены git-команды)
- Правило «Успех/Неудача» сохранено
- shared_status.md сокращён до < 2KB

### Автоматизация
- `compile.py` — обрабатывает raw-логи → wiki/ (LLM + rule-based fallback)
- `watcher.py` — мониторит raw/ через watchdog (с debounce 5с)
- Git auto-commit после компиляции

---

## Как подключить

### Antigravity (Windsurf)
Репозиторий уже находится в рабочей директории:
```
/home/segun/CascadeProjects/Перед 0_2/AGENTS_RULES-v2/
```
Antigravity автоматически читает `.agent/instructions.md` при работе с проектом.

### KiloCode (VSCode)
В файле `.kilo/kilo.json` добавить:
```json
{
  "instructions": [
    "./AGENTS_RULES-v2/.agent/instructions.md",
    "./AGENTS_RULES-v2/rules_general.md"
  ]
}
```

### Запуск Watcher
```bash
# Фоновый режим (рекомендуется)
python3 /home/segun/CascadeProjects/Перед\ 0_2/AGENTS_RULES-v2/watcher.py --daemon

# Остановка
python3 /home/segun/CascadeProjects/Перед\ 0_2/AGENTS_RULES-v2/watcher.py --stop
```

---

## Статус: ✅ ГОТОВО К РАБОТЕ
