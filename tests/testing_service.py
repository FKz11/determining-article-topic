import requests
import time

# URL сервиса FastAPI
url = 'http://localhost:8000/predict'

# Данные для отправки
data = {
    'text': """Docker — программное обеспечение для автоматизации развёртывания и управления приложениями в средах с поддержкой контейнеризации, контейнеризатор приложений. Позволяет «упаковать» приложение со всем его окружением[en] и зависимостями в контейнер, который может быть развёрнут на любой Linux-системе с поддержкой контрольных групп в ядре, а также предоставляет набор команд для управления этими контейнерами. Изначально использовал возможности LXC, с 2015 года начал использовать собственную библиотеку, абстрагирующую виртуализационные возможности ядра Linux — libcontainer. С появлением Open Container Initiative начался переход от монолитной к модульной архитектуре.

Разрабатывается и поддерживается одноимённой компанией-стартапом, распространяется в двух редакциях — общественной (Community Edition) по лицензии Apache 2.0 и для организаций (Enterprise Edition) по проприетарной лицензии[10]. Написан на языке Go.


Содержание
1	История
2	Применение
3	Примечания
4	Литература
5	Ссылки
История
Проект начат как внутренняя собственническая разработка компании dotCloud, основанной Соломоном Хайксом (Solomon Hykes) в 2008 году с целью построения публичной PaaS-платформы с поддержкой различных языков программирования. Наряду с Хайксом в первоначальной разработке значительное участие приняли инженеры dotCloud Андреа Лудзарди (Andrea Luzzardi) и Франсуа-Ксавье Бурле (François-Xavier Bourlet).

В марте 2013 года код Docker был опубликован под лицензией Apache 2.0[11]. В июне 2013 года генеральным директором в dotCloud приглашён Бен Голуб (англ. Ben Golub), ранее руководивший фирмой Gluster[en] (разрабатывавшей технологию распределённого хранения GlusterFS и поглощённой за $136 млн Red Hat в 2011 году)[12]. В октябре 2013 года, подчёркивая смещение фокуса к новой ключевой технологии, dotCloud переименована в Docker (при этом PaaS-платформа сохранена под прежним названием — dotCloud).

В октябре 2013 года выпущен релиз Havana тиражируемой IaaS-платформы OpenStack, в котором реализована поддержка Docker (как драйвер для OpenStack Nova). С ноября 2013 года частичная поддержка Docker включена в дистрибутив Red Hat Enterprise Linux версии 6.5[13] и полная — в 20-ю версию дистрибутива Fedora, ранее было достигнуто соглашение с Red Hat о включении с 2014 года Docker в тиражируемую PaaS-платформу OpenShift[14]. В декабре 2013 года объявлено о поддержке развёртывания Docker-контейнеров в среде Google Compute Engine[en][15].

С 2014 года ведутся работы по включению поддержки Docker в среду управления фреймворка распределённых приложений Hadoop; по результатам тестирования вариантов платформы виртуализации для Hadoop, проведённом в мае 2014 года, Docker показал на основных операциях (по массовому созданию, перезапуску и уничтожению виртуальных узлов) существенно более высокую производительность, нежели KVM, в частности, на тесте массового создания виртуальных вычислительных узлов прирост потребления процессорных ресурсов в Docker зафиксирован в 26 раз ниже, чем в KVM, а прирост потребления ресурсов оперативной памяти — втрое ниже[16].

С 2017 года вдобавок к свободно распространяемой под лицензией Apache 2.0 редакции продукта выпускается редакция для организаций, продаваемая по ценам от $750 до $2 тыс. в год на узел в зависимости от доступных функций[10].

Применение

Docker на физическом Linux-сервере[17]
Программное обеспечение функционирует в среде Linux с ядром, поддерживающим контрольные группы и изоляцию пространств имён (namespaces); существуют сборки только для платформ x86-64 и ARM[18]. Начиная с версии 1.6 (апрель 2015 года) возможно использование в операционных системах семейства Windows[19].

Для экономии пространства хранения проект использует файловую систему Aufs с поддержкой технологии каскадно-объединённого монтирования: контейнеры используют образ базовой операционной системы, а изменения записываются в отдельную область. Также поддерживается размещение контейнеров в файловой системе Btrfs с включённым режимом копирования при записи.

В состав программных средств входит демон — сервер контейнеров (запускается командой docker -d), клиентские средства, позволяющие из интерфейса командной строки управлять образами и контейнерами, а также API, позволяющий в стиле REST управлять контейнерами программно.

Демон обеспечивает полную изоляцию запускаемых на узле контейнеров на уровне файловой системы (у каждого контейнера собственная корневая файловая система), на уровне процессов (процессы имеют доступ только к собственной файловой системе контейнера, а ресурсы разделены средствами libcontainer), на уровне сети (каждый контейнер имеет доступ только к привязанному к нему сетевому пространству имён и соответствующим виртуальным сетевым интерфейсам).

Набор клиентских средств позволяет запускать процессы в новых контейнерах (docker run), останавливать и запускать контейнеры (docker stop и docker start), приостанавливать и возобновлять процессы в контейнерах (docker pause и docker unpause). Серия команд позволяет осуществлять мониторинг запущенных процессов (docker ps по аналогии с ps в Unix-системах, docker top по аналогии с top и другие). Новые образы возможно создавать из специального сценарного файла (docker build, файл сценария носит название Dockerfile), возможно записать все изменения, сделанные в контейнере, в новый образ (docker commit). Все команды могут работать как с docker-демоном локальной системы, так и с любым сервером Docker, доступным по сети. Кроме того, в интерфейсе командной строки встроены возможности по взаимодействию с публичным репозиторием Docker Hub, в котором размещены предварительно собранные образы приложений, например, команда docker search позволяет осуществить поиск среди размещённых в нём образов[20], образы можно скачивать в локальную систему (docker pull), возможно также отправить локально собранные образы в Docker Hub (docker push).

Также Docker имеет пакетный менеджер Docker Compose, позволяющий описывать и запускать многоконтейнерные приложения; конфигурационные файлы для него описываются на языке YAML.

Примечания
 v25.0.4 — 2024.
 http://thenewstack.io/go-programming-language-helps-docker-container-ecosystem/
 https://docs.docker.com/engine/installation/linux/
 https://docs.docker.com/docker-for-windows/
 https://docs.docker.com/docker-for-mac/
 Schmidt J. Docker bekommt 15 Millionen Risikokapital (нем.) — heise online, 2014.
 Tsai T. https://www.docker.com/blog/getting-started-with-docker-for-arm-on-linux/ — 2019.
 https://github.com/docker/docker/blob/master/LICENSE
 LICENSE (англ.)
 Thomas Claburn. Docker looks big biz in the eye: It’s not you, it’s EE — Enterprise Edition. Straight out of the Red Hat playbook: Take your VM images and pay for support (англ.). The Register (3 марта 2017). — «Docker has extended its product line by adding two E’s, for Enterprise Edition, a version of its container software tuned to the demands of businesses […] And of course there are tiers, with fees for support: Basic ($750/year); Standard ($1,500/year); and Advanced ($2,000/year)». Дата обращения: 29 июня 2017. Архивировано 1 июля 2017 года.
 Avram, Abel Docker: Automated and Consistent Software Deployments (англ.). InfoQ (27 марта 2013). Дата обращения: 3 мая 2014. Архивировано 3 мая 2014 года.
 Darrow, Barb PaaS pioneer dotCloud gets new CEO in industry vet Ben Golub. Former CEO of Gluster says PaaSes need to support multiple stacks and environments — running in house, public clouds, wherever (англ.). GigaOM (23 июля 2013). Дата обращения: 3 мая 2014. Архивировано 3 мая 2014 года.
 Sean Michael Kerner. Red Hat Enterprise Linux 6.5 Delivers Precision Timing. Red Hat’s new enterprise Linux release debuts with new security, virtualization and time-keeping features (англ.) (недоступная ссылка — история). eWeek (21 ноября 2013). Дата обращения: 3 мая 2014.
 Williams, Alex The Matrix Of Hell And Two Open-Source Projects For The Emerging Agnostic Cloud (англ.). TechCrunch (28 июля 2013). Дата обращения: 3 мая 2014. Архивировано 24 сентября 2016 года.
 Frederic Lardinois. Google’s Compute Engine Hits General Availability, Drops Instance Prices 10%, Adds 16-Core Instances & Docker Support (англ.). TechCrunch (19 сентября 2013). Дата обращения: 3 мая 2014. Архивировано 2 мая 2014 года.
 Jack Clark. Docker ported into Hadoop as benchmarks show screaming fast performance. Code committers hope unholy union of open source tech will spawn speedy gonzalez virtualization (англ.). The Register (2 мая 2014). — «Based on the compute node resource usage metrics during the serial VM packing test: Docker LXC CPU growth is approximately 26x lower than KVM. On this surface this indicates a 26x density potential increase from a CPU point of view using docker LXC vs a traditional hypervisor. Docker LXC memory growth is approximately 3x lower than KVM.» Дата обращения: 3 мая 2014. Архивировано 3 мая 2014 года.
 Pethuru Raj; Jeeva S. Chelladhurai; Vinod Singh. Learning Docker. — Packt Publishing, 2015. — 240 с. — ISBN 978-1-78439-793-7.
 Install Docker (англ.). Docker Documentation. Дата обращения: 13 августа 2017. Архивировано 13 августа 2017 года.
 "Docker 1.6: Engine & Orchestration Updates, Registry 2.0, & Windows Client Preview - Docker Blog". Docker Blog (англ.). 2015-04-16. Архивировано из оригинала 13 августа 2017. Дата обращения: 13 августа 2017.
 Репозиторий расположен по адресу registry.hub.docker.com
Литература
Э. Моуэт. Использование Docker. Разработка и внедрение программного обеспечения при помощи технологии контейнеров. Руководство = Using Docker: Developing and Deploying Software with Containers. — ДМК Пресс, 2017. — 354 с. — ISBN 978-5-97060-426-7.
Dirk Merkel. Docker: lightweight Linux containers for consistent development and deployment (англ.) // Linux Journal. — 2014. — Vol. March, no. 239. — P. art. 2.
Ссылки
Проект Docker на сайте GitHub
    """,
    'num_hubs': 5  # Этот параметр можно опустить, так как он имеет дефолтное значение
}

# Отправка POST запроса на сервер
start = time.time()
response = requests.post(url, json=data)
print('Время 1-го запроса:', time.time() - start)

start = time.time()
response = requests.post(url, json=data)
print('Время 2-го запроса:', time.time() - start)

# Проверка ответа
if response.status_code == 200:
    print('Ответ от сервера:', response.json())
else:
    print('Ошибка:', response.status_code, response.text)
