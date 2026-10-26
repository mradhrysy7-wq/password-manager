import os
import unittest
import tempfile
import app as flask_app

class SecurityTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, flask_app.DB_PATH = tempfile.mkstemp()
        flask_app.app.config['TESTING'] = True
        flask_app.app.config['WTF_CSRF_ENABLED'] = False
        self.app = flask_app.app.test_client()
        flask_app.init_db()

        # Register User 1
        self.app.post('/register', data={'username': 'user1', 'password': 'password123'})
        # Register User 2
        self.app.post('/register', data={'username': 'user2', 'password': 'password123'})

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(flask_app.DB_PATH)

    def login_user(self, username, password):
        return self.app.post('/login', data={'username': username, 'password': password}, follow_redirects=True)

    def test_idor_on_edit_and_delete(self):
        # User 1 logs in and creates an item
        self.login_user('user1', 'password123')
        self.app.post('/add_item', data={
            'account_type': 'تطبيق',
            'app_name': 'Telegram',
            'app_username': 'user1_tg',
            'email': 'user1@example.com',
            'password': 'secret_password_1'
        }, follow_redirects=True)

        # Logout User 1
        self.app.get('/logout')

        # User 2 logs in
        self.login_user('user2', 'password123')

        # User 2 tries to GET edit page of User 1's item (item_id = 1)
        res_get = self.app.get('/edit/1', follow_redirects=True)
        self.assertNotIn(b'Telegram', res_get.data)

        # User 2 tries to POST edit User 1's item
        res_post = self.app.post('/edit/1', data={
            'app_name': 'Hacked_Name',
            'app_username': 'hacked_username',
            'email': 'hacked@example.com',
            'password': 'hacked_password'
        }, follow_redirects=True)

        # User 2 tries to delete User 1's item
        res_del = self.app.post('/delete/1', follow_redirects=True)

        # User 2 tries to get password of User 1's item
        res_pw = self.app.get('/get_password/1')
        self.assertEqual(res_pw.status_code, 404)

        # Logout User 2 and login User 1 to verify item is intact
        self.app.get('/logout')
        self.login_user('user1', 'password123')
        conn = flask_app.get_db()
        row = conn.execute('SELECT app_name FROM app_accounts WHERE id=1').fetchone()
        conn.close()
        self.assertEqual(row[0], 'Telegram')

    def test_xss_prevention(self):
        # Register user with XSS payload
        xss_payload = "<script>alert('xss')</script>"
        self.app.post('/register', data={'username': xss_payload, 'password': 'password123'})
        res = self.login_user(xss_payload, 'password123')
        self.assertNotIn(xss_payload.encode('utf-8'), res.data)
        self.assertIn(b'&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;', res.data)

    def test_session_cookie_security(self):
        self.login_user('user1', 'password123')
        # Check Flask app session security flags
        self.assertTrue(flask_app.app.config.get('SESSION_COOKIE_HTTPONLY', True))

    def test_contact_form_validation(self):
        res = self.app.post('/contact', data={
            'name': 'Tester',
            'email': 'invalid_email',
            'subject': 'Hello',
            'message': 'World'
        }, follow_redirects=True)
        self.assertIn('يرجى أدخال بريد إلكتروني صحيح.'.encode('utf-8'), res.data)

if __name__ == '__main__':
    unittest.main()
