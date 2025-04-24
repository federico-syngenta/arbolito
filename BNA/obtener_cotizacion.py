import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import csv
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('exchange_rate_log.log'),
        logging.StreamHandler()
    ]
)

def get_exchange_rate():
    """Fetch USD to ARS exchange rate from BNA website"""
    logging.info("Starting exchange rate collection")
    
    # Configuration
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    
    try:
        # Initialize driver
        driver = webdriver.Chrome(options=chrome_options)
        
        # Open BNA website
        logging.info("Accessing BNA website")
        driver.get("https://www.bna.com.ar/")
        driver.maximize_window()
        time.sleep(5)  # Wait for page to load

        # Get exchange rate data
        try:
            fecha_cotizacion = driver.find_element(By.CLASS_NAME, 'fechaCot').text
            dolar_compra = driver.find_element(By.XPATH, '//*[@id="billetes"]/table/tbody/tr[1]/td[2]').text
            dolar_venta = driver.find_element(By.XPATH, '//*[@id="billetes"]/table/tbody/tr[1]/td[3]').text
            
            logging.info(f"Successfully obtained rates: Buy={dolar_compra}, Sell={dolar_venta} (Date: {fecha_cotizacion})")
            
            data = {
                'collection_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'exchange_date': fecha_cotizacion,
                'buy_rate': dolar_compra,
                'sell_rate': dolar_venta,
                'source': 'BNA',
                'status': 'Success'
            }
            
        except Exception as e:
            logging.error(f"Failed to extract data from page: {str(e)}")
            data = {
                'collection_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'status': f"Error: {str(e)}"
            }
            return None
            
        # Save to CSV
        save_to_csv(data)
        logging.info("Data successfully saved to CSV")
        
        return data
        
    except Exception as e:
        logging.error(f"Critical error in main execution: {str(e)}", exc_info=True)
        return None
        
    finally:
        try:
            driver.quit()
            logging.info("Browser session closed")
        except:
            logging.warning("Could not properly close browser session")

def save_to_csv(data):
    """Save collected data to CSV file"""
    file_exists = os.path.isfile('exchange_rates.csv')
    
    try:
        with open('exchange_rates.csv', 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['collection_time', 'exchange_date', 'buy_rate', 'sell_rate', 'source', 'status']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
                
            writer.writerow(data)
            
    except Exception as e:
        logging.error(f"Failed to save to CSV: {str(e)}")

if __name__ == "__main__":
    start_time = datetime.now()
    logging.info(f"=== Starting exchange rate collection at {start_time} ===")
    
    result = get_exchange_rate()
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    if result:
        logging.info(f"=== Completed successfully in {duration.total_seconds():.2f} seconds ===")
    else:
        logging.error(f"=== Failed after {duration.total_seconds():.2f} seconds ===")