from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import re
from typing import Any, Dict, Optional
import uvicorn
import mysql.connector
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="sadam",
        database="pandeyji_eatery"
    )
last_orders = {}



app = FastAPI(title="Dialogflow Webhook")

# ---------- Helper: Extract data from Dialogflow request ----------
def extract_from_request(body: Dict[str, Any]) -> tuple[str, str, Dict[str, Any]]:
    """
    Extracts session_id, intent_name and parameters from the Dialogflow webhook request.
    """
    session = body.get("session", "")
    # session looks like: projects/PROJECT_ID/agent/sessions/SESSION_ID
    session_id = session.split("/")[-1] if session else "unknown"

    query_result = body.get("queryResult", {})
    intent_name = query_result.get("intent", {}).get("displayName", "")
    parameters = query_result.get("parameters", {}) or {}

    return session_id, intent_name, parameters


def order_place(session_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:

    db = None
    cursor = None

    try:
        # -------------------------
        # Get values from Dialogflow
        # -------------------------
        food_items = parameters.get("food-item")
        quantities = parameters.get("number")

        if not food_items or not quantities:
            message = "Please provide the food items and quantities."

            return {
                "fulfillmentText": message,
                "fulfillmentMessages": [
                    {
                        "text": {
                            "text": [message]
                        }
                    }
                ]
            }

        # Dialogflow may return a single value instead of a list
        if not isinstance(food_items, list):
            food_items = [food_items]

        if not isinstance(quantities, list):
            quantities = [quantities]

        # Make sure every food has a quantity
        if len(food_items) != len(quantities):
            message = (
                "I couldn't match the quantities "
                "with the food items."
            )

            return {
                "fulfillmentText": message,
                "fulfillmentMessages": [
                    {
                        "text": {
                            "text": [message]
                        }
                    }
                ]
            }

        # -------------------------
        # Database connection
        # -------------------------
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # -------------------------
        # Get existing order ID
        # for this session
        # -------------------------
        if session_id in last_orders:

            order_id = last_orders[session_id]["order_id"]

            # Make sure this order still exists
            cursor.execute(
                """
                SELECT order_id
                FROM orders
                WHERE order_id = %s
                LIMIT 1
                """,
                (order_id,)
            )

            existing_order = cursor.fetchone()

            if not existing_order:
                # Previous order was cancelled/deleted
                del last_orders[session_id]

        # -------------------------
        # Create a new order ID
        # if session has no active order
        # -------------------------
        if session_id not in last_orders:

            cursor.execute(
                """
                SELECT COALESCE(MAX(order_id), 0) + 1 AS next_order_id
                FROM orders
                """
            )

            result = cursor.fetchone()

            order_id = result["next_order_id"]

            last_orders[session_id] = {
                "order_id": order_id,
                "total_price": 0
            }

        # -------------------------
        # Store ordered items
        # -------------------------
        ordered_items = []

        # -------------------------
        # Process each food item
        # -------------------------
        for food_item, quantity in zip(food_items, quantities):

            # Clean food name
            food_item = re.sub(
                r"[^\w\s]",
                "",
                str(food_item)
            )

            food_item = " ".join(
                food_item.split()
            ).strip()

            quantity = int(quantity)

            if quantity <= 0:
                raise ValueError(
                    "Quantity must be greater than zero."
                )

            print("Food:", food_item)
            print("Quantity:", quantity)

            # -------------------------
            # Find food in food_items
            # -------------------------
            cursor.execute(
                """
                SELECT item_id, name, price
                FROM food_items
                WHERE LOWER(TRIM(name)) =
                      LOWER(TRIM(%s))
                LIMIT 1
                """,
                (food_item,)
            )

            food = cursor.fetchone()

            if not food:

                db.rollback()

                message = (
                    f"Sorry, {food_item} "
                    f"is not available on the menu."
                )

                return {
                    "fulfillmentText": message,
                    "fulfillmentMessages": [
                        {
                            "text": {
                                "text": [message]
                            }
                        }
                    ]
                }

            item_id = food["item_id"]
            food_name = food["name"]
            price = float(food["price"])

            # -------------------------
            # Check if this food already
            # exists in this order
            # -------------------------
            cursor.execute(
                """
                SELECT order_row_id, quantity
                FROM orders
                WHERE order_id = %s
                AND item_id = %s
                LIMIT 1
                """,
                (
                    order_id,
                    item_id
                )
            )

            existing_item = cursor.fetchone()

            if existing_item:

                # -------------------------
                # Add quantity to existing item
                # -------------------------
                new_quantity = (
                    existing_item["quantity"]
                    + quantity
                )

                cursor.execute(
                    """
                    UPDATE orders
                    SET quantity = %s,
                        status = %s
                    WHERE order_row_id = %s
                    """,
                    (
                        new_quantity,
                        "in transit",
                        existing_item["order_row_id"]
                    )
                )

            else:

                # -------------------------
                # Add new item to order
                # -------------------------
                cursor.execute(
                    """
                    INSERT INTO orders
                    (
                        order_id,
                        item_id,
                        quantity,
                        status,
                        total_price
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        order_id,
                        item_id,
                        quantity,
                        "in transit",
                        price * quantity
                    )
                )

            ordered_items.append(
                f"{quantity} {food_name}"
            )

        # -------------------------
        # Calculate complete order total
        # -------------------------
        cursor.execute(
            """
            SELECT
                SUM(
                    fi.price * o.quantity
                ) AS order_total
            FROM orders o
            JOIN food_items fi
                ON o.item_id = fi.item_id
            WHERE o.order_id = %s
            """,
            (order_id,)
        )

        total_result = cursor.fetchone()

        total_price = float(
            total_result["order_total"] or 0
        )

        # -------------------------
        # Store total price
        # on every row of order
        # -------------------------
        cursor.execute(
            """
            UPDATE orders
            SET total_price = %s
            WHERE order_id = %s
            """,
            (
                total_price,
                order_id
            )
        )

        # -------------------------
        # Commit
        # -------------------------
        db.commit()

        # -------------------------
        # Save session
        # -------------------------
        last_orders[session_id] = {
            "order_id": order_id,
            "total_price": total_price
        }

        # -------------------------
        # Close database
        # -------------------------
        cursor.close()
        cursor = None

        db.close()
        db = None

        # -------------------------
        # Response
        # -------------------------
        item_text = ", ".join(ordered_items)

        message = (
            f"Your order has been placed successfully! "
            f"You ordered {item_text}. "
            f"Order ID: #{order_id}. "
            f"Total price: {total_price:.2f}."
            f"Anything else?"
        )

        return {
            "fulfillmentText": message,
            "fulfillmentMessages": [
                {
                    "text": {
                        "text": [message]
                    }
                }
            ]
        }

    # -------------------------
    # Invalid quantity / input
    # -------------------------
    except ValueError as e:

        print("ORDER INPUT ERROR:", repr(e))

        if db:
            try:
                db.rollback()
            except:
                pass

        message = str(e)

        return {
            "fulfillmentText": message,
            "fulfillmentMessages": [
                {
                    "text": {
                        "text": [message]
                    }
                }
            ]
        }

    # -------------------------
    # Database / unexpected error
    # -------------------------
    except Exception as e:

        print("ORDER ERROR:", repr(e))

        if db:
            try:
                db.rollback()
            except:
                pass

        return {
            "fulfillmentText":
                f"Order error: {str(e)}"
        }

    # -------------------------
    # Always close resources
    # -------------------------
    finally:

        try:
            if cursor:
                cursor.close()
        except:
            pass

        try:
            if db:
                db.close()
        except:
            pass


def order_remove(session_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:

    order_id = (
        parameters.get("order_id")
        or parameters.get("orderId")
        or parameters.get("number")
    )

    # Dialogflow may return number as a list
    if isinstance(order_id, list):
        order_id = order_id[0] if order_id else None

    if not order_id:
        message = "Please provide your Order ID so I can cancel your order."

        return {
            "fulfillmentText": message,
            "fulfillmentMessages": [
                {
                    "text": {
                        "text": [message]
                    }
                }
            ]
        }

    db = None
    cursor = None

    try:
        order_id = int(order_id)

        # -------------------------
        # Database connection
        # -------------------------
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # -------------------------
        # Check if order exists
        # -------------------------
        cursor.execute(
            """
            SELECT order_id
            FROM orders
            WHERE order_id = %s
            LIMIT 1
            """,
            (order_id,)
        )

        order = cursor.fetchone()

        if not order:
            message = f"I couldn't find an order with ID #{order_id}."

            return {
                "fulfillmentText": message,
                "fulfillmentMessages": [
                    {
                        "text": {
                            "text": [message]
                        }
                    }
                ]
            }

        # -------------------------
        # Delete ALL items belonging
        # to this order
        # -------------------------
        cursor.execute(
            """
            DELETE FROM orders
            WHERE order_id = %s
            """,
            (order_id,)
        )

        # -------------------------
        # Commit deletion
        # -------------------------
        db.commit()

        message = (
            f"Your order #{order_id} "
            f"has been cancelled successfully."
        )

        return {
            "fulfillmentText": message,
            "fulfillmentMessages": [
                {
                    "text": {
                        "text": [message]
                    }
                }
            ]
        }

    except ValueError:

        message = "Please provide a valid numeric Order ID."

        return {
            "fulfillmentText": message,
            "fulfillmentMessages": [
                {
                    "text": {
                        "text": [message]
                    }
                }
            ]
        }

    except Exception as e:

        print("Cancel order error:", repr(e))

        try:
            if db:
                db.rollback()
        except:
            pass

        message = "Sorry, I couldn't cancel your order right now."

        return {
            "fulfillmentText": message,
            "fulfillmentMessages": [
                {
                    "text": {
                        "text": [message]
                    }
                }
            ]
        }

    finally:

        try:
            if cursor:
                cursor.close()
        except:
            pass

        try:
            if db:
                db.close()
        except:
            pass
# ```python
def order_track(session_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:

    order_id = (
        parameters.get("order_id")
        or parameters.get("orderId")
        or parameters.get("number")
    )

    # Dialogflow may return the order ID as a list
    if isinstance(order_id, list):
        order_id = order_id[0] if order_id else None

    if not order_id:
        message = "Please provide your Order ID so I can track it."

        return {
            "fulfillmentText": message,
            "fulfillmentMessages": [
                {
                    "text": {
                        "text": [message]
                    }
                }
            ]
        }

    db = None
    cursor = None

    try:
        # -------------------------
        # Convert Order ID to int
        # -------------------------
        order_id = int(order_id)

        # -------------------------
        # Database connection
        # -------------------------
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # -------------------------
        # Get order status
        # -------------------------
        query = """
            SELECT DISTINCT order_id, status
            FROM orders
            WHERE order_id = %s
        """

        cursor.execute(
            query,
            (order_id,)
        )

        results = cursor.fetchall()

        # -------------------------
        # Order not found
        # -------------------------
        if not results:
            message = (
                f"I couldn't find an order with ID #{order_id}."
            )

        else:
            # Get the status from the first row
            status = results[0]["status"]

            message = (
                f"Your order #{order_id} "
                f"is currently {status}."
            )

        return {
            "fulfillmentText": message,
            "fulfillmentMessages": [
                {
                    "text": {
                        "text": [message]
                    }
                }
            ]
        }

    except ValueError:

        message = "Please provide a valid numeric Order ID."

        return {
            "fulfillmentText": message,
            "fulfillmentMessages": [
                {
                    "text": {
                        "text": [message]
                    }
                }
            ]
        }

    except Exception as e:

        print("Database error:", repr(e))

        return {
            "fulfillmentText":
                "Sorry, I couldn't check your order status right now."
        }

    finally:

        try:
            if cursor:
                cursor.close()
        except:
            pass

        try:
            if db:
                db.close()
        except:
            pass


def get_order_total(session_id: str):

    db = None
    cursor = None

    try:
        if session_id not in last_orders:
            return 0.0, ""

        order_id = last_orders[session_id]["order_id"]

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                fi.name,
                o.quantity,
                fi.price
            FROM orders o
            JOIN food_items fi
                ON o.item_id = fi.item_id
            WHERE o.order_id = %s
            """,
            (order_id,)
        )

        rows = cursor.fetchall()

        total_charges = 0.0
        ordered_items = []

        for row in rows:

            name = row["name"]
            quantity = row["quantity"]
            price = float(row["price"])

            total_charges += price * quantity

            ordered_items.append(
                f"{quantity} {name}"
            )

        names = ", ".join(ordered_items)

        return total_charges, names

    except Exception as e:

        print("Get order total error:", repr(e))

        return 0.0, ""

    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()




def item_remove(session_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:

    db = None
    cursor = None

    try:

        # -------------------------
        # Check active order
        # -------------------------
        if session_id not in last_orders:

            message = "You don't have an active order."

            return {
                "fulfillmentText": message
            }

        order_id = last_orders[session_id]["order_id"]

        # -------------------------
        # Get food item
        # -------------------------
        food_item = (
            parameters.get("food-item")
            or parameters.get("food_item")
            or parameters.get("item")
        )

        if isinstance(food_item, list):
            food_item = food_item[0] if food_item else None

        if not food_item:

            message = "Please tell me which food item you want to remove."

            return {
                "fulfillmentText": message
            }

        # -------------------------
        # Clean food name
        # -------------------------
        food_item = re.sub(
            r"[^\w\s]",
            "",
            str(food_item)
        )

        food_item = " ".join(
            food_item.split()
        ).strip()

        # -------------------------
        # Connect to database
        # -------------------------
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # -------------------------
        # Find food item
        # -------------------------
        cursor.execute(
            """
            SELECT item_id, name
            FROM food_items
            WHERE LOWER(TRIM(name)) =
                  LOWER(TRIM(%s))
            LIMIT 1
            """,
            (food_item,)
        )

        food = cursor.fetchone()

        if not food:

            message = (
                f"Sorry, {food_item} "
                f"is not available on the menu."
            )

            return {
                "fulfillmentText": message
            }

        item_id = food["item_id"]
        food_name = food["name"]

        # -------------------------
        # Check if item exists
        # in current order
        # -------------------------
        cursor.execute(
            """
            SELECT quantity
            FROM orders
            WHERE order_id = %s
            AND item_id = %s
            LIMIT 1
            """,
            (
                order_id,
                item_id
            )
        )

        existing_item = cursor.fetchone()

        if not existing_item:

            message = (
                f"{food_name} is not in "
                f"your current order."
            )

            return {
                "fulfillmentText": message
            }

        # -------------------------
        # Remove the item completely
        # -------------------------
        cursor.execute(
            """
            DELETE FROM orders
            WHERE order_id = %s
            AND item_id = %s
            """,
            (
                order_id,
                item_id
            )
        )

        # -------------------------
        # Check if anything remains
        # -------------------------
        cursor.execute(
            """
            SELECT COUNT(*) AS item_count
            FROM orders
            WHERE order_id = %s
            """,
            (order_id,)
        )

        remaining = cursor.fetchone()

        if remaining["item_count"] == 0:

            # No items left in the order
            db.commit()

            # Remove active order from session
            last_orders.pop(session_id, None)

            message = (
                f"{food_name} has been removed. "
                f"Your order is now empty."
            )

            return {
                "fulfillmentText": message
            }

        # -------------------------
        # Recalculate total
        # -------------------------
        cursor.execute(
            """
            SELECT
                COALESCE(
                    SUM(fi.price * o.quantity),
                    0
                ) AS total_charges
            FROM orders o
            JOIN food_items fi
                ON o.item_id = fi.item_id
            WHERE o.order_id = %s
            """,
            (order_id,)
        )

        result = cursor.fetchone()

        total_charges = float(
            result["total_charges"] or 0
        )

        # -------------------------
        # Update total_price
        # -------------------------
        cursor.execute(
            """
            UPDATE orders
            SET total_price = %s
            WHERE order_id = %s
            """,
            (
                total_charges,
                order_id
            )
        )

        db.commit()

        # -------------------------
        # Update session total
        # -------------------------
        last_orders[session_id]["total_price"] = total_charges

        # -------------------------
        # Response
        # -------------------------
        message = (
            f"{food_name} has been removed "
            f"from your order. "
            f"Your new total is "
            f"Rs. {total_charges:.2f}."
            f"Anything esle?"
        )

        return {
            "fulfillmentText": message
        }

    except Exception as e:

        print("Remove item error:", repr(e))

        if db:
            db.rollback()

        return {
            "fulfillmentText":
                "Sorry, I couldn't remove that item."
        }

    finally:

        if cursor:
            try:
                cursor.close()
            except:
                pass

        if db:
            try:
                db.close()
            except:
                pass





# ---------- Main Webhook Endpoint ----------
@app.post("/webhook")
async def dialogflow_webhook(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    session_id, intent_name, parameters = extract_from_request(body)

    print(f"Session: {session_id} | Intent: {intent_name} | Params: {parameters}")

    # Route to the correct intent handler
    if intent_name.strip().lower() == "add-order":
        response = order_place(session_id, parameters)

    elif intent_name.strip().lower() == "cancel-order":
        response = order_remove(session_id, parameters)
    elif intent_name.strip().lower() == "removing-item":
        response = item_remove(session_id, parameters)

    elif intent_name.strip().lower() == "tracking-order-by-id":
        response = order_track(session_id, parameters)
    

    elif intent_name.strip().lower() == "order-complete":

        total_charges,names = get_order_total(session_id)

        message = (
            f"Thanks Sir, your order has been placed! "
            f"Your final total charges are "
            f"You have ordered {names} "
            f"Rs. {total_charges:.2f}."
        )
        response = {
            "fulfillmentText": message
            }
    return response

# Health check (optional but useful)
@app.get("/")
async def health():
    return {"status": "ok", "message": "Dialogflow webhook is running"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)