from selenium import webdriver
from selenium.webdriver.common.by import By

# Configuración de Selenium
driver = webdriver.Chrome()  # Asegúrate de tener el driver de Chrome instalado
driver.get("https://www.bna.com.ar/")

# Extracción de datos
compra = driver.find_element(By.XPATH, "//div[@class='cotizacion_compra']").text
venta = driver.find_element(By.XPATH, "//div[@class='cotizacion_venta']").text
fecha = driver.find_element(By.XPATH, "//div[@class='cotizacion_fecha']").text

# Muestra los resultados
print(f"Fecha: {fecha}")
print(f"Dólar Compra: {compra}")
print(f"Dólar Venta: {venta}")

# Cierra el navegador
driver.quit()