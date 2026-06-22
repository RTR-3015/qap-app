# QAP Solver — Aplicación Web para el Problema de Asignación Cuadrática

Aplicación web desarrollada en **Flask** para resolver el Problema de
Asignación Cuadrática (QAP) mediante un procedimiento heurístico de dos fases:
construcción + mejora.

## 1. Estructura del proyecto

```
qap_app/
├── app.py                     # Aplicación Flask (rutas y lógica web)
├── requirements.txt
│
├── qap/                       # Núcleo del algoritmo (sin dependencias web)
│   ├── utils.py                -> cálculo de costo, validaciones
│   ├── construccion.py         -> heurísticos de la Fase 1
│   └── mejora.py                -> heurísticos de la Fase 2
│
├── reportes/                   # Generación de reportes
│   ├── generador_excel.py
│   └── generador_pdf.py
│
├── templates/                  # Vistas HTML (Jinja2 + Bootstrap 5)
│   ├── base.html
│   ├── index.html
│   ├── captura_matrices.html
│   ├── configurar.html
│   └── resultados.html
│
├── static/css/estilos.css
│
└── data/ejemplos/               # Matrices CSV de ejemplo para probar importación
```

## 2. Cómo ejecutarlo en PyCharm

1. Abre la carpeta `qap_app` como proyecto en PyCharm (File → Open).
2. Crea/selecciona un entorno virtual de Python 3.10+ (Settings → Project →
   Python Interpreter).
3. Abre la terminal integrada e instala las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

4. Ejecuta `app.py` (clic derecho → Run, o botón ▶ verde).
5. Abre en el navegador la URL que indique la consola
   (normalmente `http://127.0.0.1:5000`).

## 3. Heurísticos implementados

### Fase 1 — Construcción (5 métodos)
- **Método Greedy (costo combinado)**: en cada paso elige el par
  departamento-ubicación que produce el menor incremento de costo
  acumulado, evaluando flujo y distancia conjuntamente.
- **Asignación basada en mayores flujos**: asigna primero los departamentos
  con mayor flujo total a las ubicaciones más "centrales".
- **Asignación basada en menores costos**: recorre los departamentos en
  orden fijo y a cada uno le asigna la ubicación libre de menor costo
  marginal.
- **Construcción aleatorizada**: genera una permutación aleatoria.
- **Construcción semi-greedy**: en cada paso elige aleatoriamente entre las
  mejores opciones disponibles (parámetro `alpha`), combinando criterio y
  diversidad.

### Fase 2 — Mejora (5 métodos)
- **Swap (primera mejora)**: recorre los pares en orden aleatorio y aplica
  el primer intercambio que reduzca el costo (first-improvement).
- **Búsqueda local con perturbación**: aplica primera mejora hasta
  estancarse, luego perturba aleatoriamente la solución y continúa
  buscando, conservando siempre la mejor encontrada.
- **Descenso de máxima pendiente**: evalúa TODOS los intercambios posibles
  en cada iteración y aplica el mejor (best-improvement).
- **Recocido simulado**: acepta intercambios que empeoran la solución con
  una probabilidad que disminuye con la temperatura, permitiendo escapar de
  óptimos locales.
- **Búsqueda tabú**: prohíbe revertir movimientos recientes durante un
  número fijo de iteraciones, evitando ciclos, con criterio de aspiración
  para permitir movimientos tabú si mejoran el mejor costo conocido.

Todos los heurísticos de mejora usan cálculo incremental del costo (delta),
no recalculan la función objetivo completa en cada paso — esto es
importante para que la app responda rápido incluso con problemas medianos
(n ≈ 20-30).

## 4. Validación y generación de datos

En la pantalla de captura manual de matrices:
- **✅ Validar datos**: verifica que la diagonal principal sea 0 en ambas
  matrices y que no existan valores negativos. Muestra el detalle exacto
  de las celdas con problema si algo falla. Esta misma validación se aplica
  automáticamente al intentar guardar las matrices.
- **🎲 Generar datos aleatorios**: rellena ambas matrices con valores
  aleatorios dentro de un rango que tú eliges (mínimo y máximo), respetando
  automáticamente las reglas (diagonal en 0, sin negativos).

### Formato de archivos para importar

