import os
import time
import re
import json
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

load_dotenv()

USER = os.getenv('SENA_USUARIO')
PASSWORD = os.getenv('SENA_PASSWORD')
URL_LOGIN = 'https://caprendizaje.sena.edu.co/sgva/SGVA_Diseno/pag/login.aspx'

def bypass_server_error():
    print("--- 🚀 Modo Evasión de Error de Servidor ---")
    
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options)
    wait = WebDriverWait(driver, 30)
    
    try:
        print("1. Intentando login...")
        driver.get(URL_LOGIN)
        wait.until(EC.element_to_be_clickable((By.ID, "aprendices"))).click()
        wait.until(EC.visibility_of_element_located((By.ID, "tbLoginUsuario"))).send_keys(USER)
        driver.find_element(By.ID, "__tbPasswordUsuario").send_keys(PASSWORD)
        driver.find_element(By.ID, "ini_session_aprendiz").click()
        
        print("⏳ Esperando 10 segundos para que el servidor procese la sesión...")
        time.sleep(10)

        # SALTAMOS EL ERROR: Vamos directo a la página de búsqueda
        # Probamos las URLs que suelen estar activas para aprendices
        urls_bypass = [
            "https://caprendizaje.sena.edu.co/sgva/SGVA_Diseno/pag/ConsultarEmpresa.aspx",
            "https://caprendizaje.sena.edu.co/sgva/Aprendices/ConsultarEmpresa",
            "https://caprendizaje.sena.edu.co/sgva/SGVA_Diseno/pag/PAG_APRENDIZ/buscar_empresa.aspx"
        ]

        exito = False
        for url in urls_bypass:
            print(f"🔗 Intentando saltar directo a: {url}")
            driver.get(url)
            time.sleep(5)
            
            # Si vemos el dropdown de departamentos, es que logramos entrar!
            try:
                if driver.find_elements(By.XPATH, "//select[contains(@id, 'ddlDepartamento')]"):
                    print("✅ ¡EXITO! Saltamos el error del servidor y estamos en la búsqueda.")
                    exito = True
                    break
            except:
                continue

        if not exito:
            print("❌ No logramos evadir el error. El portal del SENA está realmente caído en este momento.")
            return

        # Si entramos, procedemos con Antioquia
        print("Filtrando por Antioquia...")
        dept = driver.find_element(By.XPATH, "//select[contains(@id, 'ddlDepartamento')]")
        Select(dept).select_by_visible_text("ANTIOQUIA")
        time.sleep(2)
        
        print("Buscando empresas...")
        driver.execute_script("document.querySelector('input[value*=\"Consultar\"], [id*=\"btnConsultar\"]').click();")
        time.sleep(6)

        # Extracción
        botones = driver.find_elements(By.XPATH, "//input[@value='Ver-aplicar'] | //a[contains(text(), 'Ver-aplicar')]")
        print(f"Se encontraron {len(botones)} empresas.")
        
        results = []
        for i in range(len(botones)):
            btns = driver.find_elements(By.XPATH, "//input[@value='Ver-aplicar'] | //a[contains(text(), 'Ver-aplicar')]")
            driver.execute_script("arguments[0].click();", btns[i])
            time.sleep(4)
            
            source = driver.page_source
            mail = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', source)
            
            email_final = mail[0] if mail else "No encontrado"
            print(f"Empresa {i+1}: {email_final}")
            results.append({"empresa": f"Empresa {i+1}", "correo": email_final})
            
            driver.find_element(By.TAG_NAME, "body").send_keys("\ue00c")
            time.sleep(2)

        with open('lista_final.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        print("✅ Todo guardado en lista_final.json")

    except Exception as e:
        print(f"💥 Error: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    bypass_server_error()
