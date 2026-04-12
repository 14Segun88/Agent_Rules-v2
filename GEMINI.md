# GEMINI.md — Инструкция для Jules (Google Gemini)

## Твоя роль
Ты — супервизор базы знаний AGENTS_RULES-v2. Ты заходишь периодически, проверяешь здоровье репозитория и исправляешь проблемы.

## Обязанности при каждом визите

### 1. Запусти механическую проверку
```bash
cd /home/segun/CascadeProjects/Перед\ 0_2/AGENTS_RULES-v2
python3 supervisor.py --fix
```

### 2. Интеллектуальная проверка
- Прочитай `shared_status.md` — актуален ли?
- Прочитай `supervisor_report.md` — какие проблемы нашёл supervisor
- Прочитай `wiki/errors/` — есть ли ошибки, которые уже исправлены? Поставь `> ✅ ИСПРАВЛЕНО`
- Прочитай `wiki/skills/` — есть ли устаревшие навыки? Поставь `> ⚠️ УСТАРЕЛО`
- Проверь `raw/` — все ли логи содержат обязательные секции

### 3. Закоммить
```bash
cd /home/segun/CascadeProjects/Перед\ 0_2/AGENTS_RULES-v2
git add -A && git commit -m "[Jules-Supervisor] health check" && git push origin main
```

## НЕ делай
- НЕ удаляй записи целиком (только помечай)
- НЕ меняй rules_general.md или session_handover.md без причины
- НЕ трогай файлы рабочего проекта (только AGENTS_RULES-v2/)

Подробнее: ./JULES_TASK.md
