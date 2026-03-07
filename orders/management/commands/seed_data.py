"""
Management command to populate the DB with sample products for development.
Run:  python manage.py seed_data
      python manage.py seed_data --reset   (wipe products first)
"""
import os

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from products.models import (
    AttributeGroup, AttributeOption, Category, Product, ProductSize,
    TextFieldConfig,
)
from configurator.models import ConfiguratorTemplate, FontChoice


# ─────────────────────────────────────────────
#  SVG ART GENERATORS
# ─────────────────────────────────────────────

def _plate_svg(bg1, bg2, border, label_color='#1a1a1a'):
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="400" viewBox="0 0 800 400">
  <defs>
    <linearGradient id="pg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{bg1}"/>
      <stop offset="100%" stop-color="{bg2}"/>
    </linearGradient>
    <filter id="shadow"><feDropShadow dx="0" dy="4" stdDeviation="8" flood-opacity="0.18"/></filter>
  </defs>
  <rect x="30" y="30" width="740" height="340" rx="16" fill="{border}" filter="url(#shadow)"/>
  <rect x="42" y="42" width="716" height="316" rx="12" fill="url(#pg)"/>
  <rect x="42" y="42" width="716" height="120" rx="12" fill="white" opacity="0.12"/>
  <rect x="60" y="60" width="680" height="280" rx="8" fill="none" stroke="{border}" stroke-width="2.5" opacity="0.6"/>
  <circle cx="88" cy="88" r="7" fill="{border}" opacity="0.8"/>
  <circle cx="712" cy="88" r="7" fill="{border}" opacity="0.8"/>
  <circle cx="88" cy="312" r="7" fill="{border}" opacity="0.8"/>
  <circle cx="712" cy="312" r="7" fill="{border}" opacity="0.8"/>
  <line x1="100" y1="148" x2="700" y2="148" stroke="{border}" stroke-width="1.5" opacity="0.45"/>
  <line x1="100" y1="252" x2="700" y2="252" stroke="{border}" stroke-width="1.5" opacity="0.45"/>
  <text x="400" y="188" font-family="Georgia,serif" font-size="36" fill="{label_color}" text-anchor="middle" dominant-baseline="middle" opacity="0.22">Иванов Иван Иванович</text>
  <text x="400" y="228" font-family="Arial,sans-serif" font-size="20" fill="{label_color}" text-anchor="middle" dominant-baseline="middle" opacity="0.17">Директор</text>
</svg>'''
    return svg.encode()


def _cup_svg(c1, c2, accent, star='#fff'):
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="500" height="600" viewBox="0 0 500 600">
  <defs>
    <linearGradient id="cg" x1="0%" y1="0%" x2="80%" y2="100%">
      <stop offset="0%" stop-color="{c1}"/><stop offset="100%" stop-color="{c2}"/>
    </linearGradient>
    <filter id="drop"><feDropShadow dx="0" dy="6" stdDeviation="12" flood-opacity="0.22"/></filter>
  </defs>
  <g filter="url(#drop)">
    <rect x="160" y="510" width="180" height="40" rx="8" fill="{c2}"/>
    <rect x="175" y="497" width="150" height="18" rx="5" fill="{c1}"/>
    <rect x="224" y="430" width="52" height="70" rx="6" fill="{c2}"/>
    <ellipse cx="250" cy="440" rx="100" ry="22" fill="{c2}"/>
    <path d="M150 200 Q140 320 170 420 Q200 450 250 455 Q300 450 330 420 Q360 320 350 200 Z" fill="{c1}"/>
    <path d="M150 200 Q140 320 170 420 Q200 450 250 455 Q300 450 330 420 Q360 320 350 200 Z" fill="url(#cg)"/>
    <path d="M150 220 Q90 260 100 330 Q108 380 155 390" fill="none" stroke="{accent}" stroke-width="18" stroke-linecap="round"/>
    <path d="M350 220 Q410 260 400 330 Q392 380 345 390" fill="none" stroke="{accent}" stroke-width="18" stroke-linecap="round"/>
    <ellipse cx="250" cy="200" rx="100" ry="22" fill="{c1}"/>
    <ellipse cx="220" cy="280" rx="18" ry="70" fill="white" opacity="0.15" transform="rotate(-15 220 280)"/>
    <text x="250" y="340" font-size="52" text-anchor="middle" dominant-baseline="middle" fill="{star}" opacity="0.65">&#9733;</text>
    <rect x="185" y="355" width="130" height="60" rx="6" fill="{c2}" opacity="0.35"/>
    <text x="250" y="392" font-family="Georgia,serif" font-size="15" fill="{star}" text-anchor="middle" dominant-baseline="middle" opacity="0.45">Надпись</text>
  </g>
</svg>'''
    return svg.encode()


