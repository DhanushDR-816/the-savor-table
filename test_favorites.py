import unittest
from app import create_app
from models import db, User, Category, Recipe, Favorite

class FavoriteTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()

        with self.app.app_context():
            db.drop_all()
            db.create_all()

            # Seed Category
            cat = Category(name='Italian')
            db.session.add(cat)
            db.session.commit()

            # Seed Admin User
            admin = User(name='Admin User', email='admin_test@test.com', role='admin')
            admin.set_password('password123')
            db.session.add(admin)

            # Seed Normal User 1
            user1 = User(name='Normal User 1', email='user1@test.com', role='user')
            user1.set_password('password123')
            db.session.add(user1)

            # Seed Normal User 2
            user2 = User(name='Normal User 2', email='user2@test.com', role='user')
            user2.set_password('password123')
            db.session.add(user2)

            db.session.commit()

            # Seed Recipes
            r1 = Recipe(
                title='Test Recipe 1',
                description='Delicious test recipe 1',
                category_id=cat.id,
                cuisine='Italian',
                author_id=admin.id,
                instructions='Step 1...'
            )
            r2 = Recipe(
                title='Test Recipe 2',
                description='Delicious test recipe 2',
                category_id=cat.id,
                cuisine='Mexican',
                author_id=user1.id,
                instructions='Step 1...'
            )
            db.session.add_all([r1, r2])
            db.session.commit()

            self.r1_id = r1.id
            self.r2_id = r2.id
            self.user1_id = user1.id
            self.user2_id = user2.id
            self.admin_id = admin.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def login(self, email, password):
        return self.client.post('/login', data={'email': email, 'password': password}, follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)

    # 1. Logged-out user visits collections
    def test_01_logged_out_visits_collections(self):
        res = self.client.get('/collections', follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.location)

    # 2. Logged-in user visits collections
    def test_02_logged_in_visits_collections(self):
        self.login('user1@test.com', 'password123')
        res = self.client.get('/collections')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Your Saved Recipes', res.data)
        self.assertIn(b'Your table is waiting', res.data)

    # 3. Save recipe
    def test_03_save_recipe(self):
        self.login('user1@test.com', 'password123')
        res = self.client.post(f'/recipes/{self.r1_id}/favorite', headers={'X-Requested-With': 'XMLHttpRequest'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertTrue(data['is_favorite'])

        with self.app.app_context():
            fav = Favorite.query.filter_by(user_id=self.user1_id, recipe_id=self.r1_id).first()
            self.assertIsNotNone(fav)

    # 4 & 5. Save same recipe twice and verify no duplicate favorite
    def test_04_save_same_recipe_twice_no_duplicate(self):
        self.login('user1@test.com', 'password123')
        self.client.post(f'/recipes/{self.r1_id}/favorite', headers={'X-Requested-With': 'XMLHttpRequest'})
        self.client.post(f'/recipes/{self.r1_id}/favorite', headers={'X-Requested-With': 'XMLHttpRequest'})

        with self.app.app_context():
            fav_count = Favorite.query.filter_by(user_id=self.user1_id, recipe_id=self.r1_id).count()
            self.assertEqual(fav_count, 1)

    # 6. Verify saved state on recipe details
    def test_05_verify_saved_state_on_recipe_details(self):
        self.login('user1@test.com', 'password123')
        self.client.post(f'/recipes/{self.r1_id}/favorite')
        res = self.client.get(f'/recipes/{self.r1_id}')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Saved', res.data)

    # 7 & 8. Unsave recipe and verify recipe disappears from collections
    def test_06_unsave_recipe_and_verify_collections(self):
        self.login('user1@test.com', 'password123')
        self.client.post(f'/recipes/{self.r1_id}/favorite')

        # Unsave
        res = self.client.post(f'/recipes/{self.r1_id}/unfavorite', headers={'X-Requested-With': 'XMLHttpRequest'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertFalse(data['is_favorite'])

        with self.app.app_context():
            fav = Favorite.query.filter_by(user_id=self.user1_id, recipe_id=self.r1_id).first()
            self.assertIsNone(fav)

        res_col = self.client.get('/collections')
        self.assertNotIn(b'Test Recipe 1', res_col.data)

    # 9 & 10. Save multiple recipes and verify only current user's recipes appear
    def test_07_multiple_users_collections_isolation(self):
        # User 1 saves Recipe 1
        self.login('user1@test.com', 'password123')
        self.client.post(f'/recipes/{self.r1_id}/favorite')
        self.logout()

        # User 2 saves Recipe 2
        self.login('user2@test.com', 'password123')
        self.client.post(f'/recipes/{self.r2_id}/favorite')

        # User 2 collections check
        res2 = self.client.get('/collections')
        self.assertIn(b'Test Recipe 2', res2.data)
        self.assertNotIn(b'Test Recipe 1', res2.data)

    # 11. Delete recipe and verify favorite cleanup
    def test_08_delete_recipe_favorite_cleanup(self):
        self.login('user1@test.com', 'password123')
        self.client.post(f'/recipes/{self.r1_id}/favorite')

        # Admin deletes Recipe 1
        self.logout()
        self.login('admin_test@test.com', 'password123')
        self.client.post(f'/recipes/{self.r1_id}/delete')

        with self.app.app_context():
            fav_count = Favorite.query.filter_by(recipe_id=self.r1_id).count()
            self.assertEqual(fav_count, 0)

    # 12. Logout/login persistence check
    def test_09_logout_login_persistence(self):
        self.login('user1@test.com', 'password123')
        self.client.post(f'/recipes/{self.r2_id}/favorite')
        self.logout()

        self.login('user1@test.com', 'password123')
        res = self.client.get('/collections')
        self.assertIn(b'Test Recipe 2', res.data)

if __name__ == '__main__':
    unittest.main()
