# Работа с saltbox-compose

В `saltbox-compose` меняют состав инстанса, конфигурацию сервисов и порядок их запуска. Инструкции относятся ко всему репозиторию и подходят для работы с любым помощником разработки. Названия, используемые в задачах, интерфейсе и коде, сопоставлены в [GLOSSARY.md](./GLOSSARY.md).

## Где искать изменение

| Что меняется | С чего начать |
| --- | --- |
| Состав сервисов, сети, тома, зависимости запуска | [compose.yaml](./compose.yaml). Для режима разработки посмотри соответствующий `compose-*-dev.yaml`. |
| Значение по умолчанию или подключение модуля | [base.env](./base.env) и место, где Compose передаёт значение сервису. Настройки конкретной установки задаются в локальном `override.env`. |
| Подготовка инстанса к запуску | [bin/update_and_run.sh](./bin/update_and_run.sh) и вызываемые им скрипты в `bin/`. Описания генерируемых секретов находятся в [secrets.json](./secrets.json), сами значения остаются локальными. |
| Маршрутизация HTTPS или правила доступа | Конфигурация входного прокси в `proxy/`, политики OPA в `opa/policies/`. |

Для установки с нуля используй проект `install-saltbox`, указанный в [README_RU.md](./README_RU.md). Файл `bin/install_saltbox.py` в этом репозитории завершает работу с подсказкой о переносе установщика.

## Как описать и проверить изменение

1. До правки укажи в задаче или существующей спецификации, какой вариант развёртывания затронут, что делает оператор и какой результат он должен получить. Если критерии приёмки уже записаны, используй их.
2. Подбери проверку под каждый критерий. Например, для сценария с внешней MongoDB можно проверить состав сервисов. При стандартных профилях в выводе `./bin/sb-compose.sh config --services` есть `mongo` и `salt-master`. При `COMPOSE_PROFILES=salt-master` в локальном `override.env` остаётся `salt-master`, а `mongo` из списка исчезает. Если критерий включает работу с внешней БД, проверь подключение на тестовом инстансе.
3. После правки сопоставь результат с критерием и укажи, что удалось проверить. При изменении действий оператора обнови инструкции в [README.md](./README.md) и [README_RU.md](./README_RU.md). Правила ведения журнала изменений и оформления коммитов описаны в [CONTRIBUTING.ru.md](./CONTRIBUTING.ru.md).

Для межрепозиторного изменения укажи, кто задаёт значение или отправляет сообщение, кто его читает и по какому результату оператор увидит изменение. Для обновления опиши поведение с существующим `override.env`, данными или отдельно установленным контроллером, если они затронуты. Сверяй исходники с тегами образов выбранного инстанса и версиями библиотек у потребителей. Dev-переопределения могут подключать соседние рабочие копии вместо кода из образа.

## Как проследить изменение между репозиториями

Ниже пути внутри соседних проектов отсчитываются от корня указанного репозитория. Для задачи обычно достаточно пройти одну из этих цепочек.

### Настройка сервиса и фоновые процессы

- Проследи переменную от `base.env` или `.env` дополнения через `environment` нужного сервиса до класса настроек. Например, `SALTBOX_MODULE_INVENTORY_ON` передаётся как `IS_MODULE_INVENTORY_ON`, а `saltbox-core/saltbox_core/config.py` читает её как `is_module_inventory_on`. Общие настройки MongoDB, Redis, RabbitMQ и Discovery находятся в `saltbox-sdk/saltbox_sdk/config/`.
- В `compose.yaml` несколько процессов наследуют конфигурацию `&core`. Команда контейнера определяет, какую часть ядра он выполняет. Для обработки событий сверь также `saltbox-core/pyproject.toml` и обработчик события. Например, включение Inventory влияет на обработку результата команды Salt, поэтому проверка одного HTTP-процесса Core недостаточна.
- Для нового секрета проследи имя от описания генерации через секцию `secrets` и подключение к конкретному сервису до пути, который читает приложение. Scheduler дополняет настройки и секреты встроенного `mongo`. При внешней MongoDB отдельно проверь доступ пользователя Scheduler к его БД.

### Команды Salt и сообщения модулей

