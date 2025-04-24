from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    # Configuración de Playwright
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://www.bna.com.ar/")
    
    # Extracción de datos
    compra = page.inner_text("div.cotizacion_compra")
    venta = page.inner_text("div.cotizacion_venta")
    fecha = page.inner_text("div.cotizacion_fecha")
    
    # Muestra los resultados
    print(f"Fecha: {fecha}")
    print(f"Dólar Compra: {compra}")
    print(f"Dólar Venta: {venta}")
    
    # Cierra el navegador
    browser.close()
