# Целевая модель двух агрегатов

Этот файл фиксирует итоговую предметную модель каркаса. Он описывает границы,
состав, команды и правила. Исходные файлы в `north_marketplace/domain` остаются
пустыми до последовательной реализации шести этапов.

В приложении два агрегата. `Order` отвечает за состав и состояние заказа.
`StockItem` отвечает за физический и доступный остаток одного товара на одном
складе. Каждая команда изменяет состояние только своего корня. Прикладной
сценарий может передать идентификатор заказа в команду складской позиции, но не
передаёт сам объект заказа через границу.

```mermaid
flowchart LR
    subgraph order_boundary[Граница заказа]
        order[Order] --> order_id[OrderId]
        order --> lines[OrderLine]
    end
    scenario[Прикладной сценарий]
    subgraph stock_boundary[Граница складской позиции]
        stock[StockItem] --> reservation[StockReservation]
        stock --> balance[StockBalance]
    end
    order_id -. передаётся значением .-> scenario
    scenario -->|reserve| stock
```

Пунктир обозначает передачу значения `OrderId`. У `StockReservation` нет поля
типа `Order`, доступа к строкам заказа или к его адресу. Размещение заказа, в
свою очередь, не списывает и не резервирует товар автоматически.

## Как переносить модель в код

Схемы задают не украшение документации, а последовательность реализации.
Элемент UML переводится в один конкретный элемент проекта: корень — в класс с
закрытыми полями и предметными методами, композиция — во внутренний список,
объект-значение — в отдельный класс с проверкой конструктора, а переход
состояния — в значение `Enum` и метод корня. Условие у стрелки становится
проверкой до изменения поля; нарушение условия выражается доменной ошибкой.

```mermaid
flowchart TD
    rule[Правило и состав в model.md] --> test[Негативный и успешный тест]
    test --> value[Объект-значение или идентификатор]
    value --> root[Метод корня агрегата]
    root --> verify[Запуск всех активных тестов]
    verify --> journal[Запись результата в evolution.md]
    journal --> next[Следующее изменение модели]
```

Композиция `Order *-- OrderLine` переносится в поле `_lines` и закрытый метод
присоединения строки; наружу выдаётся кортеж снимков `OrderLineSnapshot`.
Идентификатор строки проверяется на уникальность до изменения списка. Композиция
`StockItem *-- StockReservation` переносится в `_reservations`; наружу выдаются
снимки `ReservationSummary`. Пунктир `OrderId → прикладной сценарий → StockItem`
переносится в аргумент `order_id` метода `reserve` и явный вызов в
`application.py`. Он не требует импорта `Order` в `stock_item.py`.

## Рабочие потоки реализации

Разработка заказа идёт от неизменяемых частей к корню. На каждом переходе
сохраняются тесты предыдущего состояния: добавление продавца не отменяет
проверку валюты, а добавление подарка не отменяет правило одного продавца.

```mermaid
flowchart LR
    order_values[Этап 1: идентификаторы, значения, OrderLine] --> order_root[Order: строки, адрес, place]
    order_root --> seller[Этап 2: SellerId и проверка состава]
    seller --> gifts[Этап 3: LineKind и две команды строк]
    gifts --> order_done[Итог: размещённый заказ неизменяем]
```

Для этапа 1 код в `identifiers.py` и `values.py` создаёт допустимые значения,
включая `OrderLineId` и `Currency`, а `order.py` проверяет отношения между ними
и даёт команде `change_line_quantity` доступ к строке по идентификатору. Этап 2 добавляет `SellerId` в
строку и поле корня до присоединения первой строки. Этап 3 добавляет `LineKind`,
конструктор строки и две команды, которые различают цену платной и подарочной
позиции. Модуль `tests/test_order_*.py` после каждого этапа должен содержать
как успешный вызов, так и отказ без изменения заказа.

Разработка складской позиции также начинается с значений, однако её итоговое
правило зависит не от одной команды, а от суммы внутренних резервов.

```mermaid
flowchart LR
    stock_values[Этап 4: StockBalance и StockItem] --> reserve[Этап 5: StockReservation и доступный остаток]
    reserve --> expiry[Этап 6: срок и переход в EXPIRED]
    expiry --> stock_done[Итог: остаток защищён во всех командах]
```

Этап 4 помещает изменение физического остатка в `receive` и `write_off`.
Этап 5 добавляет внутреннюю сущность, расчёт доступного остатка и освобождение
по `ReservationId`. Этап 6 добавляет `ReservationDeadline` и параметр `now` в
команду истечения. Модуль `tests/test_stock_*.py` закрепляет расчёт остатка и
состояния резерва; `application.py` изменяется только после появления команд
обоих корней.

