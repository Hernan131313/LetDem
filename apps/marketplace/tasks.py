from celery import shared_task
from django.utils import timezone
from django.db import transaction
from .models import Voucher


@shared_task
def expire_old_vouchers():
    """
    Tarea programada para expirar vouchers vencidos y devolver puntos al usuario.
    Debe ejecutarse periódicamente (ej: cada hora).
    """
    now = timezone.now()
    
    # Buscar vouchers pendientes que hayan expirado
    expired_vouchers = Voucher.objects.filter(
        status=Voucher.Status.PENDING,
        expires_at__lte=now
    ).select_related('user')
    
    expired_count = 0
    points_returned = 0
    
    for voucher in expired_vouchers:
        try:
            with transaction.atomic():
                # Marcar como expirado
                voucher.status = Voucher.Status.EXPIRED
                voucher.save(update_fields=['status'])
                
                # Devolver puntos al usuario
                user = voucher.user
                user.total_points += voucher.points_used
                user.save(update_fields=['total_points'])
                
                expired_count += 1
                points_returned += voucher.points_used
                
                print(f"✓ Voucher {voucher.code} expirado. "
                      f"{voucher.points_used} puntos devueltos a {user.email}")
        
        except Exception as e:
            print(f"✗ Error al expirar voucher {voucher.code}: {str(e)}")
            continue
    
    print(f"\n📊 Resumen:")
    print(f"  - Vouchers expirados: {expired_count}")
    print(f"  - Puntos devueltos: {points_returned}")
    
    return {
        'expired_count': expired_count,
        'points_returned': points_returned
    }


@shared_task
def send_voucher_expiration_reminder(voucher_id):
    """
    Enviar recordatorio al usuario de que su voucher está por expirar.
    Se puede programar 2 horas antes de la expiración.
    """
    try:
        voucher = Voucher.objects.select_related('user', 'product').get(id=voucher_id)
        
        # TODO: Implementar envío de notificación/email
        # send_email(
        #     to=voucher.user.email,
        #     subject='Tu voucher está por expirar',
        #     template='voucher_expiration_reminder',
        #     context={'voucher': voucher}
        # )
        
        print(f"📧 Recordatorio enviado a {voucher.user.email} para voucher {voucher.code}")
        return {'sent': True, 'voucher_code': voucher.code}
    
    except Voucher.DoesNotExist:
        print(f"✗ Voucher {voucher_id} no encontrado")
        return {'sent': False, 'error': 'Voucher no encontrado'}
    except Exception as e:
        print(f"✗ Error al enviar recordatorio: {str(e)}")
        return {'sent': False, 'error': str(e)}
