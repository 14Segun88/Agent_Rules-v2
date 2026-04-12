# 🏗️ Архитектура проекта

> Мигрировано из PROJECT_MEMORY.md v1 | Обновлено: 2026-04-11

---

## Описание проекта
Интеллектуальный анализатор документов для строительных проектов (МБОУ СОШ на 1100 мест, МКД, МЕС-БМК и др.).

## Стек технологий
| Компонент | Технология |
|-----------|-----------|
| Backend | Python 3, Flask |
| PDF-парсинг | PyMuPDF (fitz) |
| OCR | Tesseract + olmOCR 2-7B (Vision) |
| LLM | LM Studio (локальный), Gemma 4-31B, Mistral 14B |
| Frontend | Vue 3, Dark Mode UI |
| KB | `knowledge_base.json` (57 записей) |

## Пайплайн обработки
```
PDF/DOCX/XML → Текст/Сырой XML
     ↓
Поиск в KB → Подбор 2-3 Few-Shot примеров + XML Hints
     ↓
LLM (Gemma/Mistral) → Экстракция 7 полей (JSON)
     ↓
KB Match (>60%) → Перезапись полей из эталонной базы
     ↓
Результат: title, customer, developer, year, document_type, content_summary, purpose
```

## Эволюция версий
| Версия | Точность | Метод | Порт |
|--------|---------|-------|------|
| V4 | 56% | Только regex | - |
| V5_llm | 65-70% | LLM + Semantic Matching | 5002 |
| V5_vostok | 60-65% | KB Override + Semantic | 5005 |
| V6_cot | 75-85% | CoT Reasoning + KB Fallback | 5007 |

## Ключевые файлы рабочего проекта
```
web_server.py                                    — Сервер (порт 5005)
web_app_v5_final.py                              — Ядро анализатора
knowledge_base.json                              — 57 эталонных записей
olmocr_wrapper.py                                — OCR через LM Studio
run_benchmark_fair.py                            — Fair-бенчмарк обеих моделей
semantic_scorer.py                               — Семантический scoring
cross_model_scorer.py                            — Cross-model scoring
```

## Рабочая среда
- **LLM API:** `http://192.168.47.22:1234/v1` (LM Studio)
- **Модели:** `gemma-4-31b-it` + `ministral-3-14b-reasoning`
- **Python:** системный Python 3
- **Зависимости:** `flask`, `werkzeug`, `rapidfuzz`, `PyMuPDF`
- **OCR (системный):** `sudo apt-get install tesseract-ocr tesseract-ocr-rus`

### 📝 [2026-04-11 22:00] [Antigravity]
watcher.py имеет debounce (5с) и min interval (30с) чтобы не перегружать систему

### 📝 [2026-04-11 22:00] [Antigravity]
Git auto-commit встроен в compile.py — wiki обновляется автоматически после каждой компиляции

### 📝 [2026-04-13 00:51] [KiloCode]
supervisor.py с exit(1) при любой ошибке = постоянные письма "failed" — теперь exit(1) только если --fix не помог

### 📝 [2026-04-13 00:51] [KiloCode]
Jules работает в облачном sandbox, абсолютные пути /home/segun/ там не существуют

### 📝 [2026-04-13 00:51] [KiloCode]
Jules не умеет вести чат автономно — вопросы нужно направлять через GitHub Issues

### 📝 [2026-04-13 01:38] [Antigravity]
При изменении фундаментальных файлов типа конфигураций агентов (или баз знаний) необходимо тщательно сканировать исходный код на предмет абсолютных и относительных путей.

### 📝 [2026-04-13 01:38] [Antigravity]
Централизованный `AGENTS_RULES-v2` стабилен. Очищена устаревшая дублирующая папка `.agent` из корня проекта.
