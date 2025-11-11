# Buscador de Horarios - Toma Ramos

Aplicación web para encontrar automáticamente horarios de clases compatibles basados en el archivo de horarios de Ingeniería Civil en Informática y Telecomunicaciones.

## 🎯 Características

- **Búsqueda automática de horarios**: Encuentra todas las combinaciones válidas de secciones sin conflictos de horario
- **Reglas inteligentes de conflicto**:
  - Las cátedras, laboratorios y ayudantías obligatorias no pueden tener topes de horario
  - Las ayudantías opcionales SÍ pueden tener topes de horario con otras clases
  - Clases en sedes distintas (ej: Huechuraba y Santiago) requieren mínimo 50 minutos de separación
- **Optimización de horarios**: 3 modos de optimización
  - 🌅 **Preferir mañanas**: Genera horarios con clases más temprano en promedio
  - 🌆 **Preferir tardes**: Genera horarios con clases más tarde en promedio
  - ⚡ **Minimizar ventanas**: Genera horarios con menor tiempo vacío entre la primera y última clase de cada día
- **Interfaz intuitiva**: Búsqueda de ramos, selección múltiple y visualización clara de resultados

## 📋 Requisitos

- Python 3.8+
- pip

## 🚀 Instalación y Ejecución

1. Instalar las dependencias:
```bash
pip install -r requirements.txt
```

2. Ejecutar la aplicación:
```bash
python app.py
```

   Para desarrollo con debug activado:
   ```bash
   FLASK_DEBUG=true python app.py
   ```

3. Abrir en el navegador:
```
http://localhost:5000
```

## 📖 Uso

1. **Seleccionar ramos**: En el panel izquierdo, busca y selecciona los ramos que quieres tomar
2. **Elegir optimización** (opcional): Selecciona si prefieres horarios de mañana, tarde, o con menos ventanas
3. **Generar horarios**: Haz clic en "Generar Horarios" para ver todas las combinaciones válidas
4. **Revisar resultados**: Explora las diferentes opciones de horario generadas

## 🏗️ Estructura del Proyecto

```
toma-ramos/
├── app.py                          # Aplicación Flask (servidor web)
├── schedule_processor.py           # Lógica de procesamiento de horarios
├── templates/
│   └── index.html                  # Interfaz web
├── ING_CIVIL_EN_INFOR_Y_TEL.xlsx  # Datos de horarios
├── requirements.txt                # Dependencias Python
└── README.md                       # Este archivo
```

## 🔧 Tecnologías Utilizadas

- **Backend**: Flask (Python)
- **Procesamiento de datos**: pandas, openpyxl
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)

## 📊 Formato de Datos

El archivo Excel debe contener las siguientes columnas:
- Asignatura: Código del ramo (ej: CBF1000)
- Nombre Asig.: Nombre completo del ramo
- Créditos Asignatura: Créditos del ramo
- Sección: Sección del ramo
- Descrip. Evento: Tipo de evento (CÁTEDRA, LABORATORIO, AYUDANTÍA OBLIGATORIA, AYUDANTÍA OPCIONAL)
- Horario: Horario del evento (ej: "MA JU 10:00 - 11:20")
- Profesor: Nombre del profesor
- Sede: Campus donde se imparte (ej: S-SANTIAGO, H-HUECHURABA)
- Paquete: Identificador del paquete de la sección
- Vac. Paquete: Vacantes disponibles

## 🎓 Ejemplo de Uso

1. Seleccionar ramos: CBF1000, CBM1000, CII1000
2. Elegir "Minimizar ventanas"
3. Ver las 50 mejores combinaciones de horarios sin conflictos

## ⚙️ Algoritmo

El sistema:
1. Parsea el archivo Excel y organiza los datos por ramos y secciones
2. Genera todas las combinaciones posibles de secciones para los ramos seleccionados
3. Valida cada combinación:
   - Verifica que no haya conflictos de horario (excepto ayudantías opcionales)
   - Verifica separación mínima entre sedes distintas (50 minutos)
4. Opcionalmente ordena los resultados según el criterio de optimización seleccionado
5. Retorna las mejores combinaciones

## 📝 Notas

- El sistema considera las ayudantías opcionales como flexibles y pueden tener topes de horario
- Las clases en diferentes sedes requieren tiempo de traslado (50 minutos mínimo)
- La optimización se aplica después de encontrar todas las combinaciones válidas
