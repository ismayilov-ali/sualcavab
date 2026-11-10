import unittest
from unittest.mock import patch
import app


class SualCavabAppTestCase(unittest.TestCase):
    def setUp(self):
        app.app.config['TESTING'] = True
        app.app.config['SECRET_KEY'] = 'test_secret_key'
        self.client = app.app.test_client()

    def test_data_loading_success(self):
        """Sualların və düzgün cavabların fayldan uğurla yükləndiyini yoxlayır."""
        self.assertGreater(len(app.BUTUN_SUALAR), 0, "Suallar boş olmamalıdır")
        self.assertGreater(len(app.DUZGUN_CAVABLAR), 0, "Cavablar lüğəti boş olmamalıdır")
        # İlk sualın strukturu yoxlanılır
        first_question = app.BUTUN_SUALAR[0]
        self.assertIsInstance(first_question, list)
        self.assertTrue(first_question[0].startswith("1."))
        # İlk sualın cavabının mövcudluğu
        self.assertIn("1", app.DUZGUN_CAVABLAR)

    def test_missing_files_handling(self):
        """Fayllar tapılmadıqda tətbiqin xəta vermədən boş siyahı saxlamasını yoxlayır."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            app.suallari_yukle()
            self.assertEqual(app.BUTUN_SUALAR, [])

            app.cavablari_yukle()
            self.assertEqual(app.DUZGUN_CAVABLAR, {})

        # Testdən sonra həqiqi məlumatları bərpa edirik
        app.suallari_yukle()
        app.cavablari_yukle()

    def test_index_route(self):
        """Əsas səhifənin (GET /) 200 qaytardığını yoxlayır."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Xo", response.data)  # Xoş gəlmisiniz!

    def test_start_quiz_sequential(self):
        """Sıra ilə rejimində kvizin başladılmasını yoxlayır."""
        response = self.client.get('/start/sequential?start=1')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/quiz'))

        with self.client.session_transaction() as sess:
            self.assertIn('sual_idleri', sess)
            self.assertEqual(sess['current_index'], 0)
            self.assertEqual(len(sess['cavablar']), len(app.BUTUN_SUALAR))

    def test_start_quiz_sequential_custom_offset(self):
        """Sıra ilə rejimində xüsusi başlanğıc nömrəsinin düzgün işləməsini yoxlayır."""
        response = self.client.get('/start/sequential?start=10')
        self.assertEqual(response.status_code, 302)

        with self.client.session_transaction() as sess:
            # 10-cu sual 9-cu indeksdən başlamalıdır
            self.assertEqual(sess['sual_idleri'][0], 9)

    def test_start_quiz_random(self):
        """Təsadüfi rejimdə parametr limitlərinə uyğun sual seçilməsini yoxlayır."""
        response = self.client.get('/start/random?limit=5&range_end=20')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/quiz'))

        with self.client.session_transaction() as sess:
            self.assertEqual(len(sess['sual_idleri']), 5)
            self.assertEqual(sess['current_index'], 0)
            self.assertEqual(len(sess['cavablar']), 5)
            # Seçilən bütün sualların indeksləri 0..19 aralığında olmalıdır
            for s_id in sess['sual_idleri']:
                self.assertLess(s_id, 20)

    def test_start_quiz_out_of_range(self):
        """Həddindən böyük 'start' verildikdə əsas səhifəyə yönləndirməni yoxlayır."""
        response = self.client.get('/start/sequential?start=999999')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/'))

    def test_quiz_without_session(self):
        """Sessiya olmadan /quiz səhifəsinə daxil olduqda əsas səhifəyə yönləndirməni yoxlayır."""
        response = self.client.get('/quiz')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/'))

    def test_quiz_get_with_session(self):
        """Sessiya olduqda /quiz GET sorğusunun düzgün HTML qaytarmasını yoxlayır."""
        with self.client.session_transaction() as sess:
            sess['sual_idleri'] = [0, 1]
            sess['current_index'] = 0
            sess['cavablar'] = ["", ""]

        response = self.client.get('/quiz')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Suallar", response.data)

    def test_quiz_post_submit_answer(self):
        """Cavab göndərildikdə sessiyanın yenilənməsini və növbəti suala keçidi yoxlayır."""
        with self.client.session_transaction() as sess:
            sess['sual_idleri'] = [0, 1]
            sess['current_index'] = 0
            sess['cavablar'] = ["", ""]

        response = self.client.post('/quiz', data={'action': 'submit', 'cavab': '  A  '})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/quiz'))

        with self.client.session_transaction() as sess:
            self.assertEqual(sess['cavablar'][0], 'a')
            self.assertEqual(sess['current_index'], 1)

    def test_quiz_post_finish_redirect_to_result(self):
        """Sonuncu sual cavablandırıldıqda /result səhifəsinə yönləndirməni yoxlayır."""
        with self.client.session_transaction() as sess:
            sess['sual_idleri'] = [0]
            sess['current_index'] = 0
            sess['cavablar'] = [""]

        response = self.client.post('/quiz', data={'action': 'submit', 'cavab': 'b'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/result'))

    def test_quiz_post_prev_action(self):
        """'prev' düyməsinə basıldıqda əvvəlki suala qayıtmanı yoxlayır."""
        with self.client.session_transaction() as sess:
            sess['sual_idleri'] = [0, 1]
            sess['current_index'] = 1
            sess['cavablar'] = ["a", ""]

        response = self.client.post('/quiz', data={'action': 'prev'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/quiz'))

        with self.client.session_transaction() as sess:
            self.assertEqual(sess['current_index'], 0)

    def test_jump_without_session(self):
        """Sessiya olmadan /jump/<index> çağırıldıqda əsas səhifəyə yönləndirməni yoxlayır."""
        response = self.client.get('/jump/1')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/'))

    def test_jump_route(self):
        """Birbaşa sual nömrəsinə sıçrayışı (/jump/<index>) yoxlayır."""
        with self.client.session_transaction() as sess:
            sess['sual_idleri'] = [0, 1, 2]
            sess['current_index'] = 0
            sess['cavablar'] = ["", "", ""]

        # Düzgün indeks
        response = self.client.get('/jump/2')
        self.assertEqual(response.status_code, 302)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess['current_index'], 2)

        # Yanlış indeks (dəyişməməlidir)
        response = self.client.get('/jump/99')
        self.assertEqual(response.status_code, 302)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess['current_index'], 2)

    def test_result_route(self):
        """Nəticələr səhifəsinin (/result) düzgün işləməsini yoxlayır."""
        with self.client.session_transaction() as sess:
            sess['sual_idleri'] = [0]
            sess['current_index'] = 1
            sess['cavablar'] = ["a"]

        response = self.client.get('/result')
        self.assertEqual(response.status_code, 200)

    def test_basic_result_route(self):
        """Sadə nəticələr səhifəsinin (/basic-result) 200 qaytardığını yoxlayır."""
        with self.client.session_transaction() as sess:
            sess['sual_idleri'] = [0]
            sess['current_index'] = 1
            sess['cavablar'] = ["b"]

        response = self.client.get('/basic-result')
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
