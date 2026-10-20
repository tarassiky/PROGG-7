# Каркас практикума «Два агрегата магазина „Север“»

Каркас содержит структуру приложения, неинтерактивную точку входа и шесть
наборов проверок. Проверки помечены `skip`, пока соответствующий этап не
реализован. После каждого этапа отметка снимается только с проверок, правила
которых уже выражены в коде.

```bash
uv run python -m unittest discover -s tests -v
uv run python -m north_marketplace
```

Реализация размещается в `north_marketplace/domain`. Целевая структура
агрегатов, их команды и правила зафиксированы в [model.md](model.md), а порядок
переноса схем в код и тесты — в [evolution.md](evolution.md).

PDF-версии этих документов находятся в
[north-two-aggregates-starter-model.pdf](../../pdf/north-two-aggregates-starter-model.pdf)
и
[north-two-aggregates-starter-evolution.pdf](../../pdf/north-two-aggregates-starter-evolution.pdf).
Внешние библиотеки, хранилище, HTTP, ORM, репозитории и события в работе не
используются.
