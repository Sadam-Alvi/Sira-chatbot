
# 🍔 Sira Food

**Sira Food** is a restaurant ordering and customer-service web application built with **HTML, CSS, Python, FastAPI, MySQL, and Dialogflow**.

The project provides a restaurant menu interface along with a conversational chatbot that allows customers to interact with the ordering system using natural language.

---

## ✨ Features

### 🍽️ Restaurant Website
- Modern and responsive restaurant landing page
- Attractive hero section
- Food menu with six items
- Food images, descriptions, and prices
- Responsive layout for desktop and mobile

### 🤖 Sira Chatbot
The website includes a **Dialogflow-powered chatbot** named **Sira**.

Customers can interact with Sira to:

- Place a new order
- Add multiple food items to the same order
- Remove individual food items
- Cancel an entire order
- Track an order using its Order ID
- Calculate the final order total

### ⚙️ Backend
- FastAPI webhook for Dialogflow
- MySQL database integration
- Order management logic
- Session-based order tracking
- Food item validation
- Automatic order total calculation

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| HTML | Website structure |
| CSS | Website styling |
| Python | Backend logic |
| FastAPI | Webhook/API backend |
| Uvicorn | ASGI server |
| MySQL | Menu and order database |
| Dialogflow | Conversational chatbot |

---

## 📁 Project Structure

```text
Sira-Food/
│
├── index.html
├── style.css
├── main.py
├── requirements.txt
│
└── db/
    └── pandeyji_eatery.sql
````

### File Description

**`index.html`**
Restaurant homepage, menu, and Dialogflow chatbot interface.

**`style.css`**
Responsive styling for the restaurant website.

**`main.py`**
FastAPI application containing the Dialogflow webhook, order management, database operations, and order tracking logic.

**`requirements.txt`**
Python dependencies required to run the backend.

**`db/pandeyji_eatery.sql`**
SQL database schema and initial menu/order data.

---

# 🚀 Installation & Setup

## 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/Sira-Food.git
cd Sira-Food
```

---

## 2. Create a virtual environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

# 🗄️ Database Setup

Make sure **MySQL Server** is installed and running.

Import the SQL database:

```bash
mysql -u root -p < db/pandeyji_eatery.sql
```

Alternatively, you can import the SQL file using **MySQL Workbench**.

The application requires the following database tables:

```text
food_items
orders
```

The `food_items` table stores the restaurant menu, while the `orders` table stores customer orders and their status.

---

# 🔐 Database Configuration

Do **not** commit your real database password to GitHub.

Instead of hard-coding credentials in `main.py`, use environment variables.

Example:

```python
import os
import mysql.connector


def get_db_connection():

    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME", "pandeyji_eatery"),
        port=int(os.getenv("DB_PORT", "3306"))
    )
```

For local development, you can configure the variables in your environment.

Example on Windows PowerShell:

```powershell
$env:DB_HOST="localhost"
$env:DB_USER="root"
$env:DB_PASSWORD="your_password"
$env:DB_NAME="pandeyji_eatery"
$env:DB_PORT="3306"
```

---

# ▶️ Run the FastAPI Backend

Start the server with:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The backend will be available at:

```text
http://127.0.0.1:8000
```

If your FastAPI application serves the frontend, open:

```text
http://127.0.0.1:8000/
```

---

# 🤖 Dialogflow Integration

Sira uses **Dialogflow** to understand customer messages.

The general flow is:

```text
Customer
   │
   ▼
Restaurant Website
   │
   ▼
Dialogflow
   │
   ▼
FastAPI Webhook
   │
   ▼
MySQL Database
```

Dialogflow identifies the customer's intent and extracts parameters such as:

```text
food-item
number
order-id
```

The FastAPI webhook then processes the request and performs the appropriate database operation.

---

# 📦 Order Management

The backend supports several order operations.

### Place Order

Customers can order one or multiple food items.

Example:

```text
I want 1 Burger and 2 Pizzas
```

The backend creates an order and stores the items in MySQL.

---

### Add More Items

Customers can continue adding items during the same conversation.

Example:

```text
I want 1 Burger
```

Then:

```text
I want 2 Pizzas too
```

Both items are associated with the same `order_id`.

---

### Remove an Item

Customers can remove an individual food item without cancelling the entire order.

Example:

```text
Remove the Pizza from my order
```

---

### Cancel Order

Customers can cancel their complete active order.

Example:

```text
Cancel my order
```

---

### Track Order

Customers can provide their Order ID to check the order status.

Example:

```text
Track my order 872352
```

---

### Final Order Total

The backend calculates the total using the food item's price and ordered quantity.

Example:

```text
Burger × 1 = Rs. 300
Pizza × 2 = Rs. 1000

Total = Rs. 1300
```

---

# 🌐 Frontend

The restaurant website contains:

* Navigation bar
* Hero section
* Menu section
* Food cards
* Food prices
* Responsive design
* Dialogflow chatbot

The chatbot is embedded into the website using the Dialogflow web client.

---

# 📱 Responsive Design

The website is designed to work across:

* 💻 Desktop
* 💻 Laptop
* 📱 Mobile
* 📟 Tablet

---

# ⚠️ Important Notes

### MySQL

The backend requires a running MySQL server.

If MySQL is not running, database-related functionality will not work.

### Dialogflow

The chatbot requires a properly configured Dialogflow agent and webhook.

The webhook URL configured in Dialogflow must point to your deployed FastAPI server.

### Session-Based Orders

The current backend uses an in-memory session mapping to associate a Dialogflow session with an active order.

This means active session mappings can be lost when the server restarts.

For production use, session/order mapping should be stored in a persistent database or external session store.

---

# 🚀 Deployment

For production deployment, the architecture can be:

```text
                 ┌──────────────────┐
                 │  Sira Food       │
                 │  Website         │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │    Dialogflow    │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ FastAPI Webhook  │
                 │     Server       │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │    MySQL         │
                 │    Database      │
                 └──────────────────┘
```

The frontend can be hosted on a static hosting service, while the FastAPI backend and MySQL database should be hosted on services that support server-side applications and databases.

---

# 🎯 Future Improvements

Possible improvements include:

* 🛒 Shopping cart functionality
* 💳 Online payment integration
* 👤 Customer accounts
* 📍 Delivery address management
* 📦 Real-time order tracking
* 🧾 Order history
* 🔔 Order status notifications
* 🗃️ Persistent session management
* 🔐 Secure authentication
* 📊 Admin dashboard
* 📱 Progressive Web App support

---

# 📚 Project Purpose

This project was created as an **educational/demo project** to practice:

* FastAPI
* REST APIs
* Webhooks
* Dialogflow
* MySQL
* SQL
* Backend development
* Frontend development
* Database-driven applications
* Conversational interfaces

---

# 👨‍💻 Author

**Sadam Hussain Alvi**

GitHub:
https://github.com/Sadam-Alvi

---

#   S i r a - c h a t b o t 
 
 #   S i r a - c h a t b o t  
 