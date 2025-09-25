import subprocess
import sys
import os

def run_translation_script():
    """Ejecutar el script de traducciones manuales"""
    try:
        # Cambiar al directorio del proyecto
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        os.chdir(project_dir)
        
        print("🌍 Ejecutando script de traducciones manuales...")
        
        # Ejecutar el script de traducciones manuales
        result = subprocess.run([
            sys.executable, 
            'scripts/create_manual_translations.py'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Script ejecutado exitosamente!")
            print(result.stdout)
        else:
            print("❌ Error ejecutando script:")
            print(result.stderr)
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = run_translation_script()
    if success:
        print("\n🎉 ¡Sistema de internacionalización configurado exitosamente!")
        print("\n📋 Próximos pasos:")
        print("1. Reinicia el servidor Django: python manage.py runserver")
        print("2. Ve a cualquier página del sistema")
        print("3. Verás el selector de idioma en la esquina superior derecha")
        print("4. Cambia entre español e inglés para probar las traducciones")
        print("5. El idioma se guardará automáticamente en las cookies del navegador")
    else:
        print("\n❌ Hubo errores en la configuración. Revisa los mensajes anteriores.")
