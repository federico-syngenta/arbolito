import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import csv
import os
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('exchange_rate_log.log'),
        logging.StreamHandler()
    ]
)

def get_exchange_rate_BNA():
    """Fetch USD to ARS exchange rate from BNA website"""
    logging.info("Starting BNA exchange rate collection")
   
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
           
            logging.info(f"Successfully obtained BNA rates: Buy={dolar_compra}, Sell={dolar_venta} (Date: {fecha_cotizacion})")
           
            data = {
                'collection_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'exchange_date': fecha_cotizacion,
                'buy_rate': dolar_compra,
                'sell_rate': dolar_venta,
                'source': 'BNA',
                'status': 'Success'
            }
           
        except Exception as e:
            logging.error(f"Failed to extract data from BNA page: {str(e)}")
            data = {
                'collection_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'exchange_date': '',
                'buy_rate': '',
                'sell_rate': '',
                'source': 'BNA',
                'status': f"Error: {str(e)}"
            }
           
        return data
       
    except Exception as e:
        logging.error(f"Critical error in BNA execution: {str(e)}", exc_info=True)
        return {
            'collection_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'exchange_date': '',
            'buy_rate': '',
            'sell_rate': '',
            'source': 'BNA',
            'status': f"Critical Error: {str(e)}"
        }
       
    finally:
        try:
            driver.quit()
            logging.info("BNA browser session closed")
        except:
            logging.warning("Could not properly close BNA browser session")

def get_exchange_rate_banco_provincia():
    """Fetch USD to ARS exchange rate from Banco Provincia website"""
    logging.info("Starting Banco Provincia exchange rate collection")
   
    # Configuration
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
   
    try:
        # Initialize driver
        driver = webdriver.Chrome(options=chrome_options)
       
        # Open Banco Provincia website
        logging.info("Accessing Banco Provincia website")
        driver.get("https://www.bancoprovincia.com.ar/")
        driver.maximize_window()
        time.sleep(5)  # Wait for page to load

        # Get exchange rate data
        try:
            fecha_cotizacion = datetime.now().strftime("%d/%m/%Y")
           
            # Find all rate elements - they should be in order: Compra, Venta
            rate_elements = driver.find_elements(By.XPATH, '//div[contains(@class, "paginas__sc-1t8sitw-1")]')
           
            if len(rate_elements) >= 2:
                dolar_compra = rate_elements[0].text.replace("Compra: $", "").strip()
                dolar_venta = rate_elements[1].text.replace("Venta: $", "").strip()
               
                logging.info(f"Successfully obtained Banco Provincia rates: Buy={dolar_compra}, Sell={dolar_venta}")
               
                data = {
                    'collection_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'exchange_date': fecha_cotizacion,
                    'buy_rate': dolar_compra.replace('.', '').replace(',', '.'),  # Format to decimal
                    'sell_rate': dolar_venta.replace('.', '').replace(',', '.'),   # Format to decimal
                    'source': 'Banco Provincia',
                    'status': 'Success'
                }
            else:
                raise Exception("Could not find both buy and sell rate elements")
           
        except Exception as e:
            logging.error(f"Failed to extract data from Banco Provincia page: {str(e)}")
            data = {
                'collection_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'exchange_date': '',
                'buy_rate': '',
                'sell_rate': '',
                'source': 'Banco Provincia',
                'status': f"Error: {str(e)}"
            }
           
        return data
       
    except Exception as e:
        logging.error(f"Critical error in Banco Provincia execution: {str(e)}", exc_info=True)
        return {
            'collection_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'exchange_date': '',
            'buy_rate': '',
            'sell_rate': '',
            'source': 'Banco Provincia',
            'status': f"Critical Error: {str(e)}"
        }
       
    finally:
        try:
            driver.quit()
            logging.info("Banco Provincia browser session closed")
        except:
            logging.warning("Could not properly close Banco Provincia browser session")

