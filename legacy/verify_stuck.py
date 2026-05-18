import os
import time
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

load_dotenv()

USER = os.getenv('SENA_USUARIO')
PASSWORD = os.getenv('SENA_PASSWORD')
URL_LOGIN = 'https://caprendizaje.sena.edu.co/sgva/SGVA_Diseno/pag/login.aspx'

def verify_stuck_dashboard():
    print("--- 📸 Iniciando Verificación de Bloqueo ---")
    
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options)
    wait = WebDriverWait(driver, 60)
    actions = ActionChains(driver)
    
    try:
        print("1. Login...")
        driver.get(URL_LOGIN)
        wait.until(EC.element_to_be_clickable((By.ID, "aprendices"))).click()
        time.sleep(2)
        
        driver.find_element(By.ID, "tbLoginUsuario").send_keys(USER)
        driver.find_element(By.ID, "__tbPasswordUsuario").send_keys(PASSWORD)
        time.sleep(2)
        
        login_btn = driver.find_element(By.ID, "ini_session_aprendiz")
        actions.move_to_element(login_btn).click().perform()
        
        print("⏳ Esperando aterrizaje en Dashboard...")
        # Esperamos a que la URL cambie
        time.sleep(15) 
        
        print(f"📍 URL actual: {driver.current_url}")
        
        print("📸 Tomando captura de pantalla...")
        driver.save_screenshot("stuck_dashboard.png")
        
        print("📄 Guardando código fuente para análisis...")
        with open("stuck_dashboard.html", "w", encoding='utf-8') as f:
            f.write(driver.page_source)
            
        print("\n--- ✅ Captura completada ---")
        print("Archivos generados: stuck_dashboard.png, stuck_dashboard.html")
        
        # Analizamos rápido el source por consola
        source = driver.page_source.lower()
        if "access to the path" in source:
            print("❗ ALERTA: Detecté el error de permisos en el código fuente.")
        if "updprogress" in source:
            print("❗ ALERTA: El elemento de carga (spinner) está presente en el código.")

    except Exception as e:
        print(f"💥 Error: {str(e)}")
    finally:
        print("Navegador listo para inspección manual.")

if __name__ == "__main__":
    verify_stuck_dashboard()
