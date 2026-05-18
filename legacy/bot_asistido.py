import os
import time
import re
import json
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def run_hybrid_bot():
    print("\n--- 🤖 BOT ASISTIDO: EL MINERO DE CORREOS ---")
    print("1. Voy a abrir una ventana de Chrome.")
    print("2. POR FAVOR: Entra al portal del SENA y navega hasta la lista de empresas de ANTIOQUIA.")
    print("3. Cuando yo vea los botones de 'Ver-aplicar', ¡empiezo a trabajar solo!\n")
    
    # Creamos una carpeta para guardar tu sesión de Chrome
    perfil_dir = os.path.join(os.getcwd(), "perfil_sena")
    if not os.path.exists(perfil_dir):
        os.makedirs(perfil_dir)

    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={perfil_dir}")
    
    driver = uc.Chrome(options=options)
    
    try:
        # Vamos al login para empezar
        driver.get("https://caprendizaje.sena.edu.co/sgva/SGVA_Diseno/pag/login.aspx")
        
        print("⏳ ESPERANDO POR VOS...")
        print("Tip: Navega hasta que veas los botones que dicen 'Ver-aplicar'.")

        # Bucle de detección: esperamos a que el usuario llegue a la página correcta
        while True:
            try:
                # Si encontramos al menos un botón de "Ver-aplicar", es que el usuario ya llegó
                botones = driver.find_elements(By.XPATH, "//input[@value='Ver-aplicar'] | //a[contains(text(), 'Ver-aplicar')]")
                if len(botones) > 0:
                    print(f"\n✅ ¡PÁGINA DETECTADA! Encontré {len(botones)} empresas.")
                    print("🚀 Tomando el control para extraer los correos...")
                    break
            except:
                pass
            time.sleep(2)

        # --- INICIO DE EXTRACCIÓN AUTOMÁTICA ---
        
        # Función para limpiar el cartel de carga que el SENA deja pegado
        def limpiar_basura_visual():
            driver.execute_script("""
                var ids = ['updProgress', 'updProgress1', 'IMGDIV', 'preloader'];
                ids.forEach(id => { var e = document.getElementById(id); if (e) e.remove(); });
                var overlays = document.querySelectorAll('.overLayBackground');
                overlays.forEach(ol => ol.remove());
                document.body.style.overflow = 'auto';
            """)

        results = []
        for i in range(len(botones)):
            try:
                # Refrescamos la lista de botones cada vez
                limpiar_basura_visual()
                btns_actuales = driver.find_elements(By.XPATH, "//input[@value='Ver-aplicar'] | //a[contains(text(), 'Ver-aplicar')]")
                btn = btns_actuales[i]
                
                # Scroll y clic vía JavaScript (para que no falle por overlays)
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", btn)
                
                print(f"   [{i+1}/{len(botones)}] Abriendo detalles...")
                time.sleep(4) # Espera generosa para el modal
                
                # Extraemos el nombre y el correo
                source = driver.page_source
                mail = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', source)
                email_final = mail[0] if mail else "No encontrado"
                
                try:
                    nombre = driver.execute_script("return document.querySelector('[id*=\"lblNombreEmpresa\"], h4, h3').innerText")
                except:
                    nombre = f"Empresa {i+1}"
                
                print(f"      🏢 {nombre.strip()} -> 📧 {email_final}")
                results.append({"empresa": nombre.strip(), "correo": email_final})
                
                # Cerrar modal con ESC
                driver.find_element(By.TAG_NAME, "body").send_keys("\ue00c")
                time.sleep(2)
                
            except Exception as e:
                print(f"      ⚠️ Error en esta empresa, saltando...")
                driver.find_element(By.TAG_NAME, "body").send_keys("\ue00c")

        # Guardar resultados
        with open('lista_final_sena.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
            
        print(f"\n✨ ¡MISIÓN CUMPLIDA! Se guardaron {len(results)} contactos en 'lista_final_sena.json'")
        print("Podes cerrar la ventana del navegador cuando quieras.")
        
        # Mantenemos abierto para que el usuario vea el final
        while True: time.sleep(1)

    except Exception as e:
        print(f"\n💥 Hubo un problema técnico: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_hybrid_bot()
