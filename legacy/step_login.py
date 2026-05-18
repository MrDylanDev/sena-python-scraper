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

def login_step():
    print("--- 🔐 PASO 1: Iniciando Sesión ---")
    
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options)
    wait = WebDriverWait(driver, 30)
    
    try:
        print("1. Abriendo portal...")
        driver.get(URL_LOGIN)
        time.sleep(3)
        
        print("2. Seleccionando Aprendices...")
        aprendices_btn = wait.until(EC.element_to_be_clickable((By.ID, "aprendices")))
        driver.execute_script("arguments[0].click();", aprendices_btn)
        time.sleep(2)
        
        print("3. Ingresando datos...")
        user_input = wait.until(EC.visibility_of_element_located((By.ID, "tbLoginUsuario")))
        user_input.send_keys(USER)
        time.sleep(0.5)
        driver.find_element(By.ID, "__tbPasswordUsuario").send_keys(PASSWORD)
        time.sleep(1)
        
        print("4. Enviando formulario...")
        driver.find_element(By.ID, "ini_session_aprendiz").click()
        
        print("⏳ Esperando respuesta del servidor (Paso crítico)...")
        # Esperamos un tiempo prudente para que el servidor cree la sesión
        time.sleep(10)
        
        print("🛠️ Limpiando posibles bloqueos visuales...")
        # Eliminamos el spinner de carga y el overlay que traba la UI
        driver.execute_script("""
            var elementsToRemove = ['updProgress', 'updProgress1', 'IMGDIV'];
            elementsToRemove.forEach(id => {
                var el = document.getElementById(id);
                if (el) el.remove();
            });
            var overlays = document.querySelectorAll('.overLayBackground');
            overlays.forEach(ol => ol.remove());
            document.body.style.overflow = 'auto';
            document.body.style.opacity = '1';
        """)
        
        url_actual = driver.current_url
        print(f"📍 Ubicación actual: {url_actual}")
        
        # Si caemos en el error 404 pero la sesión existe, forzamos el Dashboard
        if "Default.aspx" in url_actual or "login.aspx" in url_actual:
            print("⚠️ El portal no redirigió bien. Intentando entrar al Dashboard directamente...")
            driver.get("https://caprendizaje.sena.edu.co/sgva/Aprendices/Index")
            time.sleep(5)
        
        print("5. Verificando Dashboard...")
        # Buscamos algo que solo esté adentro, como el nombre del usuario o el menú
        try:
            menu_presente = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Cerrar Sesión')] | //*[contains(text(), 'Buscar Empresa')]")))
            print("✅ ¡SESIÓN CONFIRMADA! Estamos adentro del Dashboard.")
            print("\nDeteniendo aquí para que revises la pantalla. No cierres el navegador.")
            # Mantenemos el navegador abierto para que el usuario confirme
            while True:
                time.sleep(1)
        except:
            print("❌ No se pudo confirmar el inicio de sesión. Revisá el navegador.")
            driver.save_screenshot("fallo_acceso.png")

    except Exception as e:
        print(f"💥 Error: {str(e)}")
    finally:
        # Por ahora no cerramos el driver para que el usuario lo vea
        pass

if __name__ == "__main__":
    login_step()
