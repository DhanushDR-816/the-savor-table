import os
import re
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from config import Config
from models import db, User, Category, Recipe, Ingredient, Favorite, Review

# Helper Seed Functions
def seed_default_admin():
    admin_email = 'admin@recipe.com'
    existing_admin = User.query.filter_by(email=admin_email).first()
    if not existing_admin:
        admin_user = User(name='System Admin', email=admin_email, role='admin')
        admin_user.set_password('Admin@123')
        db.session.add(admin_user)
        db.session.commit()


def seed_default_categories():
    default_categories = [
        'Breakfast', 'Lunch', 'Dinner', 'Snacks',
        'Desserts', 'Beverages', 'Vegetarian', 'Non-Vegetarian'
    ]
    for cat_name in default_categories:
        existing = Category.query.filter_by(name=cat_name).first()
        if not existing:
            db.session.add(Category(name=cat_name))
    db.session.commit()


def seed_sample_recipes():
    """Seeds initial high-quality sample recipes with verified food images."""
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        return

    categories_map = {c.name: c.id for c in Category.query.all()}
    def get_cat_id(name):
        return categories_map.get(name) or list(categories_map.values())[0]

    all_seed_recipes = [
        # --- BREAKFAST ---
        {
            'title': 'Masala Dosa',
            'description': 'Crispy golden rice crepes stuffed with spiced potato mash, served with coconut chutney and sambar.',
            'image': 'https://images.unsplash.com/photo-1668236543090-82eba5ee5976?auto=format&fit=crop&w=800&q=80',
            'category_name': 'Breakfast',
            'cuisine': 'Indian',
            'prep_time': 20,
            'cook_time': 15,
            'servings': 4,
            'difficulty': 'Medium',
            'instructions': '1. Heat a flat skillet or tawa until smoking hot.\n2. Pour a ladle of fermented rice batter and spread evenly in concentric circles.\n3. Drizzle oil around the edges and cook until crisp and golden.\n4. Place spiced potato masala in the center and fold the dosa over.\n5. Serve immediately with coconut chutney and sambar.',
            'ingredients': [
                ('Fermented Rice Batter', '2', 'cups'),
                ('Potato Masala', '1.5', 'cups'),
                ('Mustard Seeds', '1/2', 'tsp'),
                ('Onion', '1', 'medium'),
                ('Curry Leaves', '8', 'leaves'),
                ('Turmeric Powder', '1/2', 'tsp'),
                ('Vegetable Oil', '2', 'tbsp')
            ]
        },
        {
            'title': 'Classic French Omelette',
            'description': 'Silky, soft-folded French omelette cooked gently in butter and garnished with fine fresh chives.',
            'image': 'https://images.unsplash.com/photo-1510693206972-df098062cb71?auto=format&fit=crop&w=800&q=80',
            'category_name': 'Breakfast',
            'cuisine': 'French',
            'prep_time': 5,
            'cook_time': 5,
            'servings': 1,
            'difficulty': 'Easy',
            'instructions': '1. Whisk eggs with salt and pepper until smooth and fully blended.\n2. Melt butter in a non-stick skillet over low-medium heat without browning.\n3. Pour in eggs and stir rapidly with a spatula until soft curds form.\n4. Roll into an oval shape while interior remains creamy.\n5. Plate and sprinkle with fresh chives.',
            'ingredients': [
                ('Eggs', '3', 'large'),
                ('Unsalted Butter', '1.5', 'tbsp'),
                ('Fresh Chives', '1', 'tbsp'),
                ('Salt', '1/4', 'tsp'),
                ('Black Pepper', '1/8', 'tsp')
            ]
        },
        {
            'title': 'Avocado Toast',
            'description': 'Crispy toasted sourdough bread topped with creamy mashed avocado, lemon juice, chili flakes, and sea salt.',
            'image': 'https://images.unsplash.com/photo-1588137378633-dea1336ce1e2?auto=format&fit=crop&w=800&q=80',
            'category_name': 'Breakfast',
            'cuisine': 'American',
            'prep_time': 5,
            'cook_time': 5,
            'servings': 2,
            'difficulty': 'Easy',
            'instructions': '1. Toast sourdough slices until golden and crisp.\n2. Mash avocado in a bowl with lemon juice, salt, and pepper.\n3. Spread mashed avocado generously over warm toast.\n4. Drizzle with extra virgin olive oil and sprinkle crushed red pepper flakes.',
            'ingredients': [
                ('Sourdough Bread', '2', 'slices'),
                ('Ripe Avocado', '1', 'whole'),
                ('Lemon Juice', '1', 'tsp'),
                ('Red Pepper Flakes', '1/2', 'tsp'),
                ('Olive Oil', '1', 'tsp'),
                ('Sea Salt', '1/4', 'tsp')
            ]
        },
        {
            'title': 'Vegetable Upma',
            'description': 'Savory South Indian semolina breakfast porridge cooked with roasted cashews, carrots, peas, and mustard tempering.',
            'image': 'https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?auto=format&fit=crop&w=800&q=80',
            'category_name': 'Breakfast',
            'cuisine': 'Indian',
            'prep_time': 10,
            'cook_time': 15,
            'servings': 3,
            'difficulty': 'Easy',
            'instructions': '1. Dry roast semolina (rava) until aromatic and set aside.\n2. Heat ghee, crackle mustard seeds, curry leaves, and green chilies.\n3. Add chopped onions, carrots, and green peas; sauté until soft.\n4. Add boiling water and salt, then slow pour semolina while stirring continuously.\n5. Cover and steam for 3 minutes before serving hot with lemon.',
            'ingredients': [
                ('Semolina (Rava)', '1', 'cup'),
                ('Onion', '1', 'medium'),
                ('Green Peas', '1/4', 'cup'),
                ('Carrots', '1/4', 'cup'),
                ('Mustard Seeds', '1/2', 'tsp'),
                ('Ghee', '2', 'tbsp'),
                ('Ginger', '1', 'tsp')
            ]
        },
        {
            'title': 'Blueberry Pancakes',
            'description': 'Fluffy American buttermilk pancakes bursting with fresh blueberries, served warm with pure maple syrup.',
            'image': 'https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?auto=format&fit=crop&w=800&q=80',
            'category_name': 'Breakfast',
            'cuisine': 'American',
            'prep_time': 10,
            'cook_time': 10,
            'servings': 4,
            'difficulty': 'Easy',
            'instructions': '1. Whisk flour, baking powder, sugar, and salt in a bowl.\n2. In another bowl, combine milk, melted butter, and egg.\n3. Gently fold wet mixture into dry ingredients until just combined.\n4. Pour batter onto hot griddle, drop fresh blueberries on top, and flip when bubbles form.\n5. Serve stacked high with butter and warm maple syrup.',
            'ingredients': [
                ('All-purpose Flour', '1.5', 'cups'),
                ('Fresh Blueberries', '1', 'cup'),
                ('Milk', '1.25', 'cups'),
                ('Eggs', '1', 'whole'),
                ('Butter', '3', 'tbsp'),
                ('Maple Syrup', '1/4', 'cup'),
                ('Baking Powder', '2', 'tsp')
            ]
        },

        # --- LUNCH ---
        {
            'title': 'Chicken Biryani',
            'description': 'Fragrant royal Indian rice dish layered with spiced marinated chicken, caramelized onions, saffron, and fresh mint.',
            'image': 'https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?auto=format&fit=crop&w=800&q=80',
            'category_name': 'Lunch',
            'cuisine': 'Indian',
            'prep_time': 30,
            'cook_time': 45,
            'servings': 6,
            'difficulty': 'Hard',
            'instructions': '1. Marinate chicken with yogurt, ginger, garlic, chili, and garam masala for 1 hour.\n2. Par-boil basmati rice with whole aromatic spices until 70% cooked.\n3. Layer spiced chicken curry, fried onions, mint, coriander, and saffron milk with rice.\n4. Seal pot tightly and cook on low heat (Dum) for 25 minutes.\n5. Gently fluff rice layers and serve hot with cucumber raita.',
            'ingredients': [
                ('Chicken', '750', 'g'),
                ('Basmati Rice', '2', 'cups'),
                ('Yogurt', '1', 'cup'),
                ('Onion', '3', 'large'),
                ('Tomato', '2', 'medium'),
                ('Ginger', '1', 'tbsp'),
                ('Garlic', '1', 'tbsp'),
                ('Garam Masala', '2', 'tsp'),
                ('Saffron', '1', 'pinch'),
                ('Mint Leaves', '1/2', 'cup'),
                ('Ghee', '3', 'tbsp')
            ]
        },
        {
            'title': 'Paneer Tikka Bowl',
            'description': 'Smoky grilled paneer cubes and charred bell peppers over basmati rice, drizzled with mint yogurt chutney.',
            'image': 'https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8?auto=format&fit=crop&w=800&q=80',
            'category_name': 'Lunch',
            'cuisine': 'Indian',
            'prep_time': 20,
            'cook_time': 15,
            'servings': 3,
            'difficulty': 'Medium',
            'instructions': '1. Cube paneer, bell peppers, and onions into 1-inch pieces.\n2. Marinate in yogurt, roasted gram flour, mustard oil, and spices for 20 minutes.\n3. Grill or pan-sear on high heat until edges turn golden brown.\n4. Assemble over fluffy warm basmati rice and garnish with fresh cilantro.',
            'ingredients': [
                ('Paneer', '250', 'g'),
                ('Yogurt', '1/2', 'cup'),
                ('Bell Peppers', '2', 'medium'),
                ('Onion', '1', 'medium'),
                ('Tomato', '1', 'medium'),
                ('Garam Masala', '1', 'tsp'),
                ('Lemon Juice', '1', 'tbsp'),
                ('Basmati Rice', '2', 'cups')
            ]
        },
        {
            'title': 'Chicken Caesar Salad',
            'description': 'Crisp romaine lettuce tossed with grilled chicken breast, crunchy garlic croutons, and creamy Caesar dressing.',
            'image': 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=800&q=80',
            'category_name': 'Lunch',
            'cuisine': 'American',
            'prep_time': 15,
            'cook_time': 10,
            'servings': 2,
            'difficulty': 'Easy',
            'instructions': '1. Season chicken breast with olive oil, garlic powder, salt, and pepper; grill until cooked through.\n2. Chop romaine lettuce into bite-sized pieces and place in salad bowl.\n3. Slice grilled chicken into strips.\n4. Toss lettuce with Caesar dressing, garlic croutons, and shaved parmesan.\n5. Top with sliced chicken and extra black pepper.',
            'ingredients': [
                ('Chicken Breast', '300', 'g'),
                ('Romaine Lettuce', '4', 'cups'),
                ('Parmesan Cheese', '1/2', 'cup'),
                ('Croutons', '1', 'cup'),
                ('Caesar Dressing', '1/4', 'cup'),
                ('Garlic', '2', 'cloves'),
                ('Olive Oil', '1', 'tbsp')
            ]
        },
        {
            'title': 'Mediterranean Chickpea Bowl',
            'description': 'Healthy lunch bowl featuring spiced chickpeas, crisp cucumbers, cherry tomatoes, Kalamata olives, and creamy feta.',
            'image': 'https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=800&q=80',
            'category_name': 'Lunch',
            'cuisine': 'Mediterranean',
            'prep_time': 15,
            'cook_time': 0,
            'servings': 2,
            'difficulty': 'Easy',
            'instructions': '1. Rinse and drain chickpeas.\n2. Dice fresh cucumber, tomatoes, and red onion.\n3. Whisk olive oil, lemon juice, dried oregano, salt, and pepper.\n4. Combine all ingredients in a serving bowl.\n5. Top with crumbled feta cheese and Kalamata olives.',
            'ingredients': [
                ('Chickpeas', '1', 'can'),
                ('Cucumber', '1', 'large'),
                ('Tomato', '2', 'medium'),
                ('Red Onion', '1/2', 'medium'),
                ('Feta Cheese', '100', 'g'),
                ('Kalamata Olives', '1/4', 'cup'),
                ('Olive Oil', '2', 'tbsp'),
                ('Lemon Juice', '1.5', 'tbsp')
            ]
        },
        {
            'title': 'Vegetable Fried Rice',
            'description': 'Wok-tossed jasmine rice with crunchy vegetables, soy sauce, sesame oil, and fragrant garlic spring onions.',
            'image': 'https://images.unsplash.com/photo-1603133872878-684f208fb84b?auto=format&fit=crop&w=800&q=80',
            'category_name': 'Lunch',
            'cuisine': 'Asian',
            'prep_time': 10,
            'cook_time': 10,
            'servings': 3,
            'difficulty': 'Easy',
            'instructions': '1. Heat oil in a wok over high heat; sauté minced garlic and onions until fragrant.\n2. Add finely diced carrots and green peas; stir-fry for 2 minutes.\n3. Add chilled day-old cooked rice, breaking up clumps.\n4. Drizzle dark soy sauce and toasted sesame oil around the rim of the wok.\n5. Toss vigorously for 3 minutes and garnish with sliced spring onions.',
            'ingredients': [
                ('Cooked Rice', '3', 'cups'),
                ('Soy Sauce', '2', 'tbsp'),
                ('Garlic', '4', 'cloves'),
                ('Onion', '1', 'medium'),
                ('Carrots', '1/2', 'cup'),
                ('Green Peas', '1/2', 'cup'),
                ('Spring Onion', '3', 'stalks'),
                ('Sesame Oil', '1', 'tbsp')
            ]
        },

        # --- DINNER ---
        {
            'title': 'Classic Indian Butter Chicken',
            'description': 'Tender marinated chicken chunks cooked in a silky, aromatic tomato and butter gravy finished with cream and spices.',
            'image': 'https://images.unsplash.com/photo-1588166524941-3bf61a9c41db?auto=format&fit=crop&w=800&q=80',
            'category_name': 'Dinner',
            'cuisine': 'Indian',
            'prep_time': 20,
            'cook_time': 30,
            'servings': 4,
            'difficulty': 'Medium',
            'instructions': '1. Marinate chicken in yogurt, ginger, garlic, and garam masala for 30 minutes.\n2. Sear chicken in a pan until lightly charred.\n3. Prepare tomato gravy with butter, onions, cashew paste, and aromatic spices.\n4. Simmer chicken in gravy for 15 minutes.\n5. Finish with fresh cream and dried fenugreek leaves (kasuri methi).',
            'ingredients': [
                ('Chicken Breast', '500', 'g'),
                ('Yogurt', '1/2', 'cup'),
                ('Butter', '3', 'tbsp'),
                ('Tomato Puree', '1.5', 'cups'),
                ('Heavy Cream', '1/4', 'cup'),
                ('Garam Masala', '1', 'tsp'),
                ('Garlic', '4', 'cloves'),
                ('Onion', '1', 'large')
            ]
        },
        {
            'title': 'Creamy Tuscan Garlic Pasta',
            'description': 'A rich, delicious Italian pasta tossed in a creamy garlic sauce with sun-dried tomatoes, fresh spinach, and grated parmesan.',
            'image': 'https://images.unsplash.com/photo-1551183053-bf91a1d81141?auto=format&fit=crop&w=800&q=80',
            'category_name': 'Dinner',
            'cuisine': 'Italian',
            'prep_time': 10,
            'cook_time': 15,
            'servings': 4,
            'difficulty': 'Easy',
            'instructions': '1. Boil pasta in salted water until al dente.\n2. In a skillet, sauté garlic and sun-dried tomatoes in butter.\n3. Pour in heavy cream and simmer until thickened.\n4. Stir in fresh spinach and grated parmesan until wilted.\n5. Toss with cooked pasta and serve warm.',
            'ingredients': [
                ('Fettuccine Pasta', '300', 'g'),
                ('Heavy Cream', '1', 'cup'),
                ('Garlic', '4', 'cloves'),
                ('Sun-dried Tomatoes', '1/2', 'cup'),
                ('Fresh Spinach', '2', 'cups'),
                ('Parmesan Cheese', '1/2', 'cup')
            ]
        },
        {
            'title': 'Woodfired Artisan Margherita Pizza',
            'description': 'Traditional Neapolitan pizza with crisp blistered crust, sweet San Marzano tomato sauce, fresh mozzarella, and aromatic basil leaves.',
            'image': 'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=800&q=80',
            'category_name': 'Dinner',
            'cuisine': 'Italian',
            'prep_time': 15,
            'cook_time': 12,
            'servings': 2,
            'difficulty': 'Medium',
            'instructions': '1. Stretch fermented pizza dough into a 12-inch round.\n2. Spread crushed San Marzano tomatoes thinly over base.\n3. Top with torn fresh mozzarella and olive oil drizzle.\n4. Bake at high heat (450°F / 230°C) for 10-12 minutes until bubbly and golden.\n5. Garnish with fresh basil leaves before slicing.',
            'ingredients': [
                ('Pizza Dough', '1', 'ball'),
                ('San Marzano Tomatoes', '1/2', 'cup'),
                ('Fresh Mozzarella', '150', 'g'),
                ('Fresh Basil', '6', 'leaves'),
                ('Extra Virgin Olive Oil', '1', 'tbsp')
            ]
        },
        {
            'title': 'Chicken Tikka Masala',
            'description': 'Juicy grilled chicken tikka simmered in a spiced orange-hued onion-tomato curry sauce enriched with cream.',
            'image': 'https://images.unsplash.com/photo-1565557623262-b51c2513a641?auto=format&fit=crop&w=800&q=80',
            'category_name': 'Dinner',
            'cuisine': 'Indian',
            'prep_time': 20,
            'cook_time': 25,
            'servings': 4,
            'difficulty': 'Medium',
            'instructions': '1. Marinate chicken chunks in spiced yogurt and skewer grill until lightly charred.\n2. Sauté minced garlic, ginger, and onions in butter.\n3. Add tomato puree, garam masala, cumin, and turmeric; simmer for 10 minutes.\n4. Add grilled chicken tikka chunks into sauce and simmer 5 minutes.\n5. Stir in heavy cream and garnish with fresh cilantro.',
            'ingredients': [
                ('Chicken Breast', '500', 'g'),
                ('Yogurt', '1/2', 'cup'),
                ('Tomato Puree', '1.5', 'cups'),
                ('Heavy Cream', '1/4', 'cup'),
                ('Onion', '1', 'large'),
                ('Garlic', '4', 'cloves'),
                ('Ginger', '1', 'tbsp'),
                ('Garam Masala', '1', 'tsp'),
                ('Butter', '2', 'tbsp')
            ]
        },
        {
            'title': 'Mexican Chicken Tacos',
            'description': 'Warm corn tortillas packed with seasoned shredded chicken, diced tomatoes, onions, cilantro, and fresh lime.',
            'image': 'https://images.unsplash.com/photo-1565299585323-38d6b0865b47?auto=format&fit=crop&w=800&q=80',
            'category_name': 'Dinner',
            'cuisine': 'Mexican',
            'prep_time': 15,
            'cook_time': 15,
            'servings': 3,
            'difficulty': 'Easy',
            'instructions': '1. Season chicken with cumin, chili powder, garlic, and salt; cook in a skillet and shred.\n2. Warm corn tortillas on a dry skillet until pliable.\n3. Fill tortillas with shredded chicken, diced tomatoes, onions, and cheese.\n4. Top with chopped cilantro and squeeze fresh lime juice before serving.',
            'ingredients': [
                ('Chicken Breast', '400', 'g'),
                ('Corn Tortillas', '6', 'small'),
                ('Onion', '1', 'medium'),
                ('Garlic', '2', 'cloves'),
                ('Tomato', '2', 'medium'),
                ('Cilantro', '1/4', 'cup'),
                ('Lime', '1', 'whole'),
                ('Cheddar Cheese', '1/2', 'cup')
            ]
        },
        {
            'title': 'Thai Green Curry',
            'description': 'Fragrant coconut green curry with cubed tofu, bamboo shoots, Thai basil leaves, and crisp vegetables.',
            'image': 'https://images.unsplash.com/photo-1455619452474-d2be8b1e70cd?auto=format&fit=crop&w=800&q=80',
            'category_name': 'Dinner',
            'cuisine': 'Thai',
            'prep_time': 15,
            'cook_time': 20,
            'servings': 4,
            'difficulty': 'Medium',
            'instructions': '1. Fry Thai green curry paste in coconut cream until fragrant oil separates.\n2. Add remaining coconut milk, ginger, and garlic; bring to a gentle simmer.\n3. Add pressed tofu cubes, bamboo shoots, and bell peppers.\n4. Simmer for 12 minutes until vegetables are tender.\n5. Tear fresh Thai basil leaves into curry right before serving with jasmine rice.',
            'ingredients': [
                ('Coconut Milk', '2', 'cups'),
                ('Thai Green Curry Paste', '2', 'tbsp'),
                ('Tofu', '300', 'g'),
                ('Bamboo Shoots', '1/2', 'cup'),
                ('Thai Basil', '1/2', 'cup'),
                ('Garlic', '3', 'cloves'),
                ('Ginger', '1', 'tsp'),
                ('Soy Sauce', '1', 'tbsp')
            ]
        },

        # --- SNACKS ---
        {
            'title': 'Samosa',
            'description': 'Golden crispy pastry pockets filled with spicy seasoned potatoes and green peas, served with mint tamarind chutney.',
            'image': 'https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=800&q=80',
            'category_name': 'Snacks',
            'cuisine': 'Indian',
            'prep_time': 30,
            'cook_time': 20,
            'servings': 4,
            'difficulty': 'Medium',
            'instructions': '1. Prepare stiff dough using flour, carom seeds, ghee, and water.\n2. Boil potatoes and mash with green peas, cumin, ginger, chili, and garam masala.\n3. Roll dough, cut into semicircles, cone-shape, and stuff with potato filling.\n4. Deep fry on low-medium heat until golden and crispy.\n5. Serve hot with green mint chutney.',
            'ingredients': [
                ('All-purpose Flour', '2', 'cups'),
                ('Potato', '4', 'large'),
                ('Green Peas', '1/2', 'cup'),
                ('Cumin Seeds', '1', 'tsp'),
                ('Ginger', '1', 'tsp'),
                ('Garam Masala', '1', 'tsp'),
                ('Vegetable Oil', '2', 'cups')
            ]
        },
        {
            'title': 'Bruschetta',
            'description': 'Toasted Italian baguette slices rubbed with garlic and topped with marinated diced tomatoes, basil, and olive oil.',
            'image': 'https://images.unsplash.com/photo-1572695157366-5e585ab2b69f?auto=format&fit=crop&w=800&q=80',
            'category_name': 'Snacks',
            'cuisine': 'Italian',
            'prep_time': 10,
            'cook_time': 5,
            'servings': 4,
            'difficulty': 'Easy',
            'instructions': '1. Slice baguette diagonally and toast until golden crisp.\n2. Rub a peeled garlic clove over hot toasted bread surface.\n3. Combine diced tomatoes, chopped basil, olive oil, balsamic vinegar, salt, and pepper.\n4. Spoon tomato mixture onto garlic toast right before serving.',
            'ingredients': [
                ('Baguette', '1', 'loaf'),
                ('Ripe Tomatoes', '4', 'medium'),
                ('Garlic', '2', 'cloves'),
                ('Fresh Basil', '1/4', 'cup'),
                ('Extra Virgin Olive Oil', '2', 'tbsp'),
                ('Balsamic Vinegar', '1', 'tbsp')
            ]
        },
        {
            'title': 'Crispy Chicken Wings',
            'description': 'Oven-baked crispy chicken wings tossed in a flavorful garlic butter and hot sauce glaze.',
            'image': 'https://images.unsplash.com/photo-1567620832903-9fc6debc209f?auto=format&fit=crop&w=800&q=80',
            'category_name': 'Snacks',
            'cuisine': 'American',
            'prep_time': 10,
            'cook_time': 35,
            'servings': 3,
            'difficulty': 'Easy',
            'instructions': '1. Pat chicken wings dry with paper towels.\n2. Toss wings with baking powder, garlic powder, salt, and black pepper.\n3. Bake on a wire rack at 400°F (200°C) for 35 minutes until golden and extra crispy.\n4. Melt butter with hot sauce and garlic; toss baked wings in glaze before serving.',
            'ingredients': [
                ('Chicken Wings', '1', 'kg'),
                ('Garlic Powder', '1', 'tsp'),
                ('Paprika', '1', 'tsp'),
                ('Butter', '3', 'tbsp'),
                ('Hot Sauce', '1/4', 'cup'),
                ('Black Pepper', '1/2', 'tsp')
            ]
        },
        {
            'title': 'Guacamole & Tortilla Chips',
            'description': 'Fresh creamy guacamole made with ripe Hass avocados, lime juice, tomatoes, onions, cilantro, and warm corn chips.',
            'image': 'https://images.unsplash.com/photo-1541288097308-7b8e3f58c4c6?auto=format&fit=crop&w=800&q=80',
            'category_name': 'Snacks',
            'cuisine': 'Mexican',
            'prep_time': 10,
            'cook_time': 0,
            'servings': 4,
            'difficulty': 'Easy',
            'instructions': '1. Halve avocados, remove pit, and scoop pulp into a bowl.\n2. Mash gently with a fork leaving slight texture.\n3. Stir in finely diced tomatoes, red onion, garlic, cilantro, and lime juice.\n4. Season with salt and pepper.\n5. Serve immediately surrounded by salted corn tortilla chips.',
            'ingredients': [
                ('Ripe Avocados', '3', 'whole'),
                ('Tomato', '1', 'medium'),
                ('Lime Juice', '2', 'tbsp'),
                ('Red Onion', '1/4', 'cup'),
                ('Cilantro', '2', 'tbsp'),
                ('Garlic', '1', 'clove'),
                ('Tortilla Chips', '1', 'bag')
            ]
        },

        # --- DESSERTS ---
        {
            'title': 'Chocolate Lava Cake',
            'description': 'Individual molten dark chocolate cakes with a warm liquid chocolate center, dusted with powdered sugar.',
            'image': 'https://images.unsplash.com/photo-1606313564200-e75d5e30476c?auto=format&fit=crop&w=800&q=80',
            'category_name': 'Desserts',
            'cuisine': 'French',
            'prep_time': 15,
            'cook_time': 12,
            'servings': 2,
            'difficulty': 'Hard',
            'instructions': '1. Melt dark chocolate and butter together until silky smooth.\n2. Whisk eggs, egg yolks, sugar, and vanilla until pale and thick.\n3. Fold chocolate mixture and flour into eggs until just combined.\n4. Divide batter into buttered cocoa-dusted ramekins.\n5. Bake at 425°F (220°C) for 12 minutes until edges are set but center soft. Invert onto plates.',
            'ingredients': [
                ('Dark Chocolate', '100', 'g'),
                ('Butter', '50', 'g'),
                ('Eggs', '2', 'large'),
                ('Sugar', '3', 'tbsp'),
                ('All-purpose Flour', '2', 'tbsp'),
                ('Vanilla Extract', '1/2', 'tsp')
            ]
        },
        {
            'title': 'Classic Tiramisu',
            'description': 'Traditional Italian dessert layered with coffee-soaked ladyfingers, whipped mascarpone cream, and cocoa powder.',
            'image': 'https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?auto=format&fit=crop&w=800&q=80',
            'category_name': 'Desserts',
            'cuisine': 'Italian',
            'prep_time': 25,
            'cook_time': 0,
            'servings': 6,
            'difficulty': 'Medium',
            'instructions': '1. Brew strong espresso coffee and allow to cool completely.\n2. Beat egg yolks and sugar over double boiler; fold in mascarpone cheese and whipped cream.\n3. Dip ladyfinger biscuits quickly into espresso and line bottom of dish.\n4. Spread half the mascarpone cream layer over biscuits.\n5. Repeat with second layer of dipped ladyfingers and cream; dust top generously with cocoa powder. Chill 4 hours.',
            'ingredients': [
                ('Ladyfinger Biscuits', '200', 'g'),
                ('Mascarpone Cheese', '250', 'g'),
                ('Espresso Coffee', '1.5', 'cups'),
                ('Eggs', '3', 'large'),
                ('Heavy Cream', '1', 'cup'),
                ('Cocoa Powder', '2', 'tbsp')
            ]
        },
        {
            'title': 'Mango Cheesecake',
            'description': 'Smooth no-bake cream cheese cake topped with sweet Alphonso mango glaze over a buttery cracker crust.',
            'image': 'https://images.unsplash.com/photo-1533134242443-d4fd215305ad?auto=format&fit=crop&w=800&q=80',
            'category_name': 'Desserts',
            'cuisine': 'International',
            'prep_time': 25,
            'cook_time': 0,
            'servings': 8,
            'difficulty': 'Medium',
            'instructions': '1. Press crushed graham crackers and melted butter into bottom of springform pan.\n2. Beat cream cheese, sugar, and mango puree until smooth.\n3. Fold whipped heavy cream gently into cream cheese mixture.\n4. Pour over crust and refrigerate for 4 hours until firmly set.\n5. Spread fresh mango glaze over top before unclamping springform pan.',
            'ingredients': [
                ('Cream Cheese', '400', 'g'),
                ('Mango Puree', '1', 'cup'),
                ('Graham Cracker Crust', '150', 'g'),
                ('Heavy Cream', '1', 'cup'),
                ('Sugar', '1/2', 'cup'),
                ('Gelatin', '1', 'tbsp')
            ]
        },
        {
            'title': 'Gulab Jamun',
            'description': 'Soft milk-solid dough balls fried to golden perfection and soaked in warm cardamom saffron sugar syrup.',
            'image': 'https://images.unsplash.com/photo-1541781774459-bb2af2f05b55?auto=format&fit=crop&w=800&q=80',
            'category_name': 'Desserts',
            'cuisine': 'Indian',
            'prep_time': 20,
            'cook_time': 15,
            'servings': 5,
            'difficulty': 'Medium',
            'instructions': '1. Simmer sugar, water, cardamom, rose water, and saffron to make thin syrup.\n2. Mix milk powder, flour, ghee, and milk to form soft smooth dough.\n3. Roll into crack-free small balls.\n4. Deep fry on low flame until uniform golden dark brown.\n5. Transfer hot jamuns into warm sugar syrup; soak for at least 2 hours.',
            'ingredients': [
                ('Milk Powder', '1', 'cup'),
                ('All-purpose Flour', '1/4', 'cup'),
                ('Ghee', '2', 'tbsp'),
                ('Sugar', '1.5', 'cups'),
                ('Cardamom', '4', 'pods'),
                ('Rose Water', '1', 'tsp'),
                ('Saffron', '1', 'pinch')
            ]
        },

        # --- BEVERAGES ---
        {
            'title': 'Mango Lassi',
            'description': 'Refreshing chilled Indian yogurt drink blended with sweet ripe mangoes, milk, cardamom, and ice.',
            'image': 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?auto=format&fit=crop&w=800&q=80',
            'category_name': 'Beverages',
            'cuisine': 'Indian',
            'prep_time': 5,
            'cook_time': 0,
            'servings': 2,
            'difficulty': 'Easy',
            'instructions': '1. Add mango pulp, thick yogurt, milk, sugar, and cardamom powder into a blender.\n2. Blend on high speed for 1 minute until completely smooth and frothy.\n3. Add ice cubes and pulse briefly.\n4. Pour into tall chilled glasses and garnish with crushed pistachio nuts.',
            'ingredients': [
                ('Mango Pulp', '1', 'cup'),
                ('Yogurt', '1', 'cup'),
                ('Milk', '1/2', 'cup'),
                ('Sugar', '2', 'tbsp'),
                ('Cardamom Powder', '1/4', 'tsp'),
                ('Ice Cubes', '4', 'cubes')
            ]
        },
        {
            'title': 'Classic Cold Coffee',
            'description': 'Creamy blended iced coffee topped with rich vanilla ice cream and chocolate drizzle.',
            'image': 'https://images.unsplash.com/photo-1517701604599-bb29b565090c?auto=format&fit=crop&w=800&q=80',
            'category_name': 'Beverages',
            'cuisine': 'International',
            'prep_time': 5,
            'cook_time': 0,
            'servings': 2,
            'difficulty': 'Easy',
            'instructions': '1. Dissolve instant coffee powder and sugar in warm water.\n2. Pour coffee mixture into blender with cold milk and ice cubes.\n3. Blend on high until thick and frothy.\n4. Drizzle chocolate syrup around inside of serving glass.\n5. Pour cold coffee and top with a scoop of vanilla ice cream.',
            'ingredients': [
                ('Instant Coffee Powder', '2', 'tbsp'),
                ('Chilled Milk', '2', 'cups'),
                ('Sugar', '2', 'tbsp'),
                ('Vanilla Ice Cream', '2', 'scoops'),
                ('Chocolate Syrup', '2', 'tbsp'),
                ('Ice Cubes', '5', 'cubes')
            ]
        },
        {
            'title': 'Fresh Strawberry Smoothie',
            'description': 'Vibrant fruity smoothie made with sweet strawberries, Greek yogurt, honey, milk, and chia seeds.',
            'image': 'https://images.unsplash.com/photo-1553530666-ba11a7da3888?auto=format&fit=crop&w=800&q=80',
            'category_name': 'Beverages',
            'cuisine': 'American',
            'prep_time': 5,
            'cook_time': 0,
            'servings': 2,
            'difficulty': 'Easy',
            'instructions': '1. Hull fresh strawberries.\n2. Combine strawberries, Greek yogurt, milk, honey, and ice in blender.\n3. Blend until silky smooth.\n4. Pour into glasses and sprinkle chia seeds on top.',
            'ingredients': [
                ('Fresh Strawberries', '1.5', 'cups'),
                ('Yogurt', '1/2', 'cup'),
                ('Honey', '1', 'tbsp'),
                ('Milk', '1/2', 'cup'),
                ('Chia Seeds', '1', 'tsp'),
                ('Ice Cubes', '4', 'cubes')
            ]
        },

        # --- ADD 3 MORE ---
        {
            'title': 'Fresh Avocado & Berry Power Salad',
            'description': 'A vibrant, nutrient-packed salad with creamy avocado slices, fresh blueberries, walnuts, and baby spinach tossed in lemon vinaigrette.',
            'image': 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=800&q=80',
            'category_name': 'Breakfast',
            'cuisine': 'Mediterranean',
            'prep_time': 10,
            'cook_time': 0,
            'servings': 2,
            'difficulty': 'Easy',
            'instructions': '1. Wash baby spinach and place in a large bowl.\n2. Slice fresh avocado and toss with lemon juice to prevent browning.\n3. Add fresh blueberries, crumbled goat cheese, and toasted walnuts.\n4. Whisk olive oil, lemon juice, honey, and black pepper for dressing.\n5. Drizzle dressing over salad right before serving.',
            'ingredients': [
                ('Ripe Avocado', '1', 'whole'),
                ('Baby Spinach', '3', 'cups'),
                ('Fresh Blueberries', '1/2', 'cup'),
                ('Walnuts', '1/4', 'cup'),
                ('Goat Cheese', '50', 'g'),
                ('Olive Oil', '2', 'tbsp')
            ]
        },
        {
            'title': 'Palak Paneer',
            'description': 'Soft cottage cheese cubes cooked in a smooth, fragrant spiced spinach gravy finished with butter and cream.',
            'image': 'https://images.unsplash.com/photo-1610057099443-fde8c4d50f91?auto=format&fit=crop&w=800&q=80',
            'category_name': 'Dinner',
            'cuisine': 'Indian',
            'prep_time': 15,
            'cook_time': 20,
            'servings': 4,
            'difficulty': 'Medium',
            'instructions': '1. Blanch spinach leaves in boiling water for 2 minutes, then plunge into ice water; puree smooth.\n2. Heat butter and oil in pan; sauté cumin, onions, ginger, and garlic.\n3. Add tomato puree, turmeric, chili, and garam masala; cook until oil separates.\n4. Pour in spinach puree and simmer for 5 minutes.\n5. Add paneer cubes and cream; simmer gently for 3 minutes before serving with naan.',
            'ingredients': [
                ('Paneer', '250', 'g'),
                ('Spinach', '500', 'g'),
                ('Onion', '1', 'medium'),
                ('Tomato', '1', 'medium'),
                ('Garlic', '4', 'cloves'),
                ('Ginger', '1', 'tsp'),
                ('Heavy Cream', '2', 'tbsp'),
                ('Garam Masala', '1', 'tsp'),
                ('Butter', '2', 'tbsp')
            ]
        },
        {
            'title': 'Grilled Chicken Sandwich',
            'description': 'Juicy grilled herb chicken breast with lettuce, sliced tomatoes, melted cheese, and garlic mayo on toasted wheat bread.',
            'image': 'https://images.unsplash.com/photo-1528735602780-2552fd46c7af?auto=format&fit=crop&w=800&q=80',
            'category_name': 'Lunch',
            'cuisine': 'American',
            'prep_time': 10,
            'cook_time': 10,
            'servings': 2,
            'difficulty': 'Easy',
            'instructions': '1. Season chicken breast with garlic powder, salt, and pepper; grill until thoroughly cooked.\n2. Toast bread slices with butter on a pan.\n3. Spread garlic mayonnaise over toasted bread slices.\n4. Layer crisp lettuce, grilled chicken breast, cheese, and sliced ripe tomatoes.\n5. Slice diagonally and serve warm.',
            'ingredients': [
                ('Chicken Breast', '300', 'g'),
                ('Whole Wheat Bread', '4', 'slices'),
                ('Lettuce', '2', 'leaves'),
                ('Tomato', '1', 'large'),
                ('Cheddar Cheese', '2', 'slices'),
                ('Mayonnaise', '2', 'tbsp'),
                ('Garlic Powder', '1/2', 'tsp'),
                ('Butter', '1', 'tbsp')
            ]
        }
    ]

    for item in all_seed_recipes:
        existing = Recipe.query.filter_by(title=item['title']).first()
        if existing:
            continue

        cat_id = get_cat_id(item['category_name'])
        recipe = Recipe(
            title=item['title'],
            description=item['description'],
            image=item['image'],
            category_id=cat_id,
            cuisine=item['cuisine'],
            prep_time=item['prep_time'],
            cook_time=item['cook_time'],
            servings=item['servings'],
            difficulty=item['difficulty'],
            instructions=item['instructions'],
            author_id=admin.id
        )
        db.session.add(recipe)
        db.session.flush()

        for ing_name, qty, unit in item['ingredients']:
            db.session.add(Ingredient(
                recipe_id=recipe.id,
                name=ing_name,
                quantity=qty,
                unit=unit
            ))

    db.session.commit()


def create_app():
    """Application factory function to initialize Flask app."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)

    # Ensure database tables exist, seed admin, categories, and sample recipes
    with app.app_context():
        db.create_all()
        seed_default_admin()
        seed_default_categories()
        seed_sample_recipes()

    # Login required decorator helper
    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('login', next=request.url))
            return f(*args, **kwargs)
        return decorated_function

    # ==========================================
    # 1. DISCOVER HOMEPAGE (Minimalist & Clean)
    # ==========================================
    @app.route('/')
    def index():
        # Display max 3 featured recipes on homepage
        recent_recipes = Recipe.query.order_by(Recipe.created_at.desc()).limit(3).all()
        return render_template('index.html', recent_recipes=recent_recipes)

    # ==========================================
    # 2. DEDICATED RECIPE DISCOVERY CATALOG
    # ==========================================
    @app.route('/recipes')
    def recipes_list():
        query = Recipe.query

        # Search parameter
        search_query = request.args.get('q', '').strip()
        if search_query:
            search_pattern = f"%{search_query}%"
            query = query.filter(
                (Recipe.title.ilike(search_pattern)) |
                (Recipe.description.ilike(search_pattern)) |
                (Recipe.cuisine.ilike(search_pattern))
            )

        # Filter by category
        cat_filter = request.args.get('category', type=int)
        if cat_filter:
            query = query.filter(Recipe.category_id == cat_filter)

        # Filter by cuisine
        cuisine_filter = request.args.get('cuisine', '').strip()
        if cuisine_filter:
            query = query.filter(Recipe.cuisine.ilike(cuisine_filter))

        # Filter by difficulty
        diff_filter = request.args.get('difficulty', '').strip()
        if diff_filter:
            query = query.filter(Recipe.difficulty == diff_filter)

        # Sort parameter
        sort_by = request.args.get('sort', 'newest')
        if sort_by == 'oldest':
            query = query.order_by(Recipe.created_at.asc())
        elif sort_by == 'title':
            query = query.order_by(Recipe.title.asc())
        else:
            query = query.order_by(Recipe.created_at.desc())

        recipes = query.all()
        categories = Category.query.order_by(Category.name.asc()).all()

        # Fetch distinct cuisines for filter dropdown
        cuisines_raw = db.session.query(Recipe.cuisine).filter(
            Recipe.cuisine.isnot(None), Recipe.cuisine != ''
        ).distinct().all()
        cuisines = sorted([c[0] for c in cuisines_raw if c[0]])

        user_favorite_ids = set()
        if 'user_id' in session:
            user_favorite_ids = {fav.recipe_id for fav in Favorite.query.filter_by(user_id=session['user_id']).all()}

        return render_template(
            'recipes.html',
            recipes=recipes,
            categories=categories,
            cuisines=cuisines,
            search_query=search_query,
            active_cat=cat_filter,
            active_cuisine=cuisine_filter,
            active_diff=diff_filter,
            active_sort=sort_by,
            user_favorite_ids=user_favorite_ids
        )

    # ==========================================
    # 3. DEDICATED RECIPE DETAILS PAGE
    # ==========================================
    @app.route('/recipes/<int:recipe_id>')
    def recipe_details(recipe_id):
        recipe = db.session.get(Recipe, recipe_id)
        if not recipe:
            flash('The requested recipe could not be found.', 'danger')
            return redirect(url_for('recipes_list'))

        is_favorite = False
        if 'user_id' in session:
            is_favorite = Favorite.query.filter_by(
                user_id=session['user_id'],
                recipe_id=recipe.id
            ).first() is not None

        return render_template('recipe_details.html', recipe=recipe, is_favorite=is_favorite)

    # ==========================================
    # 4. DEDICATED MY KITCHEN (Pantry Matching)
    # ==========================================
    @app.route('/my-kitchen')
    def my_kitchen():
        pantry_input = request.args.get('ingredients', '').strip()
        matched_recipes = []

        def normalize_ingredient_word(w):
            w = w.lower().strip()
            if len(w) > 4 and w.endswith('ies'):
                return w[:-3] + 'y'
            if len(w) > 3 and w.endswith('es'):
                return w[:-2]
            if len(w) > 3 and w.endswith('s') and not w.endswith('ss'):
                return w[:-1]
            return w

        def normalize_ingredient_text(text):
            if not text:
                return ""
            text = text.lower()
            text = re.sub(r'[^\w\s]', ' ', text)
            words = [normalize_ingredient_word(w) for w in text.split()]
            return " ".join(words)

        def is_ingredient_match(user_term, ing_name, ing_unit=""):
            t_norm = normalize_ingredient_text(user_term)
            if not t_norm:
                return False
            ing_name_norm = normalize_ingredient_text(ing_name)
            ing_full_norm = normalize_ingredient_text(f"{ing_name} {ing_unit or ''}")

            # 1. Substring match in either direction
            if t_norm in ing_name_norm or t_norm in ing_full_norm:
                return True
            if ing_name_norm in t_norm or ing_full_norm in t_norm:
                return True

            # 2. Word token intersection (ignoring pure numbers)
            t_words = {w for w in t_norm.split() if not w.isdigit()}
            ing_words = {w for w in ing_full_norm.split() if not w.isdigit()}

            if t_words & ing_words:
                return True

            return False

        if pantry_input:
            ingredient_terms = [t.strip() for t in pantry_input.split(',') if t.strip()]
            all_recipes = Recipe.query.all()

            for recipe in all_recipes:
                if not recipe.ingredients:
                    continue

                match_count = 0
                available = []
                missing = []

                for ing in recipe.ingredients:
                    is_matched = False
                    for term in ingredient_terms:
                        if is_ingredient_match(term, ing.name, ing.unit):
                            is_matched = True
                            break

                    if is_matched:
                        match_count += 1
                        available.append(ing.name)
                    else:
                        missing.append(ing.name)

                if match_count > 0:
                    match_percentage = int((match_count / len(recipe.ingredients)) * 100)
                    matched_recipes.append({
                        'recipe': recipe,
                        'percentage': match_percentage,
                        'available': available,
                        'missing': missing
                    })

            # Sort matched recipes by match percentage descending
            matched_recipes.sort(key=lambda x: x['percentage'], reverse=True)

        return render_template('my_kitchen.html', pantry_input=pantry_input, matched_recipes=matched_recipes)

    # ==========================================
    # 5. FAVORITE / SAVED COLLECTIONS ENDPOINTS
    # ==========================================
    @app.route('/recipes/<int:recipe_id>/favorite', methods=['POST'])
    def favorite_recipe(recipe_id):
        if 'user_id' not in session:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return {'status': 'error', 'message': 'Please log in to save recipes.', 'redirect': url_for('login')}, 401
            flash('Please log in to save recipes.', 'warning')
            return redirect(url_for('login', next=url_for('recipe_details', recipe_id=recipe_id)))

        recipe = db.session.get(Recipe, recipe_id)
        if not recipe:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return {'status': 'error', 'message': 'Recipe not found.'}, 404
            flash('Recipe not found.', 'danger')
            return redirect(url_for('recipes_list'))

        user_id = session['user_id']
        existing = Favorite.query.filter_by(user_id=user_id, recipe_id=recipe_id).first()

        if not existing:
            new_fav = Favorite(user_id=user_id, recipe_id=recipe_id)
            try:
                db.session.add(new_fav)
                db.session.commit()
            except Exception:
                db.session.rollback()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return {'status': 'success', 'action': 'saved', 'is_favorite': True, 'message': 'Saved to your collection!'}

        flash('Recipe saved to your collection!', 'success')
        return redirect(request.referrer or url_for('recipe_details', recipe_id=recipe_id))

    @app.route('/recipes/<int:recipe_id>/unfavorite', methods=['POST'])
    def unfavorite_recipe(recipe_id):
        if 'user_id' not in session:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return {'status': 'error', 'message': 'Please log in first.', 'redirect': url_for('login')}, 401
            flash('Please log in first.', 'warning')
            return redirect(url_for('login'))

        user_id = session['user_id']
        fav = Favorite.query.filter_by(user_id=user_id, recipe_id=recipe_id).first()

        if fav:
            try:
                db.session.delete(fav)
                db.session.commit()
            except Exception:
                db.session.rollback()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return {'status': 'success', 'action': 'unsaved', 'is_favorite': False, 'message': 'Removed from saved collection.'}

        flash('Recipe removed from your saved collection.', 'info')
        return redirect(request.referrer or url_for('collections'))

    @app.route('/recipes/<int:recipe_id>/toggle-favorite', methods=['POST'])
    def toggle_favorite_recipe(recipe_id):
        if 'user_id' not in session:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return {'status': 'error', 'message': 'Please log in to save recipes.', 'redirect': url_for('login')}, 401
            flash('Please log in to save recipes.', 'warning')
            return redirect(url_for('login'))

        recipe = db.session.get(Recipe, recipe_id)
        if not recipe:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return {'status': 'error', 'message': 'Recipe not found.'}, 404
            flash('Recipe not found.', 'danger')
            return redirect(url_for('recipes_list'))

        user_id = session['user_id']
        existing = Favorite.query.filter_by(user_id=user_id, recipe_id=recipe_id).first()

        if existing:
            try:
                db.session.delete(existing)
                db.session.commit()
                action = 'unsaved'
                is_fav = False
                msg = 'Removed from saved collection.'
            except Exception:
                db.session.rollback()
                return {'status': 'error', 'message': 'Could not remove favorite.'}, 500
        else:
            new_fav = Favorite(user_id=user_id, recipe_id=recipe_id)
            try:
                db.session.add(new_fav)
                db.session.commit()
                action = 'saved'
                is_fav = True
                msg = 'Saved to your collection!'
            except Exception:
                db.session.rollback()
                return {'status': 'error', 'message': 'Could not save favorite.'}, 500

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return {'status': 'success', 'action': action, 'is_favorite': is_fav, 'message': msg}

        flash(msg, 'success' if is_fav else 'info')
        return redirect(request.referrer or url_for('recipe_details', recipe_id=recipe_id))

    # ==========================================
    # 5. DEDICATED SAVED COLLECTIONS PAGE
    # ==========================================
    @app.route('/collections')
    @login_required
    def collections():
        user_id = session['user_id']
        # Fetch user favorites ordered by created_at descending
        favorites = Favorite.query.filter_by(user_id=user_id).order_by(Favorite.created_at.desc()).all()
        return render_template('collections.html', favorites=favorites)

    # ==========================================
    # 6. DEDICATED COOKING MODE PAGE
    # ==========================================
    @app.route('/recipes/<int:recipe_id>/cook')
    def cooking_mode(recipe_id):
        recipe = db.session.get(Recipe, recipe_id)
        if not recipe:
            flash('Recipe not found.', 'danger')
            return redirect(url_for('recipes_list'))

        def parse_recipe_instructions(instructions_raw):
            if not instructions_raw:
                return []
            lines = [line.strip() for line in instructions_raw.splitlines() if line.strip()]
            steps = []
            for line in lines:
                chunks = re.split(r'(?:\r?\n|(?<=\.|\!|\?)\s+(?=(?:Step\s*)?\d+[\.\:\)]\s+))', line, flags=re.IGNORECASE)
                for chunk in chunks:
                    chunk_clean = chunk.strip()
                    if not chunk_clean:
                        continue
                    cleaned = re.sub(r'^(?:step\s*\d+[\.\:\)\-]*\s*|\d+[\.\)\:\-]+\s*)', '', chunk_clean, flags=re.IGNORECASE).strip()
                    if cleaned:
                        steps.append(cleaned)
            if not steps and instructions_raw.strip():
                cleaned = re.sub(r'^(?:step\s*\d+[\.\:\)\-]*\s*|\d+[\.\)\:\-]+\s*)', '', instructions_raw.strip(), flags=re.IGNORECASE).strip()
                if cleaned:
                    steps.append(cleaned)
            return steps

        instructions_list = parse_recipe_instructions(recipe.instructions)
        return render_template('cooking_mode.html', recipe=recipe, instructions_list=instructions_list)

    # ==========================================
    # 7. DEDICATED RECIPE WORKSPACE (Add / Edit / Delete)
    # ==========================================
    @app.route('/recipes/add', methods=['GET', 'POST'])
    @login_required
    def add_recipe():
        categories = Category.query.order_by(Category.name.asc()).all()

        if request.method == 'POST':
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            image = request.form.get('image', '').strip()
            category_id = request.form.get('category_id', type=int)
            cuisine = request.form.get('cuisine', '').strip()
            prep_time = request.form.get('prep_time', type=int, default=0)
            cook_time = request.form.get('cook_time', type=int, default=0)
            servings = request.form.get('servings', type=int, default=1)
            difficulty = request.form.get('difficulty', 'Medium')
            instructions = request.form.get('instructions', '').strip()

            if not title or not category_id or not instructions:
                flash('Title, Category, and Instructions are required.', 'danger')
                return render_template('add_recipe.html', categories=categories, form_data=request.form)

            new_recipe = Recipe(
                title=title,
                description=description,
                image=image if image else None,
                category_id=category_id,
                cuisine=cuisine if cuisine else 'General',
                prep_time=prep_time,
                cook_time=cook_time,
                servings=servings,
                difficulty=difficulty,
                instructions=instructions,
                author_id=session['user_id']
            )

            try:
                db.session.add(new_recipe)
                db.session.flush()

                names = request.form.getlist('ingredient_name[]')
                quantities = request.form.getlist('ingredient_quantity[]')
                units = request.form.getlist('ingredient_unit[]')

                for name, qty, unit in zip(names, quantities, units):
                    clean_name = name.strip()
                    if clean_name:
                        ingredient = Ingredient(
                            recipe_id=new_recipe.id,
                            name=clean_name,
                            quantity=qty.strip() if qty else '',
                            unit=unit.strip() if unit else ''
                        )
                        db.session.add(ingredient)

                db.session.commit()
                flash('Recipe created successfully!', 'success')
                return redirect(url_for('recipe_details', recipe_id=new_recipe.id))

            except Exception as e:
                db.session.rollback()
                flash('An error occurred while creating the recipe.', 'danger')

        return render_template('add_recipe.html', categories=categories)

    @app.route('/recipes/<int:recipe_id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_recipe(recipe_id):
        recipe = db.session.get(Recipe, recipe_id)
        if not recipe:
            flash('Recipe not found.', 'danger')
            return redirect(url_for('recipes_list'))

        user_id = session.get('user_id')
        user_role = session.get('user_role')
        if recipe.author_id != user_id and user_role != 'admin':
            flash('You are not authorized to edit this recipe.', 'danger')
            return redirect(url_for('recipe_details', recipe_id=recipe.id))

        categories = Category.query.order_by(Category.name.asc()).all()

        if request.method == 'POST':
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            image = request.form.get('image', '').strip()
            category_id = request.form.get('category_id', type=int)
            cuisine = request.form.get('cuisine', '').strip()
            prep_time = request.form.get('prep_time', type=int, default=0)
            cook_time = request.form.get('cook_time', type=int, default=0)
            servings = request.form.get('servings', type=int, default=1)
            difficulty = request.form.get('difficulty', 'Medium')
            instructions = request.form.get('instructions', '').strip()

            if not title or not category_id or not instructions:
                flash('Title, Category, and Instructions are required.', 'danger')
                return render_template('edit_recipe.html', recipe=recipe, categories=categories)

            recipe.title = title
            recipe.description = description
            recipe.image = image if image else None
            recipe.category_id = category_id
            recipe.cuisine = cuisine if cuisine else 'General'
            recipe.prep_time = prep_time
            recipe.cook_time = cook_time
            recipe.servings = servings
            recipe.difficulty = difficulty
            recipe.instructions = instructions

            try:
                Ingredient.query.filter_by(recipe_id=recipe.id).delete()

                names = request.form.getlist('ingredient_name[]')
                quantities = request.form.getlist('ingredient_quantity[]')
                units = request.form.getlist('ingredient_unit[]')

                for name, qty, unit in zip(names, quantities, units):
                    clean_name = name.strip()
                    if clean_name:
                        ingredient = Ingredient(
                            recipe_id=recipe.id,
                            name=clean_name,
                            quantity=qty.strip() if qty else '',
                            unit=unit.strip() if unit else ''
                        )
                        db.session.add(ingredient)

                db.session.commit()
                flash('Recipe updated successfully!', 'success')
                return redirect(url_for('recipe_details', recipe_id=recipe.id))

            except Exception as e:
                db.session.rollback()
                flash('An error occurred while updating the recipe.', 'danger')

        return render_template('edit_recipe.html', recipe=recipe, categories=categories)

    @app.route('/recipes/<int:recipe_id>/delete', methods=['POST'])
    @login_required
    def delete_recipe(recipe_id):
        recipe = db.session.get(Recipe, recipe_id)
        if not recipe:
            flash('Recipe not found.', 'danger')
            return redirect(url_for('recipes_list'))

        user_id = session.get('user_id')
        user_role = session.get('user_role')
        if recipe.author_id != user_id and user_role != 'admin':
            flash('You are not authorized to delete this recipe.', 'danger')
            return redirect(url_for('recipe_details', recipe_id=recipe.id))

        try:
            db.session.delete(recipe)
            db.session.commit()
            flash('Recipe deleted successfully.', 'success')
            return redirect(url_for('recipes_list'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while deleting the recipe.', 'danger')
            return redirect(url_for('recipe_details', recipe_id=recipe.id))

    # ==========================================
    # 8. AUTHENTICATION & PROFILE ROUTES
    # ==========================================
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if 'user_id' in session:
            flash('You are already logged in.', 'info')
            return redirect(url_for('profile'))

        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')

            if not name or not email or not password or not confirm_password:
                flash('All fields are required.', 'danger')
                return render_template('register.html', name=name, email=email)

            if password != confirm_password:
                flash('Passwords do not match.', 'danger')
                return render_template('register.html', name=name, email=email)

            if len(password) < 6:
                flash('Password must be at least 6 characters long.', 'danger')
                return render_template('register.html', name=name, email=email)

            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash('An account with this email address already exists.', 'warning')
                return render_template('register.html', name=name)

            new_user = User(name=name, email=email, role='user')
            new_user.set_password(password)

            try:
                db.session.add(new_user)
                db.session.commit()
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                db.session.rollback()
                flash('An error occurred during registration.', 'danger')

        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if 'user_id' in session:
            flash('You are already logged in.', 'info')
            return redirect(url_for('profile'))

        if request.method == 'POST':
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')

            if not email or not password:
                flash('Please enter both email and password.', 'danger')
                return render_template('login.html', email=email)

            user = User.query.filter_by(email=email).first()

            if user and user.check_password(password):
                session['user_id'] = user.id
                session['user_name'] = user.name
                session['user_email'] = user.email
                session['user_role'] = user.role

                flash(f'Welcome back, {user.name}!', 'success')
                return redirect(url_for('profile'))
            else:
                flash('Invalid email address or password.', 'danger')
                return render_template('login.html', email=email)

        return render_template('login.html')

    @app.route('/logout')
    def logout():
        if 'user_id' in session:
            session.clear()
            flash('You have been logged out successfully.', 'success')
        return redirect(url_for('login'))

    @app.route('/profile')
    @login_required
    def profile():
        user = db.session.get(User, session['user_id'])
        if not user:
            session.clear()
            flash('User session invalid. Please log in again.', 'danger')
            return redirect(url_for('login'))
        user_recipes = Recipe.query.filter_by(author_id=user.id).all()
        return render_template('profile.html', user=user, recipes_count=len(user_recipes))

    return app


def seed_default_admin():
    admin_email = 'admin@recipe.com'
    existing_admin = User.query.filter_by(email=admin_email).first()
    if not existing_admin:
        admin_user = User(name='System Admin', email=admin_email, role='admin')
        admin_user.set_password('Admin@123')
        db.session.add(admin_user)
        db.session.commit()


def seed_default_categories():
    default_categories = [
        'Breakfast', 'Lunch', 'Dinner', 'Snacks',
        'Desserts', 'Beverages', 'Vegetarian', 'Non-Vegetarian'
    ]
    for cat_name in default_categories:
        existing = Category.query.filter_by(name=cat_name).first()
        if not existing:
            db.session.add(Category(name=cat_name))
    db.session.commit()


def seed_sample_recipes():
    """Seeds initial high-quality sample recipes with verified, high-resolution food images if DB is empty."""
    if Recipe.query.first() is not None:
        return

    admin = User.query.filter_by(role='admin').first()
    if not admin:
        return

    lunch_cat = Category.query.filter_by(name='Lunch').first() or Category.query.first()
    dinner_cat = Category.query.filter_by(name='Dinner').first() or Category.query.first()
    breakfast_cat = Category.query.filter_by(name='Breakfast').first() or Category.query.first()

    recipes_data = [
        {
            'title': 'Creamy Tuscan Garlic Pasta',
            'description': 'A rich, delicious Italian pasta tossed in a creamy garlic sauce with sun-dried tomatoes, fresh spinach, and grated parmesan.',
            'image': 'https://images.unsplash.com/photo-1551183053-bf91a1d81141?auto=format&fit=crop&w=800&q=80',
            'category_id': lunch_cat.id if lunch_cat else 1,
            'cuisine': 'Italian',
            'prep_time': 10,
            'cook_time': 15,
            'servings': 4,
            'difficulty': 'Easy',
            'instructions': '1. Boil pasta in salted water until al dente.\n2. In a skillet, sauté garlic and sun-dried tomatoes in butter.\n3. Pour in heavy cream and simmer until thickened.\n4. Stir in fresh spinach and grated parmesan until wilted.\n5. Toss with cooked pasta and serve warm.',
            'ingredients': [
                ('Fettuccine Pasta', '300', 'g'),
                ('Heavy Cream', '1', 'cup'),
                ('Garlic', '4', 'cloves'),
                ('Sun-dried Tomatoes', '1/2', 'cup'),
                ('Fresh Spinach', '2', 'cups'),
                ('Parmesan Cheese', '1/2', 'cup')
            ]
        },
        {
            'title': 'Classic Indian Butter Chicken',
            'description': 'Tender marinated chicken chunks cooked in a silky, aromatic tomato and butter gravy finished with cream and spices.',
            'image': 'https://images.unsplash.com/photo-1588166524941-3bf61a9c41db?auto=format&fit=crop&w=800&q=80',
            'category_id': dinner_cat.id if dinner_cat else 1,
            'cuisine': 'Indian',
            'prep_time': 20,
            'cook_time': 30,
            'servings': 4,
            'difficulty': 'Medium',
            'instructions': '1. Marinate chicken in yogurt, ginger, garlic, and garam masala for 30 minutes.\n2. Sear chicken in a pan until lightly charred.\n3. Prepare tomato gravy with butter, onions, cashew paste, and aromatic spices.\n4. Simmer chicken in gravy for 15 minutes.\n5. Finish with fresh cream and dried fenugreek leaves (kasuri methi).',
            'ingredients': [
                ('Chicken Breast', '500', 'g'),
                ('Yogurt', '1/2', 'cup'),
                ('Butter', '3', 'tbsp'),
                ('Tomato Puree', '1.5', 'cups'),
                ('Heavy Cream', '1/4', 'cup'),
                ('Garam Masala', '1', 'tsp')
            ]
        },
        {
            'title': 'Woodfired Artisan Margherita Pizza',
            'description': 'Traditional Neapolitan pizza with crisp blistered crust, sweet San Marzano tomato sauce, fresh mozzarella, and aromatic basil leaves.',
            'image': 'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=800&q=80',
            'category_id': dinner_cat.id if dinner_cat else 1,
            'cuisine': 'Italian',
            'prep_time': 15,
            'cook_time': 12,
            'servings': 2,
            'difficulty': 'Medium',
            'instructions': '1. Stretch fermented pizza dough into a 12-inch round.\n2. Spread crushed San Marzano tomatoes thinly over base.\n3. Top with torn fresh mozzarella and olive oil drizzle.\n4. Bake at high heat (450°F / 230°C) for 10-12 minutes until bubbly and golden.\n5. Garnish with fresh basil leaves before slicing.',
            'ingredients': [
                ('Pizza Dough', '1', 'ball'),
                ('San Marzano Tomatoes', '1/2', 'cup'),
                ('Fresh Mozzarella', '150', 'g'),
                ('Fresh Basil', '6', 'leaves'),
                ('Extra Virgin Olive Oil', '1', 'tbsp')
            ]
        },
        {
            'title': 'Fresh Avocado & Berry Power Salad',
            'description': 'A vibrant, nutrient-packed salad with creamy avocado slices, fresh blueberries, walnuts, and baby spinach tossed in lemon vinaigrette.',
            'image': 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=800&q=80',
            'category_id': breakfast_cat.id if breakfast_cat else 1,
            'cuisine': 'Mediterranean',
            'prep_time': 10,
            'cook_time': 0,
            'servings': 2,
            'difficulty': 'Easy',
            'instructions': '1. Wash baby spinach and place in a large bowl.\n2. Slice fresh avocado and toss with lemon juice to prevent browning.\n3. Add fresh blueberries, crumbled goat cheese, and toasted walnuts.\n4. Whisk olive oil, lemon juice, honey, and black pepper for dressing.\n5. Drizzle dressing over salad right before serving.',
            'ingredients': [
                ('Ripe Avocado', '1', 'whole'),
                ('Baby Spinach', '3', 'cups'),
                ('Fresh Blueberries', '1/2', 'cup'),
                ('Walnuts', '1/4', 'cup'),
                ('Goat Cheese', '50', 'g'),
                ('Olive Oil', '2', 'tbsp')
            ]
        }
    ]

    for item in recipes_data:
        recipe = Recipe(
            title=item['title'],
            description=item['description'],
            image=item['image'],
            category_id=item['category_id'],
            cuisine=item['cuisine'],
            prep_time=item['prep_time'],
            cook_time=item['cook_time'],
            servings=item['servings'],
            difficulty=item['difficulty'],
            instructions=item['instructions'],
            author_id=admin.id
        )
        db.session.add(recipe)
        db.session.flush()

        for ing_name, qty, unit in item['ingredients']:
            db.session.add(Ingredient(
                recipe_id=recipe.id,
                name=ing_name,
                quantity=qty,
                unit=unit
            ))

    db.session.commit()


# Instantiate Flask application
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