def _crystal_cup_svg(c1, c2, accent):
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="500" height="580" viewBox="0 0 500 580">
  <defs>
    <linearGradient id="xg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{c1}" stop-opacity="0.9"/>
      <stop offset="50%" stop-color="white" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="{c2}" stop-opacity="0.9"/>
    </linearGradient>
    <filter id="xs"><feDropShadow dx="0" dy="8" stdDeviation="14" flood-opacity="0.22"/></filter>
  </defs>
  <rect x="168" y="510" width="164" height="38" rx="8" fill="{c2}" filter="url(#xs)"/>
  <rect x="180" y="495" width="140" height="20" rx="5" fill="{accent}"/>
  <polygon points="232,430 268,430 255,495 245,495" fill="url(#xg)"/>
  <polygon points="250,80 360,160 380,310 340,420 250,445 160,420 120,310 140,160" fill="url(#xg)" filter="url(#xs)"/>
  <line x1="250" y1="80" x2="250" y2="445" stroke="{accent}" stroke-width="1.5" opacity="0.3"/>
  <line x1="140" y1="160" x2="360" y2="160" stroke="{accent}" stroke-width="1.5" opacity="0.3"/>
  <line x1="120" y1="310" x2="380" y2="310" stroke="{accent}" stroke-width="1.5" opacity="0.3"/>
  <line x1="250" y1="80" x2="140" y2="160" stroke="{accent}" stroke-width="1.5" opacity="0.3"/>
  <line x1="250" y1="80" x2="360" y2="160" stroke="{accent}" stroke-width="1.5" opacity="0.3"/>
  <polygon points="250,100 330,170 315,270" fill="white" opacity="0.18"/>
  <polygon points="200,180 240,200 205,320" fill="white" opacity="0.1"/>
  <rect x="192" y="310" width="116" height="74" rx="6" fill="{c2}" opacity="0.3"/>
  <text x="250" y="355" font-family="Georgia,serif" font-size="14" fill="white" text-anchor="middle" dominant-baseline="middle" opacity="0.4">Надпись</text>
</svg>'''
    return svg.encode()


def _medal_svg(rc1, rc2, medal='#C8A84B'):
    import math
    rays = ''.join(
        f'<line x1="200" y1="370" x2="{int(200+112*math.cos(i*math.pi*2/16))}" y2="{int(370+112*math.sin(i*math.pi*2/16))}" stroke="{medal}" stroke-width="3" opacity="0.22"/>'
        for i in range(16)
    )
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="520" viewBox="0 0 400 520">
  <defs>
    <linearGradient id="rg" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{rc1}"/>
      <stop offset="40%" stop-color="{rc2}"/>
      <stop offset="100%" stop-color="{rc1}"/>
    </linearGradient>
    <radialGradient id="mg" cx="40%" cy="35%">
      <stop offset="0%" stop-color="white" stop-opacity="0.2"/>
      <stop offset="100%" stop-color="{medal}"/>
    </radialGradient>
    <filter id="ms"><feDropShadow dx="0" dy="8" stdDeviation="14" flood-opacity="0.25"/></filter>
  </defs>
  <rect x="155" y="0" width="40" height="220" fill="url(#rg)" rx="2"/>
  <rect x="205" y="0" width="40" height="220" fill="{rc1}" opacity="0.7" rx="2"/>
  <rect x="165" y="200" width="70" height="24" rx="6" fill="{medal}" filter="url(#ms)"/>
  <circle cx="200" cy="370" r="130" fill="{medal}" filter="url(#ms)"/>
  <circle cx="200" cy="370" r="118" fill="url(#mg)"/>
  <circle cx="200" cy="370" r="124" fill="none" stroke="{medal}" stroke-width="5"/>
  <circle cx="200" cy="370" r="100" fill="none" stroke="{medal}" stroke-width="2" opacity="0.5"/>
  {rays}
  <ellipse cx="175" cy="335" rx="22" ry="45" fill="white" opacity="0.14" transform="rotate(-20 175 335)"/>
  <text x="200" y="358" font-family="Georgia,serif" font-size="22" font-weight="bold" fill="white" text-anchor="middle" dominant-baseline="middle" opacity="0.38">ОТЛ</text>
  <text x="200" y="395" font-family="Arial,sans-serif" font-size="13" fill="white" text-anchor="middle" opacity="0.28">ЗА ОТЛИЧИЕ</text>
</svg>'''
    return svg.encode()


def _rosette_svg(c1, c2, center='#f5e8c8'):
    import math
    petals = '\n  '.join(
        f'<ellipse cx="{int(220+160*math.cos(i*math.pi*2/14))}" cy="{int(220+160*math.sin(i*math.pi*2/14))}" rx="34" ry="18" fill="{c1}" opacity="0.85" transform="rotate({int((i*math.pi*2/14)*180/math.pi+90)} {int(220+160*math.cos(i*math.pi*2/14))} {int(220+160*math.sin(i*math.pi*2/14))})/>'
        for i in range(14)
    )
    pts = ' '.join(
        f'{int(220+(120 if i%2==0 else 108)*math.cos(i*math.pi*2/40))},{int(220+(120 if i%2==0 else 108)*math.sin(i*math.pi*2/40))}'
        for i in range(40)
    )
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="440" height="440" viewBox="0 0 440 440">
  <defs>
    <radialGradient id="rg" cx="40%" cy="35%">
      <stop offset="0%" stop-color="{center}"/>
      <stop offset="100%" stop-color="{c2}"/>
    </radialGradient>
    <filter id="rs"><feDropShadow dx="0" dy="5" stdDeviation="10" flood-opacity="0.2"/></filter>
  </defs>
  {petals}
  <polygon points="{pts}" fill="{c2}" opacity="0.6" filter="url(#rs)"/>
  <path d="M180 320 L200 440 L220 350 L240 440 L260 320" fill="{c1}" opacity="0.85"/>
  <circle cx="220" cy="220" r="108" fill="{c2}" filter="url(#rs)"/>
  <circle cx="220" cy="220" r="98" fill="url(#rg)"/>
  <circle cx="220" cy="220" r="90" fill="none" stroke="{c2}" stroke-width="4"/>
  <text x="220" y="210" font-size="38" text-anchor="middle" dominant-baseline="middle" fill="{c2}" opacity="0.55">&#9733;</text>
  <ellipse cx="196" cy="195" rx="20" ry="38" fill="white" opacity="0.13" transform="rotate(-25 196 195)"/>
  <text x="220" y="248" font-family="Georgia,serif" font-size="18" font-weight="bold" fill="{c2}" text-anchor="middle" dominant-baseline="middle" opacity="0.38">1 место</text>
