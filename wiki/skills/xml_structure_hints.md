# ✅ XML Structure Hints

> Мигрировано из PROJECT_MEMORY.md v1 | Категория: НАВЫК

---

## Суть
Поле `_xml_structure_hints` в `knowledge_base.json` содержит правила парсинга для разных типов XML-документов. Это позволяет Mistral самостоятельно определять структуру без правок кода.

## Примеры хинтов

### Техническое задание (TypeCode=05.03)
```json
{
  "_xml_structure_hints": {
    "detect_by": "TypeCode == 05.03",
    "developer": "Секция <Designers>/<Designer[@IsGeneral='true']>",
    "NOT": "<Author> (это Заказчик, не Разработчик)",
    "ignore": "ГИП, директор — это должности, не организации"
  }
}
```

### Пояснительная записка
```json
{
  "_xml_structure_hints": {
    "developer": "Секция <IssueAuthor>",
    "NOT": "Секция <Designers> (пустая для ПЗ)"
  }
}
```

## Результат
Mistral больше не путает Заказчика и Разработчика в XML-документах.

---

*Дата создания: 2026-04-07*
