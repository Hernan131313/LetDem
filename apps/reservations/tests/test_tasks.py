def test_cancel_reservation_push(db, reservation_factory, user_factory, mocker):
    user = user_factory(push=True)
    reservation = reservation_factory(reserved_by=user)
    mock_send = mocker.patch("commons.push_notifications.onesignal.handlers.send_push_notification")
    cancel_not_confirmed_reservation_task(reservation.id)
    mock_send.assert_called()
