
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

| Technology   | Purpose                  |
|--------------|--------------------------|
| HTML         | Website structure        |
| CSS          | Website styling          |
| Python       | Backend logic            |
| FastAPI      | Webhook / API backend    |
| Uvicorn      | ASGI server              |
| MySQL        | Menu and order database  |
| Dialogflow   | Conversational chatbot   |

---

## 📁 Project Structure

```text
Sira-Food/
├── index.html
├── style.css
├── main.py
├── requirements.txt
└── db/
    └── pandeyji_eatery.sql
```

### File Description

| File                     | Description |
|--------------------------|-------------|
| `index.html`             | Restaurant homepage, menu, and Dialogflow chatbot interface |
| `style.css`              | Responsive styling for the restaurant website |
| `main.py`                | FastAPI application (Dialogflow webhook, order management, database operations) |
| `requirements.txt`       | Python dependencies |
| `db/pandeyji_eatery.sql` | SQL database schema and initial menu data |

---

## 🚀 Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/Sira-Food.git
cd Sira-Food
```

### 2. Create a virtual environment

**Windows**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux / macOS**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🗄️ Database Setup

Make sure **MySQL Server** is installed and running.

Import the SQL database:

```bash
mysql -u root -p < db/pandeyji_eatery.sql
```

(or import it using MySQL Workbench)

Required tables:
- `food_items` → stores the restaurant menu
- `orders` → stores customer orders and their status

---

## 🔐 Database Configuration

**Do not** commit your real database password to GitHub.

Use environment variables instead of hard-coding credentials:

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

**Windows PowerShell example:**

```powershell
$env:DB_HOST="localhost"
$env:DB_USER="root"
$env:DB_PASSWORD="your_password"
$env:DB_NAME="pandeyji_eatery"
$env:DB_PORT="3306"
```

---

## ▶️ Run the FastAPI Backend

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Backend will be available at:  
http://127.0.0.1:8000

---

## 🤖 Dialogflow Integration

```text
Customer → Restaurant Website → Dialogflow → FastAPI Webhook → MySQL
```

Dialogflow extracts parameters such as:
- `food-item`
- `number`
- `order-id`

---

## 📦 Order Management

| Action             | Example                          |
|--------------------|----------------------------------|
| Place Order        | "I want 1 Burger and 2 Pizzas"  |
| Add More Items     | "I want 2 Pizzas too"           |
| Remove an Item     | "Remove the Pizza from my order"|
| Cancel Order       | "Cancel my order"               |
| Track Order        | "Track my order 872352"         |
| Final Order Total  | Calculated automatically        |

---

## 🌐 Frontend

- Navigation bar
- Hero section
- Menu section with food cards
- Prices
- Fully responsive design
- Embedded Dialogflow chatbot

---

## ⚠️ Important Notes

- MySQL must be running, otherwise database features will fail.
- The Dialogflow webhook URL must point to your FastAPI server.
- Session-based order tracking is currently in-memory (lost on server restart). For production, store the mapping in the database.

---

## 🎯 Future Improvements

- Shopping cart functionality
- Online payment integration
- Customer accounts
- Delivery address management
- Real-time order tracking
- Order history
- Persistent session management
- Admin dashboard
- Progressive Web App support

---

## 📚 Project Purpose

This project was created as an **educational/demo project** to practice:

- FastAPI & REST APIs
- Webhooks
- Dialogflow
- MySQL
- Full-stack development
- Conversational interfaces

---

## 👨‍💻 Author

**Sadam Hussain Alvi**  
GitHub: [https://github.com/Sadam-Alvi](https://github.com/Sadam-Alvi)

---

## 📄 License

This project is intended for educational and demonstration purposes.
```
