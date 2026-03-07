from django import forms
from products.models import Category, Product, AttributeGroup, AttributeOption, TextFieldConfig, ProductSize


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'image', 'sort_order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'mgr-input', 'placeholder': 'Название категории'}),
            'description': forms.Textarea(attrs={'class': 'mgr-input', 'rows': 3, 'placeholder': 'Описание'}),
            'sort_order': forms.NumberInput(attrs={'class': 'mgr-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'mgr-checkbox'}),
        }
        labels = {
            'name': 'Название',
            'description': 'Описание',
            'image': 'Изображение',
            'sort_order': 'Порядок сортировки',
            'is_active': 'Активна',
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['category', 'name', 'description', 'base_price', 'image', 'is_active']
        widgets = {
            'category': forms.Select(attrs={'class': 'mgr-input'}),
            'name': forms.TextInput(attrs={'class': 'mgr-input', 'placeholder': 'Название товара'}),
            'description': forms.Textarea(attrs={'class': 'mgr-input', 'rows': 4, 'placeholder': 'Описание товара'}),
            'base_price': forms.NumberInput(attrs={'class': 'mgr-input', 'step': '0.01', 'min': '0'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'mgr-checkbox'}),
        }
        labels = {
            'category': 'Категория',
            'name': 'Название',
            'description': 'Описание',
            'base_price': 'Базовая цена (₽)',
            'image': 'Изображение',
            'is_active': 'Активен',
        }


class AttributeGroupForm(forms.ModelForm):
    class Meta:
        model = AttributeGroup
        fields = ['name', 'widget_type', 'is_required', 'sort_order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'mgr-input'}),
            'widget_type': forms.Select(attrs={'class': 'mgr-input'}),
            'sort_order': forms.NumberInput(attrs={'class': 'mgr-input'}),
            'is_required': forms.CheckboxInput(attrs={'class': 'mgr-checkbox'}),
        }
        labels = {
            'name': 'Название группы',
            'widget_type': 'Тип виджета',
            'is_required': 'Обязательна',
            'sort_order': 'Порядок',
        }


class AttributeOptionForm(forms.ModelForm):
    class Meta:
        model = AttributeOption
        fields = ['name', 'price_modifier', 'color_hex', 'image', 'is_default', 'sort_order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'mgr-input'}),
            'price_modifier': forms.NumberInput(attrs={'class': 'mgr-input', 'step': '0.01'}),
            'color_hex': forms.TextInput(attrs={'class': 'mgr-input', 'placeholder': '#ffffff', 'type': 'color'}),
            'sort_order': forms.NumberInput(attrs={'class': 'mgr-input'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'mgr-checkbox'}),
        }
        labels = {
            'name': 'Название опции',
            'price_modifier': 'Модификатор цены (₽)',
            'color_hex': 'Цвет (HEX)',
            'image': 'Изображение',
            'is_default': 'По умолчанию',
            'sort_order': 'Порядок',
        }


class TextFieldConfigForm(forms.ModelForm):
    class Meta:
        model = TextFieldConfig
        fields = ['label', 'placeholder', 'max_length', 'is_required', 'sort_order',
                  'preview_x', 'preview_y', 'preview_font_size', 'preview_font_family',
                  'preview_color', 'preview_max_width', 'preview_text_anchor']
        widgets = {
            'label': forms.TextInput(attrs={'class': 'mgr-input'}),
            'placeholder': forms.TextInput(attrs={'class': 'mgr-input'}),
            'max_length': forms.NumberInput(attrs={'class': 'mgr-input'}),
            'is_required': forms.CheckboxInput(attrs={'class': 'mgr-checkbox'}),
            'sort_order': forms.NumberInput(attrs={'class': 'mgr-input'}),
            'preview_x': forms.NumberInput(attrs={'class': 'mgr-input', 'step': '1'}),
            'preview_y': forms.NumberInput(attrs={'class': 'mgr-input', 'step': '1'}),
            'preview_font_size': forms.NumberInput(attrs={'class': 'mgr-input', 'step': '1'}),
            'preview_font_family': forms.TextInput(attrs={'class': 'mgr-input'}),
            'preview_color': forms.TextInput(attrs={'class': 'mgr-input', 'placeholder': '#333333', 'type': 'color'}),
            'preview_max_width': forms.NumberInput(attrs={'class': 'mgr-input', 'step': '1'}),
            'preview_text_anchor': forms.Select(
                choices=[('start', 'Левый'), ('middle', 'По центру'), ('end', 'Правый')],
                attrs={'class': 'mgr-input'},
            ),
        }
        labels = {
            'label': 'Подпись поля',
            'placeholder': 'Плейсхолдер',
            'max_length': 'Макс. длина',
            'is_required': 'Обязательное',
            'sort_order': 'Порядок',
            'preview_x': 'Позиция X',
            'preview_y': 'Позиция Y',
            'preview_font_size': 'Размер шрифта',
            'preview_font_family': 'Шрифт',
            'preview_color': 'Цвет текста',
            'preview_max_width': 'Макс. ширина текста',
            'preview_text_anchor': 'Выравнивание',
        }


class ProductSizeForm(forms.ModelForm):
    class Meta:
        model = ProductSize
        fields = ['name', 'width', 'height', 'depth', 'unit', 'price_modifier', 'is_default', 'sort_order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'mgr-input'}),
            'width': forms.NumberInput(attrs={'class': 'mgr-input', 'step': '0.1'}),
            'height': forms.NumberInput(attrs={'class': 'mgr-input', 'step': '0.1'}),
            'depth': forms.NumberInput(attrs={'class': 'mgr-input', 'step': '0.1'}),
            'unit': forms.TextInput(attrs={'class': 'mgr-input', 'placeholder': 'мм'}),
            'price_modifier': forms.NumberInput(attrs={'class': 'mgr-input', 'step': '0.01'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'mgr-checkbox'}),
            'sort_order': forms.NumberInput(attrs={'class': 'mgr-input'}),
        }
        labels = {
            'name': 'Название размера',
            'width': 'Ширина',
            'height': 'Высота',
            'depth': 'Глубина',
            'unit': 'Единица',
            'price_modifier': 'Доплата (₽)',
            'is_default': 'По умолчанию',
            'sort_order': 'Порядок',
        }
