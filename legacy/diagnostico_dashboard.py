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

def diagnostico_dashboard():
    print("--- 📸 Diagnóstico de Dashboard (Carga Infinita) ---")
    
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options)
    wait = WebDriverWait(driver, 40)
    
    try:
        print("1. Iniciando sesión...")
        driver.get(URL_LOGIN)
        wait.until(EC.element_to_be_clickable((By.ID, "aprendices"))).click()
        wait.until(EC.visibility_of_element_located((By.ID, "tbLoginUsuario"))).send_keys(USER)
        driver.find_element(By.ID, "__tbPasswordUsuario").send_keys(PASSWORD)
        driver.find_element(By.ID, "ini_session_aprendiz").click()
        
        print("2. Esperando 10 segundos para la carga inicial...")
        time.sleep(10)
        
        print("📸 Tomando capMerenguetura del estado 'Cargando'...")
        driver.save_screenshot("dashboard_cargando.png")
        
        print("📄 Guardando HTML del dashboard...")
        with open("dashboard_source.html", "w", encoding='utf-8') as f:
            f.write(driver.page_source)

        print("3. Intentando detectar el elemento de carga...")
        # Buscamos IDs comunes de spinners en el SENA
        ids_carga = ['updProgress', 'updProgress1', 'IMGDIV', 'preloader']
        for id_c in ids_carga:
            try:
                el = driver.find_element(By.ID, id_c)
                visible = el.is_displayed()
                print(f"   - Elemento '{id_c}': Encontrado, ¿Visible?: {visible}")
            except:
                pass

        print("4. Esperando a que desaparezca el bloqueo (máximo 60 seg)...")
        # Si el usuario dice que hay que esperar, vamos a esperar de verdad
        try:
            # Esperamos a que el spinner NO sea visible
            # Ajustamos el ID según lo que encontremos en el HTML
            wait.until_not(EC.visibility_of_element_located((By.ID, "updProgress")))
            print("✅ ¡El cartel de carga desapareció solo!")
        except:
            print("⏳ El cartel sigue ahí después de un minuto.")

        print("📸 Captura final tras espera...")
        driver.save_screenshot("dashboard_final_espera.png")
        
        print("\n--- Diagnóstico completo ---")
        print("Revisá 'dashboard_cargando.png' y 'dashboard_source.html'")

    except Exception as e:
        print(f"💥 Error: {str(e)}")
    finally:
        # Mantenemos abierto para inspección manual
        print("Navegador listo para revisión manual.")

if __name__ == "__main__":
    diagnostico_dashboard()
