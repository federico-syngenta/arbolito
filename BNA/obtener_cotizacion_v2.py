import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import requests
import csv
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("exchange_rate_log.log"), logging.StreamHandler()],
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
            fecha_cotizacion = driver.find_element(By.CLASS_NAME, "fechaCot").text
            dolar_compra = driver.find_element(
                By.XPATH, '//*[@id="billetes"]/table/tbody/tr[1]/td[2]'
            ).text
            dolar_venta = driver.find_element(
                By.XPATH, '//*[@id="billetes"]/table/tbody/tr[1]/td[3]'
            ).text

            logging.info(
                f"Successfully obtained BNA rates: Buy={dolar_compra}, Sell={dolar_venta} (Date: {fecha_cotizacion})"
            )

            data = {
                "collection_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "exchange_date": fecha_cotizacion,
                "buy_rate": dolar_compra,
                "sell_rate": dolar_venta,
                "source": "BNA",
                "status": "Success",
            }

        except Exception as e:
            logging.error(f"Failed to extract data from BNA page: {str(e)}")
            data = {
                "collection_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "exchange_date": "",
                "buy_rate": "",
                "sell_rate": "",
                "source": "BNA",
                "status": f"Error: {str(e)}",
            }

        return data

    except Exception as e:
        logging.error(f"Critical error in BNA execution: {str(e)}", exc_info=True)
        return {
            "collection_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "exchange_date": "",
            "buy_rate": "",
            "sell_rate": "",
            "source": "BNA",
            "status": f"Critical Error: {str(e)}",
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
            rate_elements = driver.find_elements(
                By.XPATH, '//div[contains(@class, "paginas__sc-1t8sitw-1")]'
            )

            if len(rate_elements) >= 2:
                dolar_compra = rate_elements[0].text.replace("Compra: $", "").strip()
                dolar_venta = rate_elements[1].text.replace("Venta: $", "").strip()

                logging.info(
                    f"Successfully obtained Banco Provincia rates: Buy={dolar_compra}, Sell={dolar_venta}"
                )

                data = {
                    "collection_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "exchange_date": fecha_cotizacion,
                    "buy_rate": dolar_compra.replace(".", "").replace(
                        ",", "."
                    ),  # Format to decimal
                    "sell_rate": dolar_venta.replace(".", "").replace(
                        ",", "."
                    ),  # Format to decimal
                    "source": "Banco Provincia",
                    "status": "Success",
                }
            else:
                raise Exception("Could not find both buy and sell rate elements")

        except Exception as e:
            logging.error(f"Failed to extract data from Banco Provincia page: {str(e)}")
            data = {
                "collection_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "exchange_date": "",
                "buy_rate": "",
                "sell_rate": "",
                "source": "Banco Provincia",
                "status": f"Error: {str(e)}",
            }

        return data

    except Exception as e:
        logging.error(
            f"Critical error in Banco Provincia execution: {str(e)}", exc_info=True
        )
        return {
            "collection_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "exchange_date": "",
            "buy_rate": "",
            "sell_rate": "",
            "source": "Banco Provincia",
            "status": f"Critical Error: {str(e)}",
        }

    finally:
        try:
            driver.quit()
            logging.info("Banco Provincia browser session closed")
        except:
            logging.warning("Could not properly close Banco Provincia browser session")


def get_exchange_rate_bbva():
    logging.info("Starting BBVA exchange rate collection (using JSON endpoint)")

    url = "https://servicios.bbva.com.ar/openmarket/servicios/cotizaciones/monedaExtranjera"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        logging.debug(f"Full BBVA response:\n{json.dumps(data, indent=2)}")

        for item in data.get("respuesta", []):
            moneda = item.get("moneda", {})
            if "dolar" in moneda.get("descripcionLarga", "").lower():
                compra = float(item["precioCompra"])
                venta = float(item["precioVenta"])
                logging.info(f"BBVA rates: Compra={compra}, Venta={venta}")
                return {
                    "collection_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "exchange_date": datetime.now().strftime("%Y-%m-%d"),
                    "buy_rate": compra,
                    "sell_rate": venta,
                    "source": "BBVA",
                    "status": "Success",
                }

        raise Exception("Dolares rate not found in BBVA response")

    except Exception as e:
        logging.error(f"Error scraping BBVA exchange rate: {e}")
        return {
            "collection_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "exchange_date": "",
            "buy_rate": None,
            "sell_rate": None,
            "source": "BBVA",
            "status": f"Error: {str(e)}",
        }


def save_to_csv(data_list):
    """Save collected data to CSV file"""
    csv_path = os.path.abspath("exchange_rates_v2.csv")
    logging.info(f"Saving data to CSV at: {csv_path}")

    try:
        file_exists = os.path.isfile(csv_path)

        with open(csv_path, "a", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "collection_time",
                "exchange_date",
                "buy_rate",
                "sell_rate",
                "source",
                "status",
            ]
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

    # Collect data from both sources
    results = []
    results.append(get_exchange_rate_BNA())
    results.append(get_exchange_rate_banco_provincia())
    results.append(get_exchange_rate_bbva())

    # Save all results to CSV
    save_to_csv(results)

    end_time = datetime.now()
    duration = end_time - start_time

    success_count = sum(1 for result in results if result.get("status") == "Success")

    if success_count > 0:
        logging.info(
            f"=== Completed with {success_count}/3 successful collections in {duration.total_seconds():.2f} seconds ==="
        )
    else:
        logging.error(
            f"=== All collections failed after {duration.total_seconds():.2f} seconds ==="
        )


if __name__ == "__main__":
    main()
