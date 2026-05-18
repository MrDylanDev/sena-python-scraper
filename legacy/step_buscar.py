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

def run_step_2():
    print("--- 🔍 PASO 2: Búsqueda y Extracción Forzada ---")
    
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options)
    wait = WebDriverWait(driver, 30)
    
    def limpiar_pantalla():
        # Esta función borra cualquier cosa que tape la vista
        driver.execute_script("""
            var ids = ['updProgress', 'updProgress1', 'IMGDIV', 'preloader', 'loader'];
            ids.forEach(id => { var e = document.getElementById(id); if (e) e.remove(); });
            var overlays = document.querySelectorAll('.overLayBackground, .modal-backdrop');
            overlays.forEach(ol => ol.remove());
            document.body.style.overflow = 'auto';
            document.body.style.opacity = '1';
        """)

    try:
        print("1. Login...")
        driver.get(URL_LOGIN)
        wait.until(EC.element_to_be_clickable((By.ID, "aprendices"))).click()
        wait.until(EC.visibility_of_element_located((By.ID, "tbLoginUsuario"))).send_keys(USER)
        driver.find_element(By.ID, "__tbPasswordUsuario").send_keys(PASSWORD)
        driver.find_element(By.ID, "ini_session_aprendiz").click()
        
        time.sleep(10) # Espera de seguridad
        limpiar_pantalla()

        print("2. Accediendo a 'Buscar Empresa' (Vía Forzada)...")
        # Intentamos clic por JS que ignora si hay algo tapando
        try:
            btn_buscar = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Buscar Empresa')]")))
            driver.execute_script("arguments[0].click();", btn_buscar)
        except:
            print("⚠️ Menú no encontrado, saltando directo a la URL de búsqueda...")
            driver.get("https://caprendizaje.sena.edu.co/sgva/SGVA_Diseno/pag/ConsultarEmpresa.aspx")
        
        time.sleep(5)
        limpiar_pantalla()

        print("3. Filtrando Antioquia...")
        # Esperamos el dropdown
        dept_el = wait.until(EC.presence_of_element_located((By.XPATH, "//select[contains(@id, 'ddlDepartamento')]")))
        Select(dept_el).select_by_visible_text("ANTIOQUIA")
        time.sleep(2)
        
        print("4. Ejecutando búsqueda...")
        # Clic forzado en el botón de consulta
        driver.execute_script("""
            var btn = document.querySelector('input[value*="Consultar"], [id*="btnConsultar"], input[value*="Buscar"]');
            if (btn) btn.click();
        """)
        
        print("⏳ Esperando resultados...")
        time.sleep(8)
        limpiar_pantalla()

        # 5. Extracción
        print("--- 🔎 Iniciando extracción de correos ---")
        results = []
        # Localizamos los botones de "Ver-aplicar"
        botones = driver.find_elements(By.XPATH, "//input[@value='Ver-aplicar'] | //a[contains(text(), 'Ver-aplicar')]")
        print(f"Se detectaron {len(botones)} posibles empresas.")

        for i in range(len(botones)):
            try:
                # Refrescamos la lista para no perder la referencia
                btns_actuales = driver.find_elements(By.XPATH, "//input[@value='Ver-aplicar'] | //a[contains(text(), 'Ver-aplicar')]")
                btn = btns_actuales[i]
                
                # Scroll y clic forzado
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", btn)
                
                time.sleep(5) # El modal del SENA es MUY lento
                
                # Sacamos todo el texto de la página para buscar el mail con regex
                source = driver.page_source
                emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', source)
                email = emails[0] if emails else "No encontrado"
                
                # Intentamos sacar el nombre
                try:
                    nombre = driver.execute_script("return document.querySelector('[id*=\"lblNombreEmpresa\"], h4, h3').innerText")
                except:
                    nombre = f"Empresa {i+1}"
                
                print(f"   [{i+1}] {nombre.strip()} -> {email}")
                results.append({"empresa": nombre.strip(), "correo": email})
                
                # Cerrar modal (Escape o clic en fondo)
                driver.find_element(By.TAG_NAME, "body").send_keys("\ue00c")
                time.sleep(2)
                
            except Exception as e:
                print(f"   ⚠️ Error en fila {i+1}, continuando...")
                driver.find_element(By.TAG_NAME, "body").send_keys("\ue00c")

        # Guardar
        with open('lista_correos_sena.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        
        print(f"\n🎉 ¡LISTO! Se guardaron {len(results)} correos en 'lista_correos_sena.json'")

    except Exception as e:
        print(f"💥 Falló el proceso: {str(e)}")
        driver.save_screenshot("error_busqueda.png")
    finally:
        print("Cerrando navegador...")
        driver.quit()

if __name__ == "__main__":
    run_step_2()
