from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Voucher


@receiver(pre_save, sender=Voucher)
def return_points_on_expiration(sender, instance, **kwargs):
    """
    Devuelve los puntos al usuario cuando un voucher es marcado como expirado
    """
    # Solo procesar si el voucher ya existe (no es creación)
    if instance.pk:
        try:
            old_voucher = Voucher.objects.get(pk=instance.pk)
            
            # Si cambió de PENDING a EXPIRED, devolver puntos
            if (
                old_voucher.status == Voucher.Status.PENDING and
                instance.status == Voucher.Status.EXPIRED
            ):
                user = instance.user
                user.total_points += instance.points_used
                user.save(update_fields=['total_points'])
                
                # TODO: Enviar notificación al usuario
                # notify_user_voucher_expired(user, instance)
        
        except Voucher.DoesNotExist:
            pass