Los archivos CSV/Excel deben contener **únicamente números**, sin encabezados
de texto. Cada archivo debe ser una matriz cuadrada n×n. Se incluyen ejemplos
en `data/ejemplos/`.

## 5. Despliegue en la nube — paso a paso (PyCharm → GitHub → Render)

Esta es la ruta recomendada para que la app sea accesible desde **cualquier
computadora**, sin que nadie necesite instalar Python ni el proyecto.

### Paso 1 — Subir el proyecto a GitHub desde PyCharm

1. Abre el proyecto en PyCharm.
2. Menú **VCS → Create Git Repository...** y selecciona la carpeta raíz.
3. Menú **VCS → Commit...** (o el ícono ✓ del panel lateral). Verifica que
   **no** aparezcan `.venv/`, `.idea/` ni `__pycache__/` en la lista de
   archivos (el `.gitignore` incluido ya los excluye). Escribe un mensaje,
   por ejemplo "Primera versión", y da clic en **Commit**.
4. Menú **Git → Push...** (o **VCS → Git → Push**).
5. Si es la primera vez, PyCharm te pedirá iniciar sesión con tu cuenta de
   GitHub y crear el repositorio remoto — sigue el asistente, dale un nombre
   (ej. `qap-solver`) y confirma que sea público o privado según prefieras.
6. Confirma el Push. Tu código ya está en GitHub.

### Paso 2 — Crear el servicio en Render

1. Crea una cuenta gratuita en [render.com](https://render.com) (puedes
   entrar directamente con tu cuenta de GitHub).
2. En el Dashboard: **New → Web Service**.
3. Conecta tu cuenta de GitHub si no lo has hecho, y selecciona el
   repositorio `qap-solver` (o el nombre que le hayas dado).
4. Render detectará automáticamente el archivo `render.yaml` incluido en
   este proyecto y configurará todo solo (build y start command). Si no lo
   detecta automáticamente, configúralo manualmente:
   - **Build command**: `pip install -r requirements.txt`
   - **Start command**: `gunicorn app:app`
   - **Plan**: Free
5. Clic en **Create Web Service**. Render empezará a instalar dependencias
   y desplegar — esto tarda 2-5 minutos la primera vez.
6. Cuando termine, verás una URL pública arriba, algo como:
   `https://qap-solver.onrender.com`

Esa URL es la que puedes compartir con cualquier persona — la abren desde
su navegador (computadora, celular, tablet) sin instalar absolutamente
nada.

> **Nota sobre el plan gratuito de Render**: el servicio "duerme" tras
> ~15 minutos de inactividad, y la primera petición después de eso tarda
> unos 30-50 segundos en "despertar". Para un proyecto académico esto es
> normal y aceptable; si necesitas que esté siempre activa al instante,
> existen planes pagados desde unos pocos dólares al mes.

### Actualizar la app tras hacer cambios

Cada vez que modifiques el código:
1. **VCS → Commit...** → escribe el mensaje → **Commit**.
2. **Git → Push**.
3. Render detecta el nuevo Push automáticamente y vuelve a desplegar solo
   (puedes ver el progreso en la pestaña "Events" de tu servicio en Render).

### Opciones alternativas

- **Railway.app**: mismo flujo (GitHub → conectar repo), también detecta
  Python automáticamente; usa `gunicorn app:app` como start command.
- **PythonAnywhere**: útil si prefieres subir archivos manualmente sin usar
  Git, desde su panel web.

> **Importante para producción real**: cambia `app.secret_key` en `app.py`
> por una variable de entorno segura (en Render: Settings → Environment →
> Add Environment Variable), y considera mover el almacenamiento de
> resultados (`session`) a una base de datos si esperas muchos usuarios
> usando la app al mismo tiempo.

## 6. Próximos pasos sugeridos

- Agregar autenticación de usuarios si se requiere control de acceso.
- Guardar historial de experimentos en una base de datos (SQLite/PostgreSQL)
  para comparar ejecuciones pasadas.
- Agregar gráficas (por ejemplo con Chart.js) que muestren la convergencia
  del recocido simulado.
- Agregar más heurísticos (búsqueda tabú, GRASP, algoritmos genéticos) como
  módulos adicionales dentro de `qap/mejora.py` o `qap/construccion.py`.
