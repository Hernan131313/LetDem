from django.core.management.base import BaseCommand
from marketplace.models import Category, Store, Product
from decimal import Decimal


class Command(BaseCommand):
    help = 'Populate marketplace with sample data'

    def handle(self, *args, **options):
        self.stdout.write('🌱 Populating marketplace...')

        # Create Categories
        categories_data = [
            {'name': 'technology', 'display_name': 'Tecnología', 'icon': '💻'},
            {'name': 'sports', 'display_name': 'Deportes', 'icon': '⚽'},
            {'name': 'automotive', 'display_name': 'Automotriz', 'icon': '🚗'},
        ]

        categories = {}
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'display_name': cat_data['display_name'],
                    'icon': cat_data['icon']
                }
            )
            categories[cat_data['name']] = category
            if created:
                self.stdout.write(f'  ✅ Created category: {category.display_name}')

        # Create Stores
        stores_data = [
            {
                'name': 'NVIDIA Store',
                'description': 'La mejor tecnología en tarjetas gráficas y procesamiento',
                'category': 'technology',
                'image_url': '',
                'latitude': Decimal('40.416775'),
                'longitude': Decimal('-3.703790'),
                'address': 'Gran Vía, 28, Madrid',
                'phone': '+34 900 123 456',
                'is_open': True,
                'opening_hours': '10:00 - 22:00',
                'rating': Decimal('4.8'),
                'review_count': 1250,
            },
            {
                'name': 'Nike Store',
                'description': 'Todo en ropa y calzado deportivo de alta calidad',
                'category': 'sports',
                'image_url': '',
                'latitude': Decimal('40.420000'),
                'longitude': Decimal('-3.705000'),
                'address': 'Calle Serrano, 88, Madrid',
                'phone': '+34 900 234 567',
                'is_open': True,
                'opening_hours': '10:00 - 21:00',
                'rating': Decimal('4.6'),
                'review_count': 2100,
            },
            {
                'name': 'Atlas Automotive',
                'description': 'Repuestos y accesorios para tu vehículo',
                'category': 'automotive',
                'image_url': '',
                'latitude': Decimal('40.425000'),
                'longitude': Decimal('-3.710000'),
                'address': 'Avenida América, 45, Madrid',
                'phone': '+34 900 345 678',
                'is_open': True,
                'opening_hours': '09:00 - 20:00',
                'rating': Decimal('4.5'),
                'review_count': 850,
            },
        ]

        stores = {}
        for store_data in stores_data:
            category_name = store_data.pop('category')
            store, created = Store.objects.get_or_create(
                name=store_data['name'],
                defaults={
                    **store_data,
                    'category': categories[category_name]
                }
            )
            stores[store.name] = store
            if created:
                self.stdout.write(f'  ✅ Created store: {store.name}')

        # Create Products
        products_data = [
            # NVIDIA Store Products
            {
                'store': 'NVIDIA Store',
                'name': 'NVIDIA GeForce RTX 4090',
                'description': 'La tarjeta gráfica más potente del mercado',
                'image_url': '',
                'price': Decimal('1899.99'),
                'discount': Decimal('10'),
                'stock': 25,
                'rating': Decimal('4.9'),
                'review_count': 450,
            },
            {
                'store': 'NVIDIA Store',
                'name': 'NVIDIA GeForce RTX 4080',
                'description': 'Alto rendimiento para gaming y creación de contenido',
                'image_url': '',
                'price': Decimal('1299.99'),
                'discount': Decimal('5'),
                'stock': 40,
                'rating': Decimal('4.8'),
                'review_count': 380,
            },
            {
                'store': 'NVIDIA Store',
                'name': 'NVIDIA GeForce RTX 4070',
                'description': 'Excelente relación calidad-precio para gamers',
                'image_url': '',
                'price': Decimal('649.99'),
                'discount': Decimal('15'),
                'stock': 60,
                'rating': Decimal('4.7'),
                'review_count': 520,
            },
            # Nike Store Products
            {
                'store': 'Nike Store',
                'name': 'Nike Air Max 270',
                'description': 'Zapatillas con máxima comodidad y estilo',
                'image_url': '',
                'price': Decimal('159.99'),
                'discount': Decimal('20'),
                'stock': 150,
                'rating': Decimal('4.6'),
                'review_count': 890,
            },
            {
                'store': 'Nike Store',
                'name': 'Nike Dri-FIT Sports T-Shirt',
                'description': 'Camiseta deportiva de alta tecnología',
                'image_url': '',
                'price': Decimal('34.99'),
                'discount': Decimal('10'),
                'stock': 300,
                'rating': Decimal('4.5'),
                'review_count': 670,
            },
            {
                'store': 'Nike Store',
                'name': 'Nike Pro Leggings',
                'description': 'Mallas de compresión para máximo rendimiento',
                'image_url': '',
                'price': Decimal('49.99'),
                'discount': Decimal('0'),
                'stock': 200,
                'rating': Decimal('4.7'),
                'review_count': 445,
            },
            # Atlas Automotive Products
            {
                'store': 'Atlas Automotive',
                'name': 'Aceite de Motor 5W-30 Full Synthetic',
                'description': 'Aceite premium para máxima protección del motor',
                'image_url': '',
                'price': Decimal('45.99'),
                'discount': Decimal('5'),
                'stock': 120,
                'rating': Decimal('4.8'),
                'review_count': 320,
            },
            {
                'store': 'Atlas Automotive',
                'name': 'Filtro de Aire de Alto Rendimiento',
                'description': 'Mejora el rendimiento y la eficiencia del combustible',
                'image_url': '',
                'price': Decimal('29.99'),
                'discount': Decimal('10'),
                'stock': 85,
                'rating': Decimal('4.6'),
                'review_count': 210,
            },
            {
                'store': 'Atlas Automotive',
                'name': 'Pastillas de Freno Cerámicas',
                'description': 'Máxima durabilidad y rendimiento de frenado',
                'image_url': '',
                'price': Decimal('89.99'),
                'discount': Decimal('15'),
                'stock': 50,
                'rating': Decimal('4.9'),
                'review_count': 180,
            },
        ]

        for product_data in products_data:
            store_name = product_data.pop('store')
            product, created = Product.objects.get_or_create(
                name=product_data['name'],
                store=stores[store_name],
                defaults=product_data
            )
            if created:
                self.stdout.write(f'  ✅ Created product: {product.name}')

        self.stdout.write(self.style.SUCCESS(f'\n🎉 Marketplace populated successfully!'))
        self.stdout.write(f'  📊 Categories: {Category.objects.count()}')
        self.stdout.write(f'  🏪 Stores: {Store.objects.count()}')
        self.stdout.write(f'  📦 Products: {Product.objects.count()}')
