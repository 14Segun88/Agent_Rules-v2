# 🤖 System Prompt для AI-агентов (AGENTS_RULES v2)

> **КРИТИЧЕСКИ ВАЖНО:** Этот файл является ГЛАВНОЙ инструкцией для ЛЮБОГО AI-агента, работающего с данным проектом. Следуй КАЖДОМУ пункту без исключений.
>
> **ЕЩЁ ОДИН ФАЙЛ:** Также прочитай `../../../AGENT_PROTOCOL.md` — он содержит ОБЯЗАТЕЛЬНЫЙ протокол для всех агентов.

---

## 🔴 АВТОМАТИЧЕСКИЙ CHECK-OUT (ВЫПОЛНИ ПОСЛЕ КАЖДОГО ОТВЕТА)

> ⚠️ **ЭТО НЕ ОПЦИЯ.** После КАЖДОГО ответа пользователю ты ОБЯЗАН записать результат. Даже если задача мелкая или провалена. Следующий агент должен знать что ты делал.

### Шаг 1: Создай лог сессии в `raw/`
Файл `raw/YYYY-MM-DD_HH-MM_<AgentName>.md` с ОБЯЗАТЕЛЬНОЙ структурой:
```markdown
# Лог сессии [Дата] [Агент]

## Задача
Краткое описание задачи.

## Что получилось ✅
- Конкретный результат 1
- Конкретный результат 2 (с метриками если есть)

## Что НЕ получилось ❌
- Если всё по плану — напиши «Нет» (НЕ другие фразы!)
- Проблема 1: описание + почему не вышло

## Технические выводы
- Вывод 1 (для будущих сессий)

## Следующий шаг
Что должен сделать следующий агент.

## Блокеры
- Нет (или описание)
```

### Шаг 2: Обнови shared_status.md
**ЗАМЕНИ** (не дополни!) содержимое `shared_status.md` актуальным кратким статусом (<2KB).

### Шаг 3: Закоммить и запушь
```bash
cd /home/segun/CascadeProjects/Перед\ 0_2/AGENTS_RULES-v2
git add -A
git commit -m "[AgentName] checkout: краткое описание"
git push origin main
```

> Компиляция `raw/ → wiki/` произойдёт автоматически через watcher. Агенту НЕ нужно вручную обновлять wiki.

---

## 🟢 АВТОМАТИЧЕСКИЙ CHECK-IN (выполни НЕМЕДЛЕННО при старте)

При начале ЛЮБОЙ сессии, ПЕРЕД выполнением задачи пользователя, выполни:

### Шаг 1: Синхронизация репозитория
```bash
cd /home/segun/CascadeProjects/Перед\ 0_2/AGENTS_RULES-v2 && git pull --rebase origin main 2>/dev/null || git pull origin main
```

### Шаг 2: Прочитай текущий статус
Прочитай файл `AGENTS_RULES-v2/shared_status.md` — он содержит актуальный статус проекта (< 2KB).

### Шаг 3: Загрузи нужный контекст
На основе задачи пользователя прочитай ТОЛЬКО релевантные wiki-страницы:
- 🏗️ Архитектура → `AGENTS_RULES-v2/wiki/architecture.md`
- 🤖 LLM настройки → `AGENTS_RULES-v2/wiki/llm_integration.md`
- 📊 Бенчмарки → `AGENTS_RULES-v2/wiki/benchmark_history.md`
- ❌ Ошибки → `AGENTS_RULES-v2/wiki/errors/` (найди по теме)
- ✅ Навыки → `AGENTS_RULES-v2/wiki/skills/` (найди по теме)
- 📖 Карта знаний → `AGENTS_RULES-v2/index.md` (обзор всего)

> ⚠️ **НЕ ЧИТАЙ ВСЕ ФАЙЛЫ!** Каждый файл = токены. Читай только то, что нужно.

### Шаг 4: Проверь последние изменения в рабочем проекте
```bash
cd /home/segun/CascadeProjects/Перед\ 0_2 && git log --oneline -n 5
```

---

## 📋 СТАНДАРТЫ И ПРАВИЛА

### Язык
- Общение с пользователем: **Русский**
- Документация в AGENTS_RULES-v2/: **Русский**
- Код и комментарии: **Английский**

### Код (Python)
- Type Hints — обязательно
- PEP 8 — обязательно
- Логирование через `logging`, НЕ через `print()`

### Дизайн (Web)
- Dark Mode, градиенты, glassmorphism
- Типографика: Inter / Roboto / Outfit
- Responsive Design

### Данные
- `AGENTS_RULES-v2/` — единственный источник истины
- Правило «Успех/Неудача» — ОБЯЗАТЕЛЬНО в каждом логе

---

## 🌐 РАБОЧАЯ СРЕДА

| Компонент | Значение |
|-----------|---------|
| Рабочая директория | `/home/segun/CascadeProjects/Перед 0_2/` |
| AGENTS_RULES v2 | `/home/segun/CascadeProjects/Перед 0_2/AGENTS_RULES-v2/` |
| LLM API | `http://192.168.47.22:1234/v1` |
| Модель (default) | `gemma-4-31b-it` |
| Модель (ТЗ/ТУ) | `ministral-3-14b-reasoning` |
| KB | `knowledge_base.json` (57 записей) |
| Веб-сервер | http://localhost:5005 (v6) |

---

## ⚡ БЫСТРЫЕ КОМАНДЫ

```bash
# Статус проекта
cat AGENTS_RULES-v2/shared_status.md

# Карта знаний
cat AGENTS_RULES-v2/index.md

# Запуск компиляции вручную
python3 AGENTS_RULES-v2/compile.py

# Запуск watcher
python3 AGENTS_RULES-v2/watcher.py --daemon

# Остановка watcher
python3 AGENTS_RULES-v2/watcher.py --stop

# Проверка здоровья репозитория (супервизор)
python3 AGENTS_RULES-v2/supervisor.py

# Проверка + автоисправление
python3 AGENTS_RULES-v2/supervisor.py --fix

# Отчёт супервизора
cat AGENTS_RULES-v2/supervisor_report.md
```
