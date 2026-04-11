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
