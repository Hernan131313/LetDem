from django.core.management.base import BaseCommand
from marketplace.models import Product


class Command(BaseCommand):
    help = 'Actualiza las URLs de las imágenes de productos para usar las imágenes en la carpeta products/'

    def handle(self, *args, **options):
        self.stdout.write('\n🖼️  Actualizando imágenes de productos...')
        
        # Mapeo de nombres de productos a sus imágenes
        product_images = {}
        
        updated_count = 0
        for product in Product.objects.all():
            # Buscar coincidencia por nombre completo o parcial
            for product_name, image_url in product_images.items():
                if product_name.lower() in product.name.lower():
                    old_url = product.image_url
                    product.image_url = image_url
                    product.save()
                    updated_count += 1
                    self.stdout.write(f"  ✅ '{product.name}': {old_url} → {image_url}")
                    break
        
        if updated_count == 0:
            self.stdout.write(self.style.WARNING('\n⚠️  No se actualizó ningún producto'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\n✅ Actualizados {updated_count} productos'))