- Для обмена Core с контроллером начни с `saltbox-bridge-messages/saltbox_bridge_messages/`. Например, запрос списка миньонов строится в `saltbox-core/saltbox_core/minion_collections/routers/minion.py`, а ответ формирует `saltbox-bridge/saltbox_bridge/event_bus/subscribers/minion_subscribers.py`. Проследи поле `master` и типы запроса и ответа на обеих сторонах. Если контроллер обновляется отдельно, укажи поддерживаемую пару версий и проверь обмен с ней.
- Путь события определяй по отправителю и подписчику. Bridge использует Redis для обмена с Core. При интеграции модулей встречаются очереди RabbitMQ, например `inventory_put_data` и `audit_events`. У TaskIQ есть отдельные рабочие процессы и сервис `redis-taskiq`. Изменение адреса или секрета одного из этих сервисов проверяй по соответствующей операции.
- Для локальной проверки совместных правок Core и Bridge сверь монтирование библиотек в [compose-backend-dev.yaml](./compose-backend-dev.yaml) и [compose-salt-dev.yaml](./compose-salt-dev.yaml). При выпуске сверь зависимости в `pyproject.toml` обоих потребителей и теги образов в Compose.

### Путь пользователя от входа до экрана модуля

1. Входной HTTPS-запрос принимает `proxy`. Адреса Gateway и статических ресурсов оболочки заданы в [шаблоне Nginx](./proxy/saltbox.conf.template). Realm, клиентов и роли настраивает `saltbox-keycloak-init/saltbox_keycloak_init/`. При изменении входа проверь первый запуск и повторную инициализацию с существующим realm.
2. Backend сообщает имя сервиса, адрес экземпляра, маршруты и параметры фронтенда. Для сервисов на SDK смотри `saltbox-sdk/saltbox_sdk/discovery_client/`, для регистрации и проксирования — `saltbox-gateway/saltbox_gateway/routers/`. Сопоставь внутренний адрес контейнера с публичными URL. При изменении прав сверь параметры операции в OpenAPI, обработку OPA в Gateway и правило в `opa/policies/`. Проверь действие под ролями с разными правами.
3. В браузере `saltbox-frontend-root-config/src/saltbox-root-config.ts` запрашивает `/api/discovery/config`, выбирает доступные модули и загружает `index.js` по опубликованному URL. Для нового экрана проверь запись сервиса, загрузку его статики и конкретный маршрут или действие в меню. Для автономно регистрируемого фронтенда, например Superset, проверь запись фронтенда в конфигурации Discovery.
4. `saltbox-frontend-base` отвечает за общий экран, вход и меню. `saltbox-frontend-common` поставляет общие компоненты и типы как пакет. Экраны устройств, задач и команд находятся в `saltbox-frontend-core`, список и сведения о сервисах — в `saltbox-frontend-gateway`. Если меняется расширение экрана устройства, сверь объявление плагина в модуле и использование этой точки расширения в `saltbox-frontend-core/src/features/plugins/`.

## Подключение дополнительных модулей

Для Inventory, Metric, Scheduler, Audit, FileBrowser и Client Toolkit проверь закоммиченный `.env` соответствующего Compose-репозитория. Каждый дописывает свой файл в `COMPOSE_FILE`. Audit и Scheduler добавляют также `secrets.json` в `_UPDATE_AND_RUN_EXTRA_SECRETS_CONFS`. Когда оператор подключает несколько модулей, проверяй итоговую конфигурацию со всем списком в `_UPDATE_AND_RUN_EXTRA_ENV_FILES`.