</svg>'''
    return svg.encode()


def _badge_svg(bg, border, text='#1a1a1a'):
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="360" height="360" viewBox="0 0 360 360">
  <defs>
    <radialGradient id="bg2" cx="40%" cy="35%">
      <stop offset="0%" stop-color="white" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="{bg}"/>
    </radialGradient>
    <filter id="bs"><feDropShadow dx="0" dy="6" stdDeviation="10" flood-opacity="0.22"/></filter>
  </defs>
  <circle cx="180" cy="180" r="162" fill="{border}" filter="url(#bs)"/>
  <circle cx="180" cy="180" r="150" fill="url(#bg2)"/>
  <circle cx="180" cy="180" r="140" fill="none" stroke="{border}" stroke-width="3"/>
  <circle cx="180" cy="180" r="120" fill="none" stroke="{border}" stroke-width="1.5" opacity="0.4"/>
  <rect x="168" y="8" width="24" height="30" rx="6" fill="{border}"/>
  <circle cx="180" cy="10" r="7" fill="{border}" stroke="white" stroke-width="1.5"/>
  <ellipse cx="155" cy="150" rx="18" ry="40" fill="white" opacity="0.14" transform="rotate(-20 155 150)"/>
  <text x="180" y="168" font-family="Arial,sans-serif" font-size="20" font-weight="bold" fill="{text}" text-anchor="middle" dominant-baseline="middle" opacity="0.28">Имя Фамилия</text>
  <text x="180" y="200" font-family="Arial,sans-serif" font-size="14" fill="{text}" text-anchor="middle" opacity="0.2">Должность</text>
</svg>'''
    return svg.encode()


def _info_plate_svg(bg1, bg2, border):
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="300" viewBox="0 0 800 300">
  <defs>
    <linearGradient id="ipg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{bg1}"/>
      <stop offset="100%" stop-color="{bg2}"/>
    </linearGradient>
    <filter id="ips"><feDropShadow dx="0" dy="4" stdDeviation="6" flood-opacity="0.18"/></filter>
  </defs>
  <rect x="20" y="20" width="760" height="260" rx="14" fill="{border}" filter="url(#ips)"/>
  <rect x="30" y="30" width="740" height="240" rx="10" fill="url(#ipg)"/>
  <rect x="30" y="30" width="16" height="240" rx="10" fill="{border}" opacity="0.6"/>
  <rect x="46" y="30" width="724" height="90" rx="10" fill="white" opacity="0.1"/>
  <rect x="46" y="46" width="738" height="208" rx="7" fill="none" stroke="{border}" stroke-width="1.5" opacity="0.4"/>
  <circle cx="70" cy="150" r="6" fill="{border}" opacity="0.7"/>
  <circle cx="730" cy="150" r="6" fill="{border}" opacity="0.7"/>
  <line x1="90" y1="130" x2="710" y2="130" stroke="{border}" stroke-width="1.5" opacity="0.35"/>
  <text x="400" y="97" font-family="Arial Black,sans-serif" font-size="26" fill="{border}" text-anchor="middle" dominant-baseline="middle" opacity="0.2">ЗАГОЛОВОК</text>
  <text x="400" y="165" font-family="Arial,sans-serif" font-size="17" fill="{border}" text-anchor="middle" dominant-baseline="middle" opacity="0.16">Информационный текст</text>
  <text x="400" y="196" font-family="Arial,sans-serif" font-size="13" fill="{border}" text-anchor="middle" dominant-baseline="middle" opacity="0.12">Дополнительная строка</text>
</svg>'''
    return svg.encode()


# ─────────────────────────────────────────────
#  COMMAND
# ─────────────────────────────────────────────

class Command(BaseCommand):
    help = 'Seed the database with rich sample product data (per-color images)'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true',
                            help='Delete all products/categories before seeding')

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write(self.style.WARNING('Resetting…'))
            from configurator.models import SavedConfiguration
            SavedConfiguration.objects.all().delete()
            ConfiguratorTemplate.objects.all().delete()
            TextFieldConfig.objects.all().delete()
            AttributeOption.objects.all().delete()
            AttributeGroup.objects.all().delete()
            ProductSize.objects.all().delete()
            Product.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Reset complete.'))

        for d in ('products', 'categories', 'options'):
            os.makedirs(os.path.join(settings.MEDIA_ROOT, d), exist_ok=True)

        self._fonts()
        tab, kub, roz = self._categories()
        self._tablichka_na_dver(tab)
        self._tablichka_info(tab)
        self._tablichka_kabinet(tab)
        self._kubok_sportivnyj(kub)
        self._kubok_kristall(kub)
        self._medal(roz)
        self._rozetka(roz)
        self._znachok(roz)
        self.stdout.write(self.style.SUCCESS('\n✓ Done!'))

    # helpers
    def _img(self, obj, name, data):
        if not obj.image or not obj.image.name:
            obj.image.save(name, ContentFile(data), save=True)

    def _fonts(self):
        for i, (n, css) in enumerate([
            ('Arial', 'Arial, Helvetica, sans-serif'),
            ('Times New Roman', '"Times New Roman", Times, serif'),
            ('Georgia', 'Georgia, serif'),
            ('Courier New', '"Courier New", Courier, monospace'),
            ('Verdana', 'Verdana, Geneva, sans-serif'),
            ('Trebuchet MS', '"Trebuchet MS", sans-serif'),
        ]):
            FontChoice.objects.get_or_create(name=n, defaults={'css_family': css, 'sort_order': i})

    def _categories(self):
        t, _ = Category.objects.get_or_create(slug='tablichki', defaults={
            'name': 'Таблички', 'sort_order': 1,
            'description': 'Именные и дверные таблички на заказ. Латунь, алюминий, нержавеющая сталь.'})
        k, _ = Category.objects.get_or_create(slug='kubki', defaults={
            'name': 'Кубки', 'sort_order': 2,
            'description': 'Спортивные и наградные кубки с гравировкой.'})
        r, _ = Category.objects.get_or_create(slug='rozetki', defaults={
            'name': 'Розетки и Медали', 'sort_order': 3,
            'description': 'Наградные розетки, медали и значки.'})
        return t, k, r

    def _get_or_create_group(self, product, slug, name, widget, order):
        g, _ = AttributeGroup.objects.get_or_create(
            product=product, slug=slug,
            defaults={'name': name, 'widget_type': widget, 'sort_order': order})
        return g

    def _get_or_create_option(self, group, slug, name, **kw):
        o, _ = AttributeOption.objects.get_or_create(group=group, slug=slug, defaults={'name': name, **kw})
        return o

    # ── Табличка на дверь ─────────────────────────────────────────────────────

    def _tablichka_na_dver(self, cat):
        p, _ = Product.objects.get_or_create(slug='tablichka-na-dver', defaults={
            'category': cat, 'name': 'Табличка на дверь', 'base_price': 1500,
            'description': ('Классическая именная табличка для офиса или дома. '
                            'Изготавливается из металла с высококачественной гравировкой. '
                            'Выберите материал, цвет и введите нужный текст.'),
        })
        self._img(p, 'tablichka-na-dver.svg', _plate_svg('#d4a843', '#b8860b', '#8b6914'))

        g_mat = self._get_or_create_group(p, 'material', 'Материал', 'radio', 1)
        self._get_or_create_option(g_mat, 'brass',    'Латунь',              price_modifier=0,    is_default=True, sort_order=1)
        self._get_or_create_option(g_mat, 'aluminum', 'Алюминий',            price_modifier=-200, sort_order=2)
        self._get_or_create_option(g_mat, 'steel',    'Нержавеющая сталь',   price_modifier=300,  sort_order=3)

        g_col = self._get_or_create_group(p, 'color', 'Цвет', 'color', 2)
        o_gld = self._get_or_create_option(g_col, 'gold',   'Золото',  color_hex='#D4A843', is_default=True, sort_order=1)
        o_slv = self._get_or_create_option(g_col, 'silver', 'Серебро', color_hex='#B8B8B8', price_modifier=-100, sort_order=2)
        o_brz = self._get_or_create_option(g_col, 'bronze', 'Бронза',  color_hex='#CD7F32', price_modifier=100,  sort_order=3)
        self._img(o_gld, 'plate-gold.svg',   _plate_svg('#e8c96a', '#c49b28', '#8b6914'))
        self._img(o_slv, 'plate-silver.svg', _plate_svg('#e0e0e0', '#9e9e9e', '#616161'))
        self._img(o_brz, 'plate-bronze.svg', _plate_svg('#cd9b5a', '#8b5a2b', '#5d3a1a'))

        if not p.text_fields.exists():
            TextFieldConfig.objects.create(product=p, label='ФИО',
                placeholder='Иванов И.И.', max_length=40, sort_order=1,
                preview_x=300, preview_y=155, preview_font_size=30,
                preview_color='#1a1a1a', preview_max_width=480, is_required=True)
            TextFieldConfig.objects.create(product=p, label='Должность',
                placeholder='Директор', max_length=60, sort_order=2,
                preview_x=300, preview_y=218, preview_font_size=18,
                preview_color='#555555', preview_max_width=480, is_required=False)

        if not p.sizes.exists():
            for n,w,h,mod,dflt in [('A5',148,210,0,True),('A4',210,297,200,False),('A3',297,420,500,False)]:
                ProductSize.objects.create(product=p, name=n, width=w, height=h, unit='mm', price_modifier=mod, is_default=dflt)

        ConfiguratorTemplate.objects.get_or_create(product=p, defaults={
            'width': 600, 'height': 400,
            'layers_config': {'background_color': '#f5f0e8', 'border_radius': 12,
                'extra_decorations': [
                    {'type':'line','x1':50,'y1':120,'x2':550,'y2':120,'stroke':'#c8b88a','stroke_width':2},
                    {'type':'line','x1':50,'y1':280,'x2':550,'y2':280,'stroke':'#c8b88a','stroke_width':2},
                ]},
        })
        self.stdout.write(f'  ~ {p.name}')

    # ── Табличка информационная ────────────────────────────────────────────────

    def _tablichka_info(self, cat):
        p, _ = Product.objects.get_or_create(slug='tablichka-informacionnaya', defaults={
            'category': cat, 'name': 'Табличка информационная', 'base_price': 1200,
            'description': ('Информационная вывеска для входных дверей и помещений. '
                            'Двустрочная гравировка: заголовок и информационный текст.'),
        })
        self._img(p, 'tablichka-informacionnaya.svg', _info_plate_svg('#d4a843', '#b8860b', '#8b6914'))

        g_col = self._get_or_create_group(p, 'color', 'Цвет', 'color', 1)
        o_gld = self._get_or_create_option(g_col, 'gold',   'Золото',  color_hex='#D4A843', is_default=True, sort_order=1)
        o_slv = self._get_or_create_option(g_col, 'silver', 'Серебро', color_hex='#C0C0C0', price_modifier=-80, sort_order=2)
        o_blk = self._get_or_create_option(g_col, 'black',  'Чёрный',  color_hex='#2c2c2c', price_modifier=50, sort_order=3)
        self._img(o_gld, 'iplate-gold.svg',   _info_plate_svg('#e8c96a', '#c49b28', '#8b6914'))
        self._img(o_slv, 'iplate-silver.svg', _info_plate_svg('#e0e0e0', '#9e9e9e', '#616161'))
        self._img(o_blk, 'iplate-black.svg',  _info_plate_svg('#4a4a4a', '#2c2c2c', '#d4a843'))

        if not p.text_fields.exists():
            TextFieldConfig.objects.create(product=p, label='Заголовок',
                placeholder='КАБИНЕТ №101', max_length=50, sort_order=1,
                preview_x=400, preview_y=97, preview_font_size=28,
                preview_color='#1a1a1a', preview_max_width=680, is_required=True,
                preview_font_family='Arial Black, sans-serif', preview_text_anchor='middle')
            TextFieldConfig.objects.create(product=p, label='Информация',
                placeholder='Приём по записи', max_length=80, sort_order=2,
                preview_x=400, preview_y=160, preview_font_size=18,
                preview_color='#3a3a3a', preview_max_width=640, is_required=False,
                preview_text_anchor='middle')
            TextFieldConfig.objects.create(product=p, label='Доп. текст',
                placeholder='Пн-Пт 09:00-18:00', max_length=60, sort_order=3,
                preview_x=400, preview_y=195, preview_font_size=14,
                preview_color='#555555', preview_max_width=600, is_required=False,
                preview_text_anchor='middle')

        if not p.sizes.exists():
            for n,w,h,mod,dflt in [('200×100 мм',200,100,0,True),('300×150 мм',300,150,200,False),('400×200 мм',400,200,400,False)]:
                ProductSize.objects.create(product=p, name=n, width=w, height=h, unit='mm', price_modifier=mod, is_default=dflt)

        ConfiguratorTemplate.objects.get_or_create(product=p, defaults={
            'width': 800, 'height': 300,
            'layers_config': {'background_color': '#f0ece0', 'border_radius': 10,
                'extra_decorations': [{'type':'line','x1':80,'y1':130,'x2':720,'y2':130,'stroke':'#c8b88a','stroke_width':2}]},
        })
        self.stdout.write(f'  ~ {p.name}')

    # ── Табличка на кабинет ────────────────────────────────────────────────────

    def _tablichka_kabinet(self, cat):
        p, _ = Product.objects.get_or_create(slug='tablichka-na-kabinet', defaults={
            'category': cat, 'name': 'Табличка на кабинет', 'base_price': 1100,
            'description': ('Офисная именная табличка с именем и должностью сотрудника. '
                            'Крепится на дверь или рядом с рабочим местом. Латунь с гравировкой.'),
        })
        self._img(p, 'tablichka-na-kabinet.svg', _plate_svg('#c8a860','#9a7840','#6a5020','#ffffff'))

        g_col = self._get_or_create_group(p, 'color', 'Отделка', 'color', 1)
        o_gld  = self._get_or_create_option(g_col, 'gold',      'Золото',        color_hex='#D4A843', is_default=True, sort_order=1)
        o_slv  = self._get_or_create_option(g_col, 'silver',    'Серебро',       color_hex='#B8B8B8', price_modifier=-50, sort_order=2)
        o_dark = self._get_or_create_option(g_col, 'dark-gold', 'Тёмное золото', color_hex='#8B6914', price_modifier=150, sort_order=3)
        self._img(o_gld,  'kab-gold.svg',     _plate_svg('#e8d080','#c49828','#8b6914','#1a1a1a'))
        self._img(o_slv,  'kab-silver.svg',   _plate_svg('#e8e8e8','#b0b0b0','#707070','#1a1a1a'))
        self._img(o_dark, 'kab-darkgold.svg', _plate_svg('#a07820','#6a5010','#3a2c08','#f5e8c0'))

        if not p.text_fields.exists():
            TextFieldConfig.objects.create(product=p, label='ФИО',
                placeholder='Петров П.П.', max_length=40, sort_order=1,
                preview_x=300, preview_y=155, preview_font_size=28,
                preview_color='#1a1a1a', preview_max_width=480, is_required=True)
            TextFieldConfig.objects.create(product=p, label='Должность',
                placeholder='Главный специалист', max_length=60, sort_order=2,
                preview_x=300, preview_y=218, preview_font_size=17,
                preview_color='#444444', preview_max_width=460, is_required=False)

        if not p.sizes.exists():
            for n,w,h,mod,dflt in [('A5',148,210,0,True),('A4',210,297,180,False)]:
                ProductSize.objects.create(product=p, name=n, width=w, height=h, unit='mm', price_modifier=mod, is_default=dflt)

        ConfiguratorTemplate.objects.get_or_create(product=p, defaults={
            'width': 600, 'height': 400,
            'layers_config': {'background_color': '#f0ece0', 'border_radius': 10,
                'extra_decorations': [
                    {'type':'line','x1':50,'y1':120,'x2':550,'y2':120,'stroke':'#c8b88a','stroke_width':2},
                    {'type':'line','x1':50,'y1':280,'x2':550,'y2':280,'stroke':'#c8b88a','stroke_width':2},
                ]},
        })
        self.stdout.write(f'  ~ {p.name}')

    # ── Кубок спортивный ──────────────────────────────────────────────────────

    def _kubok_sportivnyj(self, cat):
        p, _ = Product.objects.get_or_create(slug='kubok-sportivnyj', defaults={
            'category': cat, 'name': 'Кубок спортивный', 'base_price': 2800,
            'description': ('Классический наградной кубок с ручками из цинкового сплава '
                            'с гальваническим покрытием. Гравировка на пластине у основания.'),
        })
        self._img(p, 'kubok-sportivnyj.svg', _cup_svg('#f0c040','#c89020','#d4a843'))

        g_col = self._get_or_create_group(p, 'otdelka', 'Отделка', 'color', 1)
        o_gld = self._get_or_create_option(g_col, 'gold',   'Золото',  color_hex='#D4A843', is_default=True, sort_order=1)
        o_slv = self._get_or_create_option(g_col, 'silver', 'Серебро', color_hex='#C0C0C0', price_modifier=-200, sort_order=2)
        o_brz = self._get_or_create_option(g_col, 'bronze', 'Бронза',  color_hex='#CD7F32', price_modifier=-500, sort_order=3)
        self._img(o_gld, 'cup-gold.svg',   _cup_svg('#f5d060','#c89428','#d4a843','#fff'))
        self._img(o_slv, 'cup-silver.svg', _cup_svg('#e8e8e8','#9e9e9e','#b0b0b0','#fff'))
        self._img(o_brz, 'cup-bronze.svg', _cup_svg('#d4956a','#8b4513','#cd7f32','#fff'))

        if not p.text_fields.exists():
            TextFieldConfig.objects.create(product=p, label='Надпись',
                placeholder='Лучший спортсмен 2026', max_length=60, sort_order=1,
                preview_x=300, preview_y=392, preview_font_size=18,
                preview_color='#ffffff', preview_max_width=260, is_required=False,
                preview_font_family='Georgia, serif', preview_text_anchor='middle')

        if not p.sizes.exists():
            for n,w,h,d,mod,dflt in [
                ('Малый (20 см)',100,200,100,0,True),
                ('Средний (30 см)',130,300,130,800,False),
                ('Большой (40 см)',160,400,160,2000,False)]:
                ProductSize.objects.create(product=p, name=n, width=w, height=h, depth=d, unit='mm', price_modifier=mod, is_default=dflt)

        ConfiguratorTemplate.objects.get_or_create(product=p, defaults={
            'width': 500, 'height': 600,
            'layers_config': {'background_color': '#f8f4ee', 'border_radius': 8},
        })
        self.stdout.write(f'  ~ {p.name}')

    # ── Кубок Кристалл ────────────────────────────────────────────────────────

    def _kubok_kristall(self, cat):
        p, _ = Product.objects.get_or_create(slug='kubok-kristall', defaults={
            'category': cat, 'name': 'Кубок «Кристалл»', 'base_price': 4500,
            'description': ('Элегантный гранёный кубок из акрила с металлическим основанием. '
                            'Выглядит как хрусталь. Гравировка лазером. Выберите цвет подсветки.'),
        })
        self._img(p, 'kubok-kristall.svg', _crystal_cup_svg('#a8d8f0','#5090c0','#3070a0'))

        g_col = self._get_or_create_group(p, 'color', 'Цвет', 'color', 1)
        o_blue  = self._get_or_create_option(g_col, 'blue',  'Синий',       color_hex='#4488CC', is_default=True, sort_order=1)
        o_red   = self._get_or_create_option(g_col, 'red',   'Красный',     color_hex='#CC4444', sort_order=2)
        o_green = self._get_or_create_option(g_col, 'green', 'Зелёный',     color_hex='#44AA66', sort_order=3)
        o_clear = self._get_or_create_option(g_col, 'clear', 'Прозрачный',  color_hex='#d0eaf8', price_modifier=-300, sort_order=4)
        self._img(o_blue,  'xtal-blue.svg',  _crystal_cup_svg('#a8d8f0','#3a6ea8','#284e80'))
        self._img(o_red,   'xtal-red.svg',   _crystal_cup_svg('#f0a8a8','#a83a3a','#802828'))
        self._img(o_green, 'xtal-green.svg', _crystal_cup_svg('#a8f0c0','#3aa868','#287848'))
        self._img(o_clear, 'xtal-clear.svg', _crystal_cup_svg('#e8f4fc','#b8d8f0','#8ab8d8'))

        if not p.text_fields.exists():
            TextFieldConfig.objects.create(product=p, label='Надпись на кубке',
                placeholder='За выдающиеся достижения', max_length=70, sort_order=1,
                preview_x=250, preview_y=355, preview_font_size=14,
                preview_color='#ffffff', preview_max_width=200, is_required=False,
                preview_font_family='Georgia, serif', preview_text_anchor='middle')

        if not p.sizes.exists():
            for n,w,h,mod,dflt in [('Настольный',120,180,0,True),('Стандарт',150,250,1000,False),('Представительский',180,320,2500,False)]:
                ProductSize.objects.create(product=p, name=n, width=w, height=h, unit='mm', price_modifier=mod, is_default=dflt)

        ConfiguratorTemplate.objects.get_or_create(product=p, defaults={
            'width': 500, 'height': 580,
            'layers_config': {'background_color': '#f0f4f8', 'border_radius': 8},
        })
        self.stdout.write(f'  ~ {p.name}')

    # ── Медаль за отличие ─────────────────────────────────────────────────────

    def _medal(self, cat):
        p, _ = Product.objects.get_or_create(slug='medal-za-otlichie', defaults={
            'category': cat, 'name': 'Медаль за отличие', 'base_price': 650,
            'description': ('Серебряная медаль на ленте для школьных и студенческих наград. '
                            'Металл с эмалью, диаметр 50 мм. Выберите цвет ленты и отделку.'),
        })
        self._img(p, 'medal-za-otlichie.svg', _medal_svg('#1565c0','#0d47a1'))

        g_rib = self._get_or_create_group(p, 'ribbon-color', 'Цвет ленты', 'color', 1)
        o_blue  = self._get_or_create_option(g_rib, 'blue',  'Синяя',   color_hex='#1565c0', is_default=True, sort_order=1)
        o_red   = self._get_or_create_option(g_rib, 'red',   'Красная', color_hex='#C62828', sort_order=2)
        o_green = self._get_or_create_option(g_rib, 'green', 'Зелёная', color_hex='#2E7D32', sort_order=3)
        self._img(o_blue,  'medal-blue.svg',  _medal_svg('#1565c0','#0d47a1'))
        self._img(o_red,   'medal-red.svg',   _medal_svg('#C62828','#b71c1c'))
        self._img(o_green, 'medal-green.svg', _medal_svg('#2E7D32','#1b5e20'))

        g_fin = self._get_or_create_group(p, 'finish', 'Отделка', 'radio', 2)
        self._get_or_create_option(g_fin, 'silver', 'Серебро', price_modifier=0,   is_default=True, sort_order=1)
        self._get_or_create_option(g_fin, 'gold',   'Золото',  price_modifier=100, sort_order=2)
        self._get_or_create_option(g_fin, 'bronze', 'Бронза',  price_modifier=50,  sort_order=3)

        if not p.text_fields.exists():
            TextFieldConfig.objects.create(product=p, label='Подпись',
                placeholder='Выпускник 2026', max_length=30, sort_order=1,
                preview_x=200, preview_y=358, preview_font_size=22,
                preview_color='#ffffff', preview_max_width=160, is_required=False,
                preview_font_family='Georgia, serif', preview_text_anchor='middle')

        if not p.sizes.exists():
            for n,w,h,mod,dflt in [('50 мм',50,50,0,True),('65 мм',65,65,100,False),('80 мм',80,80,250,False)]:
                ProductSize.objects.create(product=p, name=n, width=w, height=h, unit='mm', price_modifier=mod, is_default=dflt)

        ConfiguratorTemplate.objects.get_or_create(product=p, defaults={
            'width': 400, 'height': 520,
            'layers_config': {'background_color': '#f2f0ea', 'border_radius': 6},
        })
        self.stdout.write(f'  ~ {p.name}')

    # ── Розетка спортивная ────────────────────────────────────────────────────

    def _rozetka(self, cat):
        p, _ = Product.objects.get_or_create(slug='rozetka-sportivnaya', defaults={
            'category': cat, 'name': 'Розетка спортивная', 'base_price': 450,
            'description': ('Наградная розетка с лентами — традиционная спортивная награда. '
                            'Атласная лента с фольгированной отделкой.'),
        })
        self._img(p, 'rozetka-sportivnaya.svg', _rosette_svg('#1565c0','#0a3070'))

        g_col = self._get_or_create_group(p, 'ribbon-color', 'Цвет ленты', 'color', 1)
        o_blue   = self._get_or_create_option(g_col, 'blue',   'Синяя',       color_hex='#1565c0', is_default=True, sort_order=1)
        o_red    = self._get_or_create_option(g_col, 'red',    'Красная',     color_hex='#c62828', sort_order=2)
        o_green  = self._get_or_create_option(g_col, 'green',  'Зелёная',     color_hex='#2e7d32', sort_order=3)
        o_purple = self._get_or_create_option(g_col, 'purple', 'Фиолетовая',  color_hex='#6a1b9a', sort_order=4)
        self._img(o_blue,   'roz-blue.svg',   _rosette_svg('#1565c0','#0a3070'))
        self._img(o_red,    'roz-red.svg',    _rosette_svg('#c62828','#7f0000'))
        self._img(o_green,  'roz-green.svg',  _rosette_svg('#2e7d32','#0a3d0a'))
        self._img(o_purple, 'roz-purple.svg', _rosette_svg('#6a1b9a','#38006b'))

        if not p.text_fields.exists():
            TextFieldConfig.objects.create(product=p, label='Номинация',
                placeholder='1 место', max_length=30, sort_order=1,
                preview_x=220, preview_y=248, preview_font_size=18,
                preview_color='#0a3070', preview_max_width=120, is_required=False,
                preview_font_family='Georgia, serif', preview_text_anchor='middle')

        if not p.sizes.exists():
            for n,w,h,mod,dflt in [('Мини (80 мм)',80,80,0,True),('Стандарт (120 мм)',120,120,100,False),('Большая (180 мм)',180,180,280,False)]:
                ProductSize.objects.create(product=p, name=n, width=w, height=h, unit='mm', price_modifier=mod, is_default=dflt)

        ConfiguratorTemplate.objects.get_or_create(product=p, defaults={
            'width': 440, 'height': 440,
            'layers_config': {'background_color': '#f5f2ec', 'border_radius': 220},
        })
        self.stdout.write(f'  ~ {p.name}')

    # ── Значок именной ────────────────────────────────────────────────────────

    def _znachok(self, cat):
        p, _ = Product.objects.get_or_create(slug='znachok-imennoj', defaults={
            'category': cat, 'name': 'Значок именной', 'base_price': 250,
            'description': ('Круглый нагрудный значок с булавкой. Металлизированная поверхность, '
                            'печать под эпоксидной смолой. Популярен для корпоративных мероприятий.'),
        })
        self._img(p, 'znachok-imennoj.svg', _badge_svg('#D4A843','#8b6914'))

        g_col = self._get_or_create_group(p, 'color', 'Фон значка', 'color', 1)
        o_gld = self._get_or_create_option(g_col, 'gold',   'Золото',  color_hex='#D4A843', is_default=True, sort_order=1)
        o_slv = self._get_or_create_option(g_col, 'silver', 'Серебро', color_hex='#C0C0C0', sort_order=2)
        o_blk = self._get_or_create_option(g_col, 'black',  'Чёрный',  color_hex='#1a1a1a', price_modifier=30, sort_order=3)
        o_wht = self._get_or_create_option(g_col, 'white',  'Белый',   color_hex='#f5f5f5', sort_order=4)
        self._img(o_gld, 'badge-gold.svg',   _badge_svg('#e8c96a','#8b6914'))
        self._img(o_slv, 'badge-silver.svg', _badge_svg('#e0e0e0','#707070','#222'))
        self._img(o_blk, 'badge-black.svg',  _badge_svg('#2a2a2a','#d4a843','#f5e8c0'))
        self._img(o_wht, 'badge-white.svg',  _badge_svg('#f5f5f5','#c0a050','#1a1a1a'))

        if not p.text_fields.exists():
            TextFieldConfig.objects.create(product=p, label='Имя',
                placeholder='Александра', max_length=30, sort_order=1,
                preview_x=180, preview_y=168, preview_font_size=20,
                preview_color='#1a1a1a', preview_max_width=240, is_required=True,
                preview_text_anchor='middle')
            TextFieldConfig.objects.create(product=p, label='Должность',
                placeholder='Консультант', max_length=40, sort_order=2,
                preview_x=180, preview_y=200, preview_font_size=14,
                preview_color='#444444', preview_max_width=240, is_required=False,
                preview_text_anchor='middle')

        if not p.sizes.exists():
            for n,d,mod,dflt in [('44 мм',44,0,True),('56 мм',56,50,False),('75 мм',75,120,False)]:
                ProductSize.objects.create(product=p, name=n, width=d, height=d, unit='mm', price_modifier=mod, is_default=dflt)

        ConfiguratorTemplate.objects.get_or_create(product=p, defaults={
            'width': 360, 'height': 360,
            'layers_config': {'background_color': '#f8f4ee', 'border_radius': 180},
        })
        self.stdout.write(f'  ~ {p.name}')
