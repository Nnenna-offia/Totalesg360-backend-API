from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

from accounts.services import invite as invite_service


User = get_user_model()


class InviteServiceTests(TestCase):
    def test_create_user_with_roles_generates_password_and_creates_user(self):
        email = "temp.user@example.com"
        user, pwd, created = invite_service.create_user_with_roles(
            email=email, first_name="Temp", last_name="User"
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(pwd))
        # default password length from service (get_random_string(16))
        self.assertTrue(len(pwd) >= 8)
        self.assertEqual(created, 0)

    @patch("common.tasks.send_email_task")
    def test_send_temporary_password_email_enqueues_task(self, mock_task):
        mock_task.delay = MagicMock()
        user = User.objects.create_user(username="u1", email="u1@example.com", password="pass")
        sent = invite_service.send_temporary_password_email(user, "tmp-pass-123")
        self.assertTrue(sent)
        mock_task.delay.assert_called()

    @patch("common.tasks.send_email_task")
    @patch("common.email.send_email")
    def test_send_temporary_password_email_fallbacks_to_sync(self, mock_send_email, mock_task):
        # Make the async task's .delay raise so the code falls back to sync send
        mock_task.delay.side_effect = Exception("celery down")
        mock_send_email.return_value = 1
        user = User.objects.create_user(username="u2", email="u2@example.com", password="pass")
        sent = invite_service.send_temporary_password_email(user, "tmp-pass-456")
        self.assertTrue(sent)
        mock_send_email.assert_called()

    @patch("accounts.services.invite.create_and_send_password_reset_otp")
    def test_enqueue_password_reset_returns_true_when_enqueued(self, mock_create):
        mock_create.return_value = (None, True)
        user = User.objects.create_user(username="u3", email="u3@example.com", password="pass")
        res = invite_service.enqueue_password_reset(user)
        self.assertTrue(res)

    @patch("accounts.services.invite.create_and_send_password_reset_otp", side_effect=Exception("fail"))
    def test_enqueue_password_reset_handles_exception(self, mock_create):
        user = User.objects.create_user(username="u4", email="u4@example.com", password="pass")
        res = invite_service.enqueue_password_reset(user)
        self.assertFalse(res)
