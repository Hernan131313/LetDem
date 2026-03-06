from django import forms

from .models import Category, Store, Product


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'display_name', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'slug interno'}),
            'display_name': forms.TextInput(attrs={'placeholder': 'Nombre visible'}),
            'icon': forms.TextInput(attrs={'placeholder': 'Ej: 🛍️ o icon-name'}),
        }


class StoreForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = [
            'name',
            'description',
            'category',
            'image_url',
            'latitude',
            'longitude',
            'address',
            'phone',
            'is_open',
            'opening_hours',
            'rating',
            'review_count',
            'is_active',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'opening_hours': forms.TextInput(attrs={'placeholder': '09:00 - 21:00'}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'store',
            'name',
            'description',
            'image_url',
            'price',
            'discount',
            'stock',
            'rating',
            'review_count',
            'is_active',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
