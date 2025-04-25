import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import json
import requests
import csv
import os
import logging

# Logging configuration
os.makedirs("log", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("log/exchange_rate_log.log"),
        logging.StreamHandler(),
    ],
)


def start_browser(browse):
    """Start the browser 'edge' or 'chrome' with the specified options"""
    if browse == "edge":
        options = webdriver.EdgeOptions()
        options.use_chromium = True
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        driver = webdriver.Edge(options=options)
    elif browse == "chrome":
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        driver = webdriver.Chrome(options=options)
    else:
        raise ValueError("Unsupported browser type. Use 'edge' or 'chrome'.")
    return driver


def get_exchange_rate_BNA(browser="chrome"):
    """Fetch USD to ARS exchange rate from BNA website"""
    logging.info("Starting BNA exchange rate collection")

    try:
        # Initialize driver
        driver = start_browser(browser)

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


def get_exchange_rate_banco_provincia(browser="chrome"):
    """Fetch USD to ARS exchange rate from Banco Provincia website"""
    logging.info("Starting Banco Provincia exchange rate collection")

    try:
        # Initialize driver
        driver = start_browser(browser)

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


def get_exchange_rate_bancociudad(browser="chrome"):
    """Fetch USD to ARS exchange rate from Banco Ciudad website"""
    logging.info("Starting Banco Ciudad exchange rate collection")

    url = "https://bancociudad.com.ar/institucional/herramientas/getCotizacionesInicio"
    params = {"_": int(datetime.now().timestamp() * 1000)}

    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://bancociudad.com.ar/institucional/",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }

    session = requests.Session()
    session.headers.update(headers)

    # Try to get and set cookies first
    try:
        session.get("https://bancociudad.com.ar/institucional/", timeout=10)
    except Exception as e:
        logging.warning(f"Failed to get initial cookies: {str(e)}")

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = session.get(url, params=params, timeout=10)
            response.raise_for_status()

            try:
                json_data = response.json()
            except json.JSONDecodeError:
                logging.error(
                    f"Failed to decode JSON from Banco Ciudad. Response content: {response.text}"
                )
                if "CAPTCHA" in response.text:
                    raise Exception("CAPTCHA detected")
                raise Exception("Failed to decode JSON from Banco Ciudad")

            dolar = json_data["data"]["dolar"]
            compra = dolar["compra"].replace("$", "").replace(".", "").replace(",", ".")
            venta = dolar["venta"].replace("$", "").replace(".", "").replace(",", ".")

            logging.info(f"Banco Ciudad rates: Compra={compra}, Venta={venta}")
            return {
                "collection_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "exchange_date": datetime.now().strftime("%d/%m/%Y"),
                "buy_rate": float(compra),
                "sell_rate": float(venta),
                "source": "Banco Ciudad",
                "status": "Success",
            }

        except Exception as e:
            logging.error(f"Attempt {attempt + 1} failed for Banco Ciudad: {str(e)}")
            if attempt == max_retries - 1:
                return {
                    "collection_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "exchange_date": "",
                    "buy_rate": None,
                    "sell_rate": None,
                    "source": "Banco Ciudad",
                    "status": f"Error: {str(e)}",
                }
            time.sleep(5 * (attempt + 1))  # Exponential backoff

    # This should never be reached due to the return in the loop, but just in case:
    return {
        "collection_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "exchange_date": "",
        "buy_rate": None,
        "sell_rate": None,
        "source": "Banco Ciudad",
        "status": "Error: Max retries reached",
    }
    time.sleep(5)  # Wait for 5 seconds before retrying


def save_to_csv(data_list):
    """Save collected data to CSV file"""
    os.makedirs("data", exist_ok=True)  # Crea la carpeta si no existe
    csv_path = os.path.abspath(os.path.join("data", "exchange_rates_v2.csv"))
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
                data["exchange_date"] = normalize_date(data["exchange_date"])
                data["buy_rate"] = normalize_number(data["buy_rate"])
                data["sell_rate"] = normalize_number(data["sell_rate"])
                writer.writerow(data)

        logging.info(f"Successfully saved {len(data_list)} records to CSV")

    except Exception as e:
        logging.error(f"Failed to save to CSV: {str(e)}")


def normalize_date(date_str):
    """Convierte varias formas de fecha a YYYY-MM-DD"""
    for fmt in ("%d/%m/%Y", "%d/%-m/%Y", "%Y-%m-%d"):  # el segundo para 25/4/2025
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return date_str  # si falla, devuelve el original


def normalize_number(num_str):
    """Convierte string a float, reemplazando coma por punto si hace falta"""
    try:
        return float(num_str.replace(",", "."))
    except (ValueError, AttributeError):
        return num_str  # si falla, deja el valor original


def main(browser="chrome"):
    start_time = datetime.now()
    logging.info(f"=== Starting exchange rate collection at {start_time} ===")

    # Collect data from both sources
    results = []
    results.append(get_exchange_rate_BNA(browser))
    results.append(get_exchange_rate_banco_provincia(browser))
    results.append(get_exchange_rate_bbva())
    results.append(get_exchange_rate_bancociudad(browser))

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
    input_browser = input("Enter browser (edge/chrome): ").strip().lower()
    if input_browser not in ["edge", "chrome"]:
        print(f"Invalid browser choice {input_browser}. Choose 'edge' or 'chrome'...")
        print("chrome is selected by default...")
        input_browser = "chrome"
    main(input_browser)