| Модуль и репозитории | Что проследить и чем подтвердить результат на стенде |
| --- | --- |
| Инвентаризация — `saltbox-inventory-compose`, `saltbox-inventory-backend`, `saltbox-inventory-frontend` | Core передаёт подходящий результат команды в `inventory_put_data`. Обработчик `saltbox_inventory/event_bus/routers/inventory.py` извлекает данные и отправляет их ядру в `minions_add_extra_data`. Проверь ожидаемую категорию и значение у выбранного устройства. Отдельный интерфейс Inventory в текущем `root-config` исключён из загрузки, а в базовом Compose-файле дополнения объявлены API и обработчик FastStream. |
| Метрики — `saltbox-metric-compose`, `saltbox-metric-backend`, `saltbox-frontend-metric` | Флаг `SALTBOX_MODULE_METRIC_ON` включает передачу данных из Core. Сбор метрик выполняет `saltbox-metric-app`. Конфигурации Prometheus, Grafana и Loki находятся в Compose-репозитории модуля. Фронтенд добавляет в настройки ссылки на Grafana. Для изменения метрики проверь значение после известного события, для изменения навигации — переход на нужный дашборд или в логи. |
| Планировщик — `saltbox-scheduler-compose`, `saltbox-scheduler-backend`, `saltbox-scheduler-frontend` | API сохраняет расписание, TaskIQ инициирует его выполнение, обработчики RabbitMQ принимают шаблоны и результаты от сервисов. Формат сообщений смотри в `saltbox-sdk/saltbox_sdk/scheduler/messages.py`. Проверь одно срабатывание тестового расписания и появление результата в интерфейсе планировщика. |
| Аудит — `saltbox-audit-compose`, `saltbox-audit-backend` | `app/rabbit_router.py` принимает `audit_events` и сохраняет событие. У модуля есть собственный профиль `mongodb-audit`. Выполни отслеживаемое действие на тестовом инстансе и проверь соответствующую запись через API аудита. Если меняется выгрузка событий в файл, проверь и файл. |
| Файловый менеджер — `saltbox-filebrowser-compose`, `saltbox-filebrowser-adapter`, `saltbox-filebrowser-frontend` | Compose задаёт источники файлов и монтирования. Адаптер читает Swagger и регистрирует маршруты в Discovery. Фронтенд открывает `/filesystem/browser`. При изменении источника проверь один и тот же файл со стороны хранилища и из нужного раздела менеджера с предусмотренными правами. |
| Client Toolkit — `saltbox-client-toolkit-compose`, `saltbox-client-toolkit-backend` | Compose подключает образы API и фронтенда. В текущем backend реализованы регистрация через SDK и `/discovery/health`. Проверяй появление модуля в конфигурации Gateway и загрузку его интерфейса. |

У следующих двух модулей свои Compose-проекты. Для них меняются точки настройки и признаки готовности.

- **Сценарии** — `saltbox-migration-compose`, `saltbox-migration-backend`, `saltbox-migration-frontend`. Отправная точка — `example.env` проекта модуля. Проверь доступ к MongoDB Salt.Box, RabbitMQ и Discovery из сети этого проекта. API работает отдельно от `migration-processing`. Для шага с командой Salt проследи получение JID и результата этой попытки в `app/rabbit_router.py`, затем открой сценарий в интерфейсе. Внешний маршрут списка — `/scenarios/list`.
- **Аналитика** — `saltbox-analytics-compose`, `saltbox-analytics-backend`, `saltbox-analytics-frontend`. Сам стек описан в `saltbox-analytics/compose.yaml` репозитория дополнения. В режиме интеграции основной проект подключает `saltbox/compose-analytics-proxy.yaml`, а `analytics-superset-register` публикует фронтенд в Discovery. Для изменения данных проверь запуск соответствующего DAG в Airflow и обновление витрины. Для изменения интерфейса проверь загрузку микрофронтенда и открытие дашборда Superset через выбранную точку входа.

## Как проследить операцию по логам

Начни с времени действия, часового пояса и того, что увидел пользователь. Возьми одно окно времени для всех участников операции. Например, для недавнего действия в Планировщике на инстансе с этим модулем выполни из корня проекта:

```bash
./bin/sb-compose.sh logs --since 10m --timestamps \
  rabbitmq saltbox-scheduler-taskiq-scheduler saltbox-scheduler-taskiq-worker saltbox-scheduler-faststream
```

| Что проверяем | Какие записи сопоставить |
| --- | --- |
| Старт Планировщика | При `Connection refused` к RabbitMQ сравни время ошибки с `started TCP listener` на порту 5672. Затем ищи `Startup completed` у TaskIQ scheduler и `Listening started` у worker. Ошибку MongoDB `AuthenticationFailed` (код 18) проверяй отдельно по следующей попытке того же сервиса. Для API и worker признак восстановления доступа — `MongoDB scheduler cron tasks initialized`. Для `mongo-exporter` проверь свежее значение `mongodb_up` для нужного экземпляра в Prometheus. |
| Срабатывание расписания из интерфейса | Служебные задачи `sync_scheduled_tasks` и `request_task_templates` идут каждую минуту и раз в пять минут соответственно. Для пользовательского расписания ищи `Sending task …process_scheduled_task` с его `schedule_id`, затем `Executing task …process_scheduled_task` у worker. У каждой попытки свой TaskIQ ID. Дальше модуль получает `scheduler_run_task`, а Scheduler сохраняет ответ из `scheduler_run_task_result` по `process_id`. Проверь результат этой попытки в интерфейсе. |
| Устройство не получило ожидаемый Pillar | Сопоставь ошибку рендера в `salt-master` с запросом `master_get_pillar_data` в `saltbox-core-faststream-redis` для того же контроллера. Если рядом с `Processed` есть `Master … not found`, проверь статус регистрации. После `MasterStatus.ACCEPTED` и `Connection to Core succeed` проверь новое чтение одного ожидаемого несекретного ключа Pillar для затронутого миньона. |
| Запрос из интерфейса и проверка прав | Найди метод и путь запроса в `saltbox-gateway`. Для маршрута с политикой OPA и включённым аудитом найди `permission_check` и его `decision`. Если запрос дошёл до сервиса, сопоставь `data_access` и `status_code` по тому же `correlation_id`. В журнале OPA поле `req_id` связывает запрос политики с её HTTP-ответом. Статус 200 у OPA означает, что сервис вернул ответ на запрос политики. |

В примерах из журналов замени идентификаторы согласованными метками, чтобы сохранить связь между событиями. Перед публикацией удали пароли, токены, заголовки авторизации и значения Pillar.

## Проверки из корня репозитория

```bash
./bin/dotenv_tool.sh env-files     # Порядок подключённых dotenv-файлов
./bin/validate_dotenv.py           # Проверка существующего override.env
./bin/sb-compose.sh config --quiet # Проверка итоговой модели Compose
```

Обёртка `sb-compose.sh` читает `base.env`, затем файлы из `_UPDATE_AND_RUN_EXTRA_ENV_FILES` в заданном порядке, последним — локальный `override.env`, если он есть. Проверяй модель с теми профилями и файлами переопределений, которые заданы в сценарии. Для проверки работы сервисов нужен тестовый инстанс. Штатный запуск через `update_and_run.sh` может обновить репозитории, создать секреты, загрузить образы и запустить контейнеры.

Основной `compose.yaml` должен работать с Docker Compose 2.20.2. Настройки `develop` помещай в файлы для разработки. Для Python-скриптов в `bin/` используй стандартную библиотеку и проверяй изменённый сценарий на Python 3.7.3. Требования к среде и инструкции по запуску приведены в [README_RU.md](./README_RU.md).

### Пример приёмки конфигурации дополнения

В отдельной тестовой копии с соседним `saltbox-inventory-compose` задай в `override.env` строку `_UPDATE_AND_RUN_EXTRA_ENV_FILES='../saltbox-inventory-compose/.env'`. Выполни проверки выше, затем сравни два варианта установки.

| Проверка | Базовая установка | Подключена «Инвентаризация» |
| --- | --- | --- |
| `./bin/sb-compose.sh config --services` | Сервисов Inventory в списке нет | Присутствуют `saltbox-inventory` и `saltbox-inventory-faststream` |
| `./bin/dotenv_tool.sh get SALTBOX_MODULE_INVENTORY_ON` | `false` | `true` |

Если критерий касается сбора данных, следующий шаг — проверить на стенде результат для конкретного миньона по цепочке из таблицы модулей.

### Где уже есть проверки

- Для изменений логики Core в его CI используется `SALTBOX_ENV_FILE=tests/test.env pytest`. Из корня `saltbox-core` можно выбрать подходящий тест, например `tests/test_task_targeting_masters.py` для выбора контроллеров. Для общих компонентов интерфейса в `saltbox-frontend-common` команда `yarn test` запускает Vitest.
- `saltbox-autotests` проверяет работающий API. Например, `pytest tests/test_discovery.py` проверяет HTTP-ответ и схему health по настроенному `RESOURCE_URL`. Для интеграционных тестов подготовь отдельный инстанс с доступными Core, Keycloak и Redis. Фикстуры могут создавать сущности и очищать тестовые данные. В основном проекте есть [compose-autotests.yaml](./compose-autotests.yaml) для запуска `./bin/sb-compose.sh up autotests`, в `base.env` этот способ помечен как устаревший.
- При изменении тегов образов сверь условие задания `Check release image tags` в [.gitlab-ci.yml](./.gitlab-ci.yml). Оно запускает `bin/image_tags.py check` для тега при включённом `TEST_IMAGE_TAGS`. Для изменения API Core проверь также задание `Trigger API Client pipeline` в CI ядра и версию сгенерированного клиента, используемую интерфейсом.