## 1. Заказ: начало, развитие и итог

### 1.1. Граница и состав

`Order` — корень агрегата. Он создаётся с `OrderId`, `BuyerId` и объектом
значения `Currency`.
`BuyerId` обозначает покупателя вне этой модели и хранится только как
типизированное значение. Состояние заказа составляют строки, адрес доставки,
валюта, продавец и статус. Внешний код не должен добавлять строку в список или
менять статус напрямую; все изменения проходят через методы корня.

`OrderLine` — внутренняя сущность. Её идентичность задаёт `OrderLineId`:
именно по этому значению корень адресно меняет количество конкретной строки.
Строка не является самостоятельным агрегатом: её создаёт, ищет и изменяет
только `Order`. Цена строки — снимок на момент добавления: цена предложения
может измениться позднее, но цена уже сформированной строки не меняется.
Для чтения корень возвращает `OrderLineSnapshot`, а не изменяемую строку.

```mermaid
classDiagram
    direction TB
    class Order {
        -OrderId _id
        -BuyerId _buyer_id
        -Currency _currency
        -OrderStatus _status
        -SellerId _seller_id
        -list~OrderLine~ _lines
        -ShippingAddress _shipping_address
        +add_paid_line(line_id, sku, title, seller_id, price, quantity)
        +add_gift_line(line_id, sku, title, seller_id, quantity)
        +change_line_quantity(line_id, quantity)
        +set_shipping_address(address)
        +place()
        +cancel()
        +total() Money
    }
    class OrderLine {
        -OrderLineId _id
        -Sku _sku
        -str _title
        -SellerId _seller_id
        -Money _unit_price
        -Quantity _quantity
        -LineKind _kind
        +subtotal() Money
        -_change_quantity(quantity)
        -_snapshot() OrderLineSnapshot
    }
    class OrderLineSnapshot {
        -OrderLineId _id
        -Sku _sku
        -Quantity _quantity
        -LineKind _kind
        +subtotal() Money
    }
    class Money {
        -Decimal _amount
        -Currency _currency
    }
    class Currency {
        -str _code
    }
    class ShippingAddress {
        -str _city
        -str _street
        -str _building
        -str _postal_code
    }
    class OrderStatus {
        <<enumeration>>
        DRAFT
        PLACED
        CANCELLED
    }
    class LineKind {
        <<enumeration>>
        PAID
        GIFT
    }
    class OrderId
    class OrderLineId
    class BuyerId
    class SellerId
    class Sku
    class Quantity
    Order "1" *-- "0..*" OrderLine : содержит
    Order --> OrderId : идентичность
    Order --> BuyerId : хранит значение
    Order --> SellerId : хранит значение
    Order --> ShippingAddress : содержит
    Order --> OrderStatus : состояние
    OrderLine --> Sku : содержит
    OrderLine --> OrderLineId : идентичность
    OrderLine --> SellerId : хранит значение
    OrderLine --> Money : снимок цены
    OrderLine --> Quantity : содержит
    OrderLine --> LineKind : вид строки
    Order ..> OrderLineSnapshot : возвращает снимок
```

Композиция `Order *-- OrderLine` означает, что строка принадлежит заказу.
Связи с `BuyerId` и `SellerId` показывают хранение идентификаторов, а не
объектные связи с моделями покупателя и продавца. Адрес, деньги, валюта и количество
также являются объектами-значениями: они проверяются при создании и сравнимы
по своему содержанию.

### 1.2. Три последовательных этапа

Первый этап вводит базовый заказ. Заказ может содержать строки одной валюты,
адрес доставки и состояние черновика. Метод `place()` возможен, когда есть
хотя бы одна строка, полный адрес и положительная итоговая сумма.

Второй этап вводит `SellerId`. При добавлении первой строки корень сохраняет
её продавца в `_seller_id`. Каждая следующая строка проверяется до изменения
списка; строка другого продавца вызывает `SellerMismatchError` и не попадает в
заказ. Это правило принадлежит `Order`, потому что только он видит все строки.

Третий этап вводит `LineKind`. Платная строка имеет `PAID` и положительную
цену. Подарочная строка имеет `GIFT` и нулевую цену. Обе участвуют в правиле
одного продавца, но `place()` требует хотя бы одну платную строку. Заказ,
состоящий только из подарков, не размещается.

