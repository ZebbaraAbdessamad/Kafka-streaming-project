import json
import time
import threading
from kafka import KafkaConsumer, KafkaProducer
from flask import Flask, render_template, jsonify
import random

app = Flask(__name__)

# Kafka producer setup
producer_order_details = KafkaProducer(bootstrap_servers="localhost:29092")
producer_order_confirmed = KafkaProducer(bootstrap_servers="localhost:29092")

# Kafka consumer setup
consumer_order_details = KafkaConsumer('order_details', bootstrap_servers='localhost:29092')
consumer_order_confirmed = KafkaConsumer('order_confirmed', bootstrap_servers='localhost:29092')

# Lists to store consumed messages
consumed_order_details_messages = []
consumed_order_confirmed_messages = []

# Lists to store analytics data
confirmed_orders_analytics = {"total_orders": 0, "burger_count": 0, "pizza_count": 0}

# Set to track processed order IDs
processed_order_ids = set()

# Kafka consumer functions running in separate threads
def kafka_order_details_consumer():
    for message in consumer_order_details:
        consumed_message = json.loads(message.value.decode('utf-8'))
        consumed_order_details_messages.append(consumed_message)

        # Simulate order confirmation logic (e.g., confirm every second order)
        if consumed_message["order_id"] % 2 == 0:
            # Confirm the order with a mix of "burger" and "pizza"
           items = random.choice(["burger", "pizza"])
           consumed_message["items"] = items
           producer_order_confirmed.send('order_confirmed', json.dumps(consumed_message).encode('utf-8'))


def kafka_order_confirmed_consumer():
    for message in consumer_order_confirmed:
        consumed_confirmation_message = json.loads(message.value.decode('utf-8'))
        consumed_order_confirmed_messages.append(consumed_confirmation_message)

        order_id = consumed_confirmation_message.get("order_id")
        # Check if the order has already been processed
        if order_id not in processed_order_ids:
            processed_order_ids.add(order_id)

            # Update analytics data for confirmed orders
            confirmed_orders_analytics["total_orders"] += 1
            items = consumed_confirmation_message.get("items", "").split(",")  # Split items into a list
            for item in items:
                item_type = item.strip()
                if item_type:
                    confirmed_orders_analytics["burger_count" if item_type == "burger" else "pizza_count"] += 1


# Start the Kafka consumer threads
order_details_consumer_thread = threading.Thread(target=kafka_order_details_consumer)
order_details_consumer_thread.start()

order_confirmed_consumer_thread = threading.Thread(target=kafka_order_confirmed_consumer)
order_confirmed_consumer_thread.start()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/listen_order')
def listen_order():
    return render_template('order_messages.html', messages=consumed_order_details_messages)

@app.route('/listen_confirmation')
def listen_confirmation():
    return render_template('confirmation_messages.html', messages=consumed_order_confirmed_messages)

@app.route('/get_order_messages')
def get_order_messages():
    return jsonify({'messages': consumed_order_details_messages})

@app.route('/get_confirmation_messages')
def get_confirmation_messages():
    return jsonify({'messages': consumed_order_confirmed_messages})

@app.route('/analytics')
def analytics():
    return render_template('analytics.html', analytics=confirmed_orders_analytics)

@app.route('/get_analytics_data')
def get_analytics_data():
    return jsonify(confirmed_orders_analytics)

@app.route('/produce')
def produce():
    ORDER_LIMIT = 15
    for i in range(ORDER_LIMIT):
        data = {
            "order_id": i,
            "user_id": f"tom_{i}",
            "total_cost": i,
            "items": "burger" if i % 2 == 0 else "pizza",  # Vary the item types
        }

        producer_order_details.send("order_details", json.dumps(data).encode("utf-8"))
        time.sleep(5)

    return "Orders sent successfully!"

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
