# 🍽️ The Savor Table

### Recipes Worth Remembering.

The Savor Table is a modern recipe management web application built with Flask. It allows users to discover recipes, search and filter dishes, save favorite recipes, manage their personal kitchen ingredients, and follow recipes through a dedicated cooking mode.

The project is designed with a food-focused interface that provides a simple and enjoyable cooking experience.

---

## ✨ Features

### 👤 User Authentication
- User registration and login
- Secure password hashing
- Session-based authentication
- Protected profile page
- Logout functionality

### 🍳 Recipe Management
- Browse all recipes
- Search recipes by title, description, or cuisine
- Filter by:
  - Category
  - Cuisine
  - Difficulty
- Sort recipes
- View detailed recipe information
- Add new recipes
- Edit recipes
- Delete recipes
- Ingredient management

### ❤️ Favorites & Collections
- Save recipes to favorites
- Remove saved recipes
- Dedicated Collections page
- Persistent saved recipes for logged-in users

### 🥕 My Kitchen
- Enter ingredients available at home
- Match ingredients with recipes
- Display recipe match percentage
- Show available ingredients
- Show missing ingredients
- Supports singular/plural ingredient variations

### 👨‍🍳 Cooking Mode
- Step-by-step cooking instructions
- Ingredient checklist
- Previous/Next navigation
- Cooking progress indicator
- Dedicated distraction-free cooking interface

### 🎨 User Interface
- Responsive design
- Desktop, tablet, and mobile support
- Fixed navigation bar
- Food-focused visual identity
- Light and dark themes
- DAY TABLE / NIGHT TABLE theme system
- Custom Savor Table branding

---

## 🛠️ Technology Stack

### Frontend
- HTML5
- CSS3
- JavaScript
- Jinja2 Templates

### Backend
- Python
- Flask
- Flask-SQLAlchemy

### Database
- SQLite
- SQLAlchemy ORM

### Authentication & Security
- Flask Sessions
- Werkzeug Password Hashing

### Deployment
- GitHub
- Render
- Gunicorn

---

## 📁 Project Structure

```text
the-savor-table/
│
├── app.py
├── config.py
├── models.py
├── database.db
├── requirements.txt
├── README.md
├── test_favorites.py
│
├── static/
│   ├── css/
│   │   └── style.css
│   │
│   ├── js/
│   │   └── script.js
│   │
│   └── images/
│       ├── savor-table-logo.png
│       └── the-savor-table-logo.jpg
│
└── templates/
    ├── base.html
    ├── index.html
    ├── login.html
    ├── register.html
    ├── profile.html
    ├── recipes.html
    ├── recipe_details.html
    ├── add_recipe.html
    ├── edit_recipe.html
    ├── my_kitchen.html
    ├── collections.html
    └── cooking_mode.html