| Команда | Изменяемая часть | Предусловие | Постусловие |
|---|---|---|---|
| `add_paid_line` | состав | `DRAFT`, новый `OrderLineId`, совпадают валюта и продавец | добавлена платная строка |
| `add_gift_line` | состав | `DRAFT`, новый `OrderLineId`, совпадает продавец | добавлена строка с нулевой ценой |
| `change_line_quantity` | конкретная строка | `DRAFT`, строка найдена по `OrderLineId` | количество строки заменено |
| `set_shipping_address` | адрес | `DRAFT`, адрес полон | адрес заменён целиком |
| `place` | статус | есть адрес, строки и платная часть | статус `PLACED` |
| `cancel` | статус | заказ ещё не отменён | статус `CANCELLED` |

```mermaid
stateDiagram-v2
    [*] --> DRAFT: создание Order
    DRAFT --> PLACED: place — заказ готов
    DRAFT --> CANCELLED: cancel()
    PLACED --> CANCELLED: cancel()
    CANCELLED --> [*]
    note right of DRAFT
        Строки и адрес меняются
        только в черновике
    end note
```

Начало жизненного цикла заказа — создание черновика. После `place()` состав и
адрес закрыты. `cancel()` переводит черновик или размещённый заказ в
`CANCELLED`; повторная отмена отклоняется. Конец этой границы наступает не при
резервировании, а при завершении её собственных правил: состава, адреса,
валюты, продавца и статуса.

## 2. Складская позиция: начало, развитие и итог

### 2.1. Граница и состав

`StockItem` — корень агрегата складской позиции. Он представляет один `Sku` на
одном `WarehouseId` и имеет идентичность `StockItemId`. Корень владеет
физическим остатком и внутренними резервами. Физический остаток хранится как
`StockBalance` и не может быть отрицательным.

`StockReservation` имеет собственный `ReservationId` и изменяющееся состояние,
поэтому это внутренняя сущность. Она не становится самостоятельным корнем:
создание, освобождение и истечение выполняет `StockItem`. Для чтения корень
возвращает `ReservationSummary`, то есть снимок без методов изменения.

```mermaid
classDiagram
    direction TB
    class StockItem {
        -StockItemId _id
        -WarehouseId _warehouse_id
        -Sku _sku
        -StockBalance _physical_balance
        -list~StockReservation~ _reservations
        +receive(quantity)
        +write_off(quantity)
        +reserve(reservation_id, order_id, quantity, deadline)
        +release_reservation(reservation_id)
        +expire_reservations(now) int
        +available_quantity() StockBalance
    }
    class StockReservation {
        -ReservationId _id
        -OrderId _order_id
        -Quantity _quantity
        -ReservationDeadline _deadline
        -ReservationStatus _status
        -release()
        -expire_if_due(now) bool
    }
    class ReservationSummary {
        -ReservationId _reservation_id
        -OrderId _order_id
        -Quantity _quantity
        -ReservationDeadline _deadline
        -ReservationStatus _status
    }
    class StockBalance {
        -int _value
        +increase(quantity) StockBalance
        +decrease(quantity) StockBalance
    }
    class ReservationStatus {
        <<enumeration>>
        ACTIVE
        RELEASED
        EXPIRED
    }
    class StockItemId
    class WarehouseId
    class Sku
    class ReservationId
    class OrderId
    class Quantity
    class ReservationDeadline
    StockItem "1" *-- "0..*" StockReservation : владеет
    StockItem --> StockItemId : идентичность
    StockItem --> WarehouseId : хранит значение
    StockItem --> Sku : хранит значение
    StockItem --> StockBalance : физический остаток
    StockReservation --> ReservationId : идентичность
    StockReservation --> OrderId : хранит значение
    StockReservation --> Quantity : содержит
    StockReservation --> ReservationDeadline : содержит
    StockReservation --> ReservationStatus : состояние
    StockItem ..> ReservationSummary : возвращает снимок
```

Связь `StockReservation → OrderId` показывает ровно одно поле значения. В
складской позиции нет объекта `Order`, его строк, адреса и методов. Резерв не
удаляется после освобождения или истечения: меняется его статус, благодаря чему
видна история решения в пределах этой складской позиции.

### 2.2. Три последовательных этапа

Четвёртый этап вводит базовую складскую позицию. `receive()` увеличивает
физический остаток, а `write_off()` уменьшает его, не позволяя получить
отрицательное значение.

Пятый этап добавляет `StockReservation`. Корень создаёт резерв по
`ReservationId`, хранит `OrderId`, количество и срок. Сумма активных резервов
не может превышать физический остаток. Освобождение принимает только
`ReservationId`: связь с заказом была зафиксирована при создании и не нужна для
изменения статуса резерва.

Шестой этап добавляет `ReservationDeadline` и истечение. Доступный остаток
вычисляется по формуле:

```text
доступный остаток = физический остаток − сумма активных резервов
```

Время передаётся в `expire_reservations(now)` параметром. Резерв с наступившим
сроком переходит из `ACTIVE` в `EXPIRED` и перестаёт уменьшать доступный
остаток. Уже освобождённый резерв не истекает повторно.

```mermaid
stateDiagram-v2
    [*] --> ACTIVE: reserve()
    ACTIVE --> RELEASED: release_reservation(reservation_id)
    ACTIVE --> EXPIRED: expire_reservations(now)
    RELEASED --> [*]
    EXPIRED --> [*]
    note right of ACTIVE
        Учитывается в доступном остатке
    end note
    note right of EXPIRED
        Срок наступил
    end note
```

```mermaid
sequenceDiagram
    participant Scenario as Прикладной сценарий
    participant Stock as StockItem
    participant Reservation as StockReservation
    Scenario->>Stock: reserve(reservation_id, order_id, quantity, deadline)
    Stock->>Stock: available_quantity()
    alt Остатка достаточно
        Stock->>Reservation: создать ACTIVE
        Stock->>Stock: добавить резерв
        Stock-->>Scenario: команда завершена
    else Остатка недостаточно
        Stock-->>Scenario: InsufficientStockError
    end
```

На диаграмме резервирования отсутствует участник `Order`: для команды
достаточно `OrderId`. Прикладной сценарий выбирает момент вызова и передаёт
данные. `StockItem` решает только то, что относится к его границе: достаточен
ли остаток и в каком состоянии находятся его резервы.

## 3. Прикладной сценарий: вызов двух корней

После шестого этапа `application.py` связывает готовые агрегаты одним явным
сценарием. Сначала он создаёт и размещает заказ. Затем создаёт складскую позицию
и передаёт в её команду резервирования только значение `order.id()`. Корни не
вызывают друг друга, а `application.py` не повторяет их проверки.

```mermaid
sequenceDiagram
    participant App as application.py
    participant Order as Order
    participant Stock as StockItem
    App->>Order: создать Order(order-100, buyer-20, RUB)
    App->>Order: добавить платную строку и подарок
    App->>Order: задать ShippingAddress
    App->>Order: place()
    App->>Stock: создать StockItem(stock-400, BOOK-001, 8)
    App->>Stock: reserve(reservation-900, order.id(), 1, deadline)
    App->>Order: total() и status()
    App->>Stock: physical_balance() и available_quantity()
```

В прикладном файле этот порядок выражается обычными вызовами. Конструкторы
`OrderLine` и `StockReservation` здесь не используются: их создают методы
корней. Сценарий должен получить результат `PLACED`, сумму `1290.00 RUB`,
физический остаток `8`, доступный остаток `7` и текст о резервировании по
`OrderId`.

```python
rub = Currency("RUB")
order = Order(OrderId("order-100"), BuyerId("buyer-20"), rub)
seller_id = SellerId("seller-7")
order.add_paid_line(OrderLineId("line-1"), Sku("BOOK-001"), "Книга о Севере", seller_id,
                    Money(Decimal("1290.00"), rub), Quantity(1))
order.add_gift_line(OrderLineId("line-2"), Sku("BOOKMARK-001"), "Закладка", seller_id, Quantity(1))
order.change_line_quantity(OrderLineId("line-1"), Quantity(2))
order.set_shipping_address(ShippingAddress("Архангельск", "Поморская", "18", "163000"))
order.place()

stock_item = StockItem(StockItemId("stock-400"), WarehouseId("warehouse-ark"),
                       Sku("BOOK-001"), StockBalance(8))
stock_item.reserve(ReservationId("reservation-900"), order.id(), Quantity(1), deadline)
```

## 4. Итоговая карта ответственности

| Этап | Добавление | Корень команды | Защищаемое правило |
|---|---|---|---|
| 1 | базовый `Order` | `Order` | одна валюта; адрес и строки для размещения |
| 2 | `SellerId` | `Order` | в строках один продавец |
| 3 | `LineKind` | `Order` | подарок нулевой; платная часть обязательна |
| 4 | базовый `StockItem` | `StockItem` | физический остаток неотрицателен |
| 5 | `StockReservation` | `StockItem` | резервы не превышают остаток |
| 6 | `ReservationDeadline` | `StockItem` | доступны только не зарезервированные единицы |

Итог образуют две независимые границы. Заказ защищает состав, адрес и денежную
часть обещания покупателю. Складская позиция защищает остаток и состояние своих
резервов. Их единственная показанная связь — передача `OrderId` прикладным
сценарием; общих изменяемых объектов и автоматического резервирования нет.
