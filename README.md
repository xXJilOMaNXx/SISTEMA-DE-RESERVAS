# Guía rápida para ejecutar el proyecto Hotel VE2

## 1. Eliminar el entorno virtual anterior (si existe)
En la terminal de PowerShell, ejecuta:
```powershell
Remove-Item -Recurse -Force .\venv
```

## 2. Crear un nuevo entorno virtual
```powershell
python -m venv venv
```

## 3. Activar el entorno virtualcls
```powershell
.\venv\Scripts\Activate.ps1
```

## 4. Instalar las dependencias
```powershell
pip install -r requerements.txt
```

## 5. Ejecutar la aplicación
```powershell
python app.py
```

---

**Notas:**
- Si ves un error como `ModuleNotFoundError: No module named 'flask'`, asegúrate de haber activado el entorno virtual y de haber instalado las dependencias.
- Si tienes problemas con la activación en PowerShell, puedes probar en CMD con:
  ```cmd
  .\venv\Scripts\activate.bat
  ```
- El archivo de dependencias se llama `requerements.txt`. Si lo renombras a `requirements.txt`, recuerda cambiar el comando de instalación.