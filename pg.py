from flask import Flask, render_template, request, redirect, url_for, session
from flask_pymongo import PyMongo
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Set a secret key for session management

# MongoDB configuration
app.config["MONGO_URI"] = "mongodb://localhost:27017/pg_database"
mongo = PyMongo(app)
pg_collection = mongo.db.pg_accommodations

# Home route
@app.route('/')
def home():
    return render_template('home.html')

# Route for searching PGs
@app.route('/search_pg', methods=['GET', 'POST'])
def search_pg():
    if request.method == 'POST':
        location = request.form['location']
        results = list(pg_collection.find({"location": {"$regex": location, "$options": "i"}}))

        # Format amenities list into a comma-separated string
        for result in results:
            result['amenities'] = ", ".join(result['amenities'])

        return render_template('pg_results.html', results=results, location=location)
    return render_template('search_pg.html')

# Route for handling favicon requests
@app.route('/favicon.ico')
def favicon():
    return ''  # Or serve a real favicon file if you have one

# Route for scraping data
@app.route('/scrape')
def scrape():
    options = Options()
    options.add_argument("--headless")  # Run headless Chrome, without GUI (optional)

    # Use WebDriverManager to download and manage ChromeDriver
    service = ChromeService(ChromeDriverManager().install())

    # Initialize WebDriver with the correct service and options
    driver = webdriver.Chrome(service=service, options=options)

    # Open the website
    website = 'https://www.justdial.com/Bangalore/Paying-Guest-Accommodations-in-M-S-Ramaiah-Road-Mathikere/nct-10934649'
    driver.get(website)

    # Allow the page to load
    time.sleep(3)

    # Scrape the data (update the following lines based on actual element attributes)
    pg_elements = driver.find_elements(By.CSS_SELECTOR, '.your-css-selector')  # Adjust the CSS selector

    # Extract and insert the data
    for pg in pg_elements:
        name = pg.find_element(By.CSS_SELECTOR, '.store-name').text  # Adjust the CSS selector
        location = "Mathikere, Bangalore"  # This should be dynamic based on scraping
        contact = pg.find_element(By.CSS_SELECTOR, '.contact-number').text  # Adjust the CSS selector
        address = pg.find_element(By.CSS_SELECTOR, '.address-class').text  # Adjust the CSS selector
        amenities = ["Wi-Fi", "Laundry", "Meals"]  # This should be dynamic based on scraping

        pg_document = {
            "name": name,
            "location": location,
            "contact": contact,
            "address": address,
            "amenities": amenities
        }

        # Print the document to console for debugging
        print(pg_document)

        # Insert the document into MongoDB
        pg_collection.insert_one(pg_document)

    # Close the browser
    driver.quit()

    # Redirect to the search page after scraping is completed
    return redirect(url_for('search_pg'))
if __name__ == '__main__':
    app.run(debug=True)