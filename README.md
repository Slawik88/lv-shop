# LV Shop — Custom Products E-Commerce Platform

## Стек
- **Backend**: Python (Django 6.0), PostgreSQL
- **Frontend**: HTMX, Alpine.js, TailwindCSS (CDN)
- **Preview**: Динамический SVG генерируемый Django view
- **PDF**: ReportLab для производственных заказов

## Принципы
- **ZERO HARDCODE**: Все настройки (цены, шрифты, материалы, координаты текста) через Django Admin
- **Live Preview**: Мгновенный WYSIWYG предпросмотр при изменении параметров

## Быстрый старт

```bash
# 1. Создать виртуальное окружение
python -m venv venv
source venv/bin/activate

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Выполнить миграции
python manage.py migrate

# 4. Загрузить тестовые данные (3 товара: табличка, кубок, розетка)
python manage.py seed_data

# 5. Создать суперпользователя
python manage.py createsuperuser

# 6. Запустить сервер
python manage.py runserver
```

Сайт: http://localhost:8000  
Админка: http://localhost:8000/admin/

## Структура проекта

```
├── config/              # Django настройки, URLs
├── products/            # Товары, категории, атрибуты, текстовые поля
├── configurator/        # Шаблоны конфигуратора, SVG превью, шрифты
├── orders/              # Корзина, заказы, PDF генерация
├── templates/           # HTML шаблоны (HTMX + Alpine.js)
├── static/              # CSS, JS, шрифты
├── media/               # Загруженные файлы
└── requirements.txt     # Python зависимости
```

## Архитектура

### Модели
- **Category** → Категории товаров
- **Product** → Базовый товар с ценой
- **AttributeGroup** → Группа опций (Материал, Цвет, Шрифт)
- **AttributeOption** → Опция с модификатором цены
- **TextFieldConfig** → Настраиваемое текстовое поле с координатами на превью
- **ConfiguratorTemplate** → SVG шаблон с JSON конфигурацией слоёв
- **FontChoice** → Доступные шрифты
- **SavedConfiguration** → Сохранённая конфигурация (для корзины/заказа)
- **Order / OrderItem** → Заказы

### Live Preview
1. Alpine.js отслеживает изменения в форме
2. При каждом изменении обновляется `src` тега `<img>`, указывающий на `/configurator/preview/<slug>.svg`
3. Django view генерирует SVG на лету, читая координаты и стили из БД
4. HTMX одновременно пересчитывает цену через `/configurator/price/<slug>/`

### Django Admin
- Inline модели для добавления атрибутов и текстовых полей
- Координатный редактор для позиционирования текста на превью
- JSON-редактор для конфигурации слоёв и декораций
