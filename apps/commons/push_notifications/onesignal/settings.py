SPACE_SCHEDULED_IN_PLACE_NOTIFICATION = 'space_scheduled_in_place'
SPACE_OCCUPIED_NOTIFICATION = 'space_occupied'
SPACE_RESERVED_NOTIFICATION = 'space_reserved'
EVENT_CONFIRMED_NOTIFICATION = 'event_confirmed'
ACCOUNT_ACCEPTED_NOTIFICATION = 'account_accepted'
RESERVATION_CONFIRMED_NOTIFICATION = 'reservation_confirmed'
REMIND_CONFIRM_RESERVATION_NOTIFICATION = 'remind_confirm_reservation'
RESERVATION_CANCELLED_REQUESTER = 'reservation_cancelled_requester'
RESERVATION_CANCELLED_OWNER = 'reservation_cancelled_owner'
SPACE_ABOUT_TO_EXPIRE = 'space_about_to_expire'


NOTIFICATION_MESSAGE_SETTINGS = {
    SPACE_SCHEDULED_IN_PLACE_NOTIFICATION: {
        'headings': {'en': 'Space Published', 'es': 'Aparcamiento publicado'},
        'contents': {
            'en': 'A new space has been published {meters} meters around {street_name}',
            'es': 'Aparcamiento publicado a {meters} metros de {street_name}',
        },
    },
    SPACE_OCCUPIED_NOTIFICATION: {
        'headings': {
            'en': 'Space Occupied',
            'es': 'Aparcamiento Ocupado',
        },
        'contents': {
            'en': 'You have earned +{points} LetDem Points for your contribution.',
            'es': 'Acabas de obtener +{points} Puntos LetDem por tu contribución.',
        },
    },
    ACCOUNT_ACCEPTED_NOTIFICATION: {
        'headings': {
            'en': 'Your account is approved',
            'es': 'Tu cuenta ha sido aprobada',
        },
        'contents': {
            'en': 'You are ready to publish paid space and earn money.',
            'es': 'Ahora puedes publicar aparcamientos de pago y ganar dinero.',
        },
    },
    SPACE_RESERVED_NOTIFICATION: {
        'headings': {
            'en': 'Space Reserved',
            'es': 'Aparcamiento reservado',
        },
        'contents': {
            'en': 'You have to get the confirmation code from the space requester to confirm the reservation.',
            'es': 'Tienes que recibir el código de confirmación del solicitante para confirmar la reserva.',
        },
    },
    EVENT_CONFIRMED_NOTIFICATION: {
        'headings': {
            'en': 'Your alert is confirmed by other user',
            'es': 'Tu alerta ha sido confirmada por otro usuario',
        },
        'contents': {
            'en': 'You have earned +{points} LetDem Points for your contribution.',
            'es': 'Acabas de obtener +{points} Puntos LetDem por tu contribución.',
        },
    },
    RESERVATION_CONFIRMED_NOTIFICATION: {
        'headings': {
            'en': 'Reservation confirmed',
            'es': 'Reserva confirmada',
        },
        'contents': {
            'en': 'You have earned +{points} LetDem Points for your contribution.',
            'es': 'Acabas de obtener +{points} Puntos LetDem por tu contribución.',
        },
    },
    SPACE_ABOUT_TO_EXPIRE: {
        'headings': {
            'en': 'Your space expires in {minutes} minutes',
            'es': 'Tu aparcamiento expira en {minutes} minutos',
        },
        'contents': {
            'en': 'Once your paid space is expired, you can publish new one.',
            'es': 'Una vez se expire tu aparcamiento de pago, podrás publicar uno nuevo.',
        },
    },
    REMIND_CONFIRM_RESERVATION_NOTIFICATION: {
        'headings': {
            'en': 'Confirm your reservation',
            'es': 'Confirma tu reserva',
        },
        'contents': {
            'en': 'Your reservation will be cancelled in {minutes} minutes.',
            'es': 'Tu reserva será cancelada en {minutes} minutos.',
        },
    },
    RESERVATION_CANCELLED_REQUESTER: {
        'headings': {
            'en': 'Reservation cancelled',
            'es': 'Reserva cancelada',
        },
        'contents': {
            'en': 'Your reservation has been canceled by the owner. We have refunded to you the full amount of your reservation.',
            'es': 'Tu reserva ha sido cancelada por el propietario. Te hemos devuelto el importe total de la reserva.',
        },
    },
    RESERVATION_CANCELLED_OWNER: {
        'headings': {
            'en': 'Reservation cancelled',
            'es': 'Reserva cancelada',
        },
        'contents': {
            'en': 'Your reservation has been canceled by the requester, we have refunded the full amount of money to the requester.',
            'es': 'Tu reserva ha sido cancelada por el solicitante, hemos devuelto el importe total de la reserva al solicitante.',
        },
    },
}
