import os
import time
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

load_dotenv()

USER = os.getenv('SENA_USUARIO')
PASSWORD = os.getenv('SENA_PASSWORD')
URL_LOGIN = 'https://caprendizaje.sena.edu.co/sgva/SGVA_Diseno/pag/login.aspx'

def stabilize_dashboard():
    print("--- 🛠️ PRUEBA DE ESTABILIZACIÓN DE DASHBOARD ---")
    
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options)
    wait = WebDriverWait(driver, 20)
    
    try:
        print("1. Intentando login...")
        driver.get(URL_LOGIN)
        
        # Seleccionamos Aprendices
        wait.until(EC.element_to_be_clickable((By.ID, "aprendices"))).click()
        time.sleep(2)
        
        # Llenamos datos
        wait.until(EC.visibility_of_element_located((By.ID, "tbLoginUsuario"))).send_keys(USER)
        driver.find_element(By.ID, "__tbPasswordUsuario").send_keys(PASSWORD)
        
        print("2. Enviando credenciales...")
        driver.find_element(By.ID, "ini_session_aprendiz").click()
        
        # Esperamos el primer aterrizaje
        time.sleep(10)
        url_inicial = driver.current_url
        print(f"📍 Aterrizamos en: {url_inicial}")
        
        # --- ESTRATEGIA DE REINTENTO INTERNO ---
        source = driver.page_source.lower()
        if "server error" in source or "access to the path" in source or "404" in source:
            print("⚠️ Error de servidor detectado. Aplicando refresco de seguridad...")
            driver.refresh()
            time.sleep(8)
            print(f"📍 Tras refresco, estamos en: {driver.current_url}")
        
        # Si seguimos con error, intentamos forzar la URL que vimos antes
        if "login.aspx" in driver.current_url or "Default.aspx" in driver.current_url:
            print("🔗 Forzando navegación a la URL del Index...")
            driver.get("https://caprendizaje.sena.edu.co/sgva/Aprendices/Index")
            time.sleep(8)

        # Verificación final
        print("3. Verificando estado final...")
        try:
            # Buscamos algo que confirme que estamos en una zona privada
            # "Cerrar Sesión" es el mejor indicador
            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Cerrar Sesión')] | //*[contains(text(), 'Salir')]")))
            print("\n✅ ¡LOGRADO! Estamos adentro del Dashboard de forma estable.")
            print("No cierres el navegador, voy a sacar una captura de lo que se ve.")
            driver.save_screenshot("dashboard_exito.png")
        except:
            print("\n❌ No pudimos confirmar la entrada.")
            driver.save_screenshot("dashboard_fallo.png")
            print("Revisá 'dashboard_fallo.png' para ver qué pantalla quedó.")

    except Exception as e:
        print(f"💥 Error inesperado: {str(e)}")
    finally:
        print("\n--- Fin de la prueba de entrada ---")
        # No cerramos para que puedas ver el resultado
        while True: time.sleep(1)

if __name__ == "__main__":
    stabilize_dashboard()
