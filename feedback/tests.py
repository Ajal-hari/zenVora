from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.core import mail
from django.test import TestCase, Client
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch
import re

from .models import RegistrationOTP, Student


class AuthenticationTests(TestCase):
    def student(self, password):
        return Student.objects.create(name='Test Student', email='student@kristujayanti.com', password=password, department='MCA', semester='1', class_name='A')

    def test_legacy_login_preserves_record_and_rotates_session(self):
        student = self.student('legacy-password')
        session = self.client.session
        session['admin_logged_in'] = True
        session.save()
        old_key = session.session_key
        response = self.client.post('/login/', {'email': student.email, 'password': 'legacy-password'})
        self.assertRedirects(response, '/dashboard/', fetch_redirect_response=False)
        self.assertNotEqual(old_key, self.client.session.session_key)
        self.assertNotIn('admin_logged_in', self.client.session)
        student.refresh_from_db()
        self.assertEqual(student.password, 'legacy-password')
        self.assertEqual(self.client.get('/lost-found/').status_code, 200)

    def test_hashed_login_and_invalid_password(self):
        student = self.student(make_password('valid-password'))
        self.client.post('/login/', {'email': student.email, 'password': 'wrong'})
        self.assertNotIn('student_id', self.client.session)
        self.assertEqual(self.client.post('/login/', {'email': student.email, 'password': 'valid-password'}).status_code, 302)
        self.client.get('/logout/')
        self.assertNotIn('student_id', self.client.session)

    def test_admin_requires_active_staff_and_ignores_legacy_flag(self):
        session = self.client.session
        session['admin_logged_in'] = True
        session.save()
        self.assertEqual(self.client.get('/admin-dashboard/').status_code, 302)
        self.assertEqual(self.client.get('/lost-found/admin/').status_code, 302)
        User = get_user_model()
        User.objects.create_user(username='staff', password='staff-password', is_staff=True)
        User.objects.create_user(username='regular', password='staff-password')
        self.client.post('/admin-login/', {'email': 'regular', 'password': 'staff-password'})
        self.assertEqual(self.client.get('/admin-dashboard/').status_code, 302)
        self.client.post('/admin-login/', {'email': 'staff', 'password': 'staff-password'})
        self.assertEqual(self.client.get('/admin-dashboard/').status_code, 200)



class RegistrationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.data = {'name': 'Test Student', 'email': 'new@kristujayanti.com', 'department': 'MCA', 'semester': '1', 'class_name': 'A', 'password': 'secure123', 'confirm_password': 'secure123'}

    def register(self):
        return self.client.post('/register/', self.data)

    def code(self):
        return re.search(r'\b[0-9]{6}\b', mail.outbox[-1].body).group()

    def test_delivery_verification_and_single_use(self):
        response = self.register()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(mail.outbox[-1].to, [self.data['email']])
        self.assertFalse(Student.objects.exists())
        code = self.code()
        record = RegistrationOTP.objects.get()
        self.assertNotEqual(record.verifier, code)
        self.assertTrue(check_password('secure123', self.client.session['registration_data']['password_hash']))
        self.assertRedirects(self.client.post('/verify-otp/', {'otp': code}), '/login/', fetch_redirect_response=False)
        self.assertTrue(check_password('secure123', Student.objects.get().password))
        self.client.post('/verify-otp/', {'otp': code})
        self.assertEqual(Student.objects.count(), 1)
        self.assertFalse(RegistrationOTP.objects.get().verifier)

    def test_incorrect_and_attempt_limit(self):
        self.register()
        code = self.code()
        wrong = '000000' if code != '000000' else '000001'
        for _ in range(5):
            self.client.post('/verify-otp/', {'otp': wrong})
        self.client.post('/verify-otp/', {'otp': code})
        self.assertFalse(Student.objects.exists())
        self.assertEqual(RegistrationOTP.objects.get().attempts, 5)

    def test_expiry(self):
        self.register()
        code = self.code()
        RegistrationOTP.objects.update(created_at=timezone.now() - timedelta(minutes=5))
        self.client.post('/verify-otp/', {'otp': code})
        self.assertFalse(Student.objects.exists())

    def test_resend_cooldown_and_old_code_invalidated(self):
        self.register()
        old_code = self.code()
        self.client.post('/resend-otp/')
        self.assertEqual(len(mail.outbox), 1)
        RegistrationOTP.objects.update(last_sent_at=timezone.now() - timedelta(seconds=61))
        with patch('feedback.views.secrets.randbelow', return_value=(int(old_code) + 1) % 1000000):
            self.client.post('/resend-otp/')
        self.assertEqual(len(mail.outbox), 2)
        self.client.post('/verify-otp/', {'otp': old_code})
        self.assertFalse(Student.objects.exists())
        self.client.post('/verify-otp/', {'otp': self.code()})
        self.assertEqual(Student.objects.count(), 1)

    def test_resend_requires_post_and_csrf(self):
        self.assertEqual(self.client.get('/resend-otp/').status_code, 405)
        self.assertEqual(Client(enforce_csrf_checks=True).post('/resend-otp/').status_code, 403)

    def test_delivery_failure(self):
        with patch('feedback.views.send_mail', side_effect=RuntimeError('private provider information')):
            response = self.register()
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'private provider information')
        self.assertNotContains(response, 'Verification code sent')
        self.assertFalse(Student.objects.exists())
        self.assertFalse(RegistrationOTP.objects.get().verifier)

    def test_duplicate_and_send_limit(self):
        self.register()
        for _ in range(4):
            RegistrationOTP.objects.update(last_sent_at=timezone.now() - timedelta(seconds=61))
            self.client.post('/resend-otp/')
        RegistrationOTP.objects.update(last_sent_at=timezone.now() - timedelta(seconds=61))
        self.client.post('/resend-otp/')
        self.assertEqual(len(mail.outbox), 5)
        Student.objects.create(name='Existing', email=self.data['email'], password='unchanged', department='MCA', semester='1', class_name='A')
        self.client.post('/verify-otp/', {'otp': self.code()})
        self.assertEqual(Student.objects.count(), 1)

    def test_request_throttling(self):
        for _ in range(21):
            self.register()
        self.assertEqual(len(mail.outbox), 1)
        self.assertContains(self.register(), 'Too many requests')

    def test_zero_sent_is_failure(self):
        with patch('feedback.views.send_mail', return_value=0):
            response = self.register()
        self.assertContains(response, 'Email delivery failed')
        self.assertFalse(RegistrationOTP.objects.get().verifier)