def get_exchange_rate_bancociudad():
    logging.info("Starting Banco Ciudad exchange rate collection")

    url = "https://bancociudad.com.ar/institucional/herramientas/getCotizacionesInicio"
    params = {
        "_": int(datetime.now().timestamp() * 1000)
    }

    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://bancociudad.com.ar/institucional/",
    }

    cookies = {
    "__uzma": "fadd7c5a-8008-4392-af92-614565dbbb94",
    "__uzmb": "1745523191",
    "__uzme": "2954",
    "__ssds": "3",
    "__ssuzjsr3": "a9be0cd8e",
    "__uzmbj3": "1745524217",
    "__uzmlj3": "mOcoaA9AcxS578823r4INpxvaZEQ8lVc6NhWnGM=",
    "_gcl_au": "1.1.1367185401.1745524218",
    "_ga": "GA1.1.827248151.1745524218",
    "_fbp": "fb.2.1745524218867.663776400689637672",
    "__uzmaj3": "fadd7c5a-8008-4392-af92-614565dbbb94",
    "__uzmcj3": "941041334171",
    "__uzmdj3": "1745524245",
    "__uzmfj3": "7f600093b5a530-4929-4962-ae55-719e507131361745524217442792",
    "uzmxj": "7f90006198bab7-3abd-4d69-b680-30a5580c43ce1-1745524217442792",
    "WWWBCBA": "rd2o00000000000000000000ffffac166159o8081",
    "_ga_S65TZ8VLMZ": "GS1.1.1745524218.1.1.1745524380.60.0.0",
    "__uzmc": "283289428561",
    "__uzmd": "1745524380",
    "__uzmf": "7f600093b5a530-4929-4962-ae55-719e507131361745523191035118925",
    "uzmx": "7f90006198bab7-3abd-4d69-bb80-30a5580c43ce1-1745523191035118925"
            }

    try:
        response = requests.get(url, headers=headers, params=params, cookies=cookies, timeout=10)
        response.raise_for_status()

        try:
            json_data = response.json()
        except json.JSONDecodeError:
            logging.error(f"Failed to decode JSON from Banco Ciudad. Response content: {response.text}")
            if "CAPTCHA" in response.text:
                return {
                    'collection_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'exchange_date': datetime.now().strftime("%d/%m/%Y"),
                    'buy_rate': None,
                    'sell_rate': None,
                    'source': 'Banco Ciudad',
                    'status': 'Error: CAPTCHA detected'
                }
            raise Exception("Failed to decode JSON from Banco Ciudad")

        dolar = json_data["data"]["dolar"]
        compra = dolar["compra"].replace("$", "").replace(".", "").replace(",", ".")
        venta = dolar["venta"].replace("$", "").replace(".", "").replace(",", ".")

        logging.info(f"Banco Ciudad rates: Compra={compra}, Venta={venta}")
        return {
            'collection_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'exchange_date': datetime.now().strftime("%d/%m/%Y"),
            'buy_rate': float(compra),
            'sell_rate': float(venta),
            'source': 'Banco Ciudad',
            'status': 'Success'
        }

    except Exception as e:
        logging.error(f"Failed to get Banco Ciudad direct rate: {str(e)}", exc_info=True)
        return {
            'collection_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'exchange_date': '',
            'buy_rate': None,
            'sell_rate': None,
            'source': 'Banco Ciudad',
            'status': f"Error: {str(e)}"
        }

def save_to_csv(data_list):
    """Save collected data to CSV file"""
    csv_path = os.path.abspath('exchange_rates.csv')
    logging.info(f"Saving data to CSV at: {csv_path}")
   
    try:
        file_exists = os.path.isfile(csv_path)
       
        with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['collection_time', 'exchange_date', 'buy_rate', 'sell_rate', 'source', 'status']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
           
            if not file_exists:
                writer.writeheader()
               
            for data in data_list:
                writer.writerow(data)
               
        logging.info(f"Successfully saved {len(data_list)} records to CSV")
       
    except Exception as e:
        logging.error(f"Failed to save to CSV: {str(e)}")

def main():
    start_time = datetime.now()
    logging.info(f"=== Starting exchange rate collection at {start_time} ===")
   
    # Collect data from all sources
    results = []
    for func in [get_exchange_rate_BNA, get_exchange_rate_banco_provincia, get_exchange_rate_bancociudad]:
        try:
            result = func()
            results.append(result)
        except Exception as e:
            logging.error(f"Error in {func.__name__}: {str(e)}")
            results.append({
                'collection_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'exchange_date': '',
                'buy_rate': None,
                'sell_rate': None,
                'source': func.__name__.replace('get_exchange_rate_', ''),
                'status': f"Error: {str(e)}"
            })

    # Save all results to CSV
    save_to_csv(results)
   
    end_time = datetime.now()
    duration = end_time - start_time
   
    success_count = sum(1 for result in results if result.get('status') == 'Success')
   
    if success_count > 0:
        logging.info(f"=== Completed with {success_count}/3 successful collections in {duration.total_seconds():.2f} seconds ===")
    else:
        logging.error(f"=== All collections failed after {duration.total_seconds():.2f} seconds ===")

if __name__ == "__main__":
    main()