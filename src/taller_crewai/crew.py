import os

from crewai import Agent, Crew, LLM, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent

from pathlib import Path


# MODELOS
"""
    Se utilizan multimodelos para dividir la carga de trabajo y
    poder conseguir un mejor resultado en menor tiempo al delegarle
    tareas a modelos en la nube y uno local. Elegido Gemini por ser gratuito jajaja
    Neta te lo juro que lo hice yo y no la IA
"""

# Qwen local especializado en codigo
qwen_coder_llm = LLM(
    model=os.getenv(
        "QWEN_MODEL",
        "qwen2.5-coder:7b"
    ),
    custom_openai=True,
    base_url=os.getenv(
        "OLLAMA_BASE_URL",
        "http://localhost:11434/v1"
    ),
    api_key="ollama",
    temperature=0.2,
)


# Gemini ligero
gemini_fast_llm = LLM(
    model=os.getenv(
        "GEMINI_FAST_MODEL",
        "gemini/gemini-3.5-flash-lite"
    ),
    api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.2,
)


# Gemini potente
gemini_strong_llm = LLM(
    model=os.getenv(
        "GEMINI_STRONG_MODEL",
        "gemini/gemini-3.5-flash"
    ),
    api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.1,
)


# CREW

@CrewBase
class TallerCrewai:
    """
    Crew para desarrollar lo de la Hormiga
    """

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    agents: list[BaseAgent]
    tasks: list[Task]

    # AGENTES

    @agent
    def arquitecto(self) -> Agent:
        return Agent(
            config=self.agents_config["arquitecto"],
            llm=gemini_fast_llm,
            verbose=True,
            allow_delegation=False,
            max_iter=6,
        )

    @agent
    def especialista_grafos(self) -> Agent:
        return Agent(
            config=self.agents_config["especialista_grafos"],
            llm=gemini_fast_llm,
            verbose=True,
            allow_delegation=False,
            max_iter=6,
        )

    @agent
    def desarrollador_backend(self) -> Agent:
        return Agent(
            config=self.agents_config["desarrollador_backend"],
            llm=qwen_coder_llm,
            verbose=True,
            allow_delegation=False,
            max_iter=8,
        )

    @agent
    def desarrollador_pyqt(self) -> Agent:
        return Agent(
            config=self.agents_config["desarrollador_pyqt"],
            llm=qwen_coder_llm,
            verbose=True,
            allow_delegation=False,
            max_iter=8,
        )

    @agent
    def integrador(self) -> Agent:
        return Agent(
            config=self.agents_config["integrador"],
            llm=gemini_strong_llm,
            verbose=True,
            allow_delegation=False,
            max_iter=10,
        )

    @agent
    def tester(self) -> Agent:
        return Agent(
            config=self.agents_config["tester"],
            llm=gemini_fast_llm,
            verbose=True,
            allow_delegation=False,
            max_iter=8,
        )

    # TAREAS

    @task
    def disenar_arquitectura(self) -> Task:
        return Task(
            config=self.tasks_config["disenar_arquitectura"],
            agent=self.arquitecto(),
            output_file="artifacts/01_arquitectura.md",
            create_directory=True,
        )

    @task
    def disenar_algoritmos(self) -> Task:
        return Task(
            config=self.tasks_config["disenar_algoritmos"],
            agent=self.especialista_grafos(),
            context=[
                self.disenar_arquitectura()
            ],
            output_file="artifacts/02_algoritmos.md",
            create_directory=True,
        )

    @task
    def implementar_backend(self) -> Task:
        return Task(
            config=self.tasks_config["implementar_backend"],
            agent=self.desarrollador_backend(),
            context=[
                self.disenar_arquitectura(),
                self.disenar_algoritmos(),
            ],
            output_file="artifacts/03_backend.md",
            create_directory=True,
        )

    @task
    def disenar_interfaz(self) -> Task:
        return Task(
            config=self.tasks_config["disenar_interfaz"],
            agent=self.desarrollador_pyqt(),
            context=[
                self.disenar_arquitectura(),
                self.disenar_algoritmos(),
                self.implementar_backend(),
            ],
            output_file="artifacts/04_pyqt.md",
            create_directory=True,
        )

    @task
    def integrar_borrador(self) -> Task:
        return Task(
            config=self.tasks_config["integrar_borrador"],
            agent=self.integrador(),
            context=[
                self.disenar_arquitectura(),
                self.disenar_algoritmos(),
                self.implementar_backend(),
                self.disenar_interfaz(),
            ],
            output_file="hormiga/main_draft.py",
            create_directory=True,
        )

    @task
    def probar_sistema(self) -> Task:
        return Task(
            config=self.tasks_config["probar_sistema"],
            agent=self.tester(),
            context=[
                self.disenar_arquitectura(),
                self.disenar_algoritmos(),
                self.implementar_backend(),
                self.disenar_interfaz(),
                self.integrar_borrador(),
            ],
            output_file="artifacts/05_qa_report.md",
            create_directory=True,
        )

    @task
    def corregir_y_finalizar(self) -> Task:
        return Task(
            config=self.tasks_config["corregir_y_finalizar"],
            agent=self.integrador(),
            context=[
                self.disenar_arquitectura(),
                self.disenar_algoritmos(),
                self.implementar_backend(),
                self.disenar_interfaz(),
                self.integrar_borrador(),
                self.probar_sistema(),
            ],
            output_file="hormiga/main.py",
            create_directory=True,
        )

    @task
    def generar_readme(self) -> Task:
        return Task(
            config=self.tasks_config["generar_readme"],
            agent=self.integrador(),
            context=[
                self.disenar_arquitectura(),
                self.disenar_algoritmos(),
                self.probar_sistema(),
                self.corregir_y_finalizar(),
            ],
            output_file="hormiga/README.md",
            create_directory=True,
        )

    # ESCAPAR LLAVES
    def _escapar_llaves(self, texto: str) -> str:
        return texto.replace("{", "{{").replace("}", "}}")

    # CREW

    # MODO AHORRADOR

    def _leer_artefacto(self, ruta: str) -> str:
        """
        Lee un artefacto previamente generado
        Si no existe, devuelve un aviso para que el integrador
        pueda continuar con los archivos disponibles
        """

        path = Path(ruta)

        if not path.exists():
            return f"\n[No se encontró el archivo {ruta}]\n"

        return path.read_text(
            encoding="utf-8",
            errors="replace"
        )


    def _escapar_llaves(self, texto: str) -> str:
        """
        Hace que CrewAI no interprete
        fragmentos de codigo como variables de plantilla
        Es que tuve varios errores donde CrewAI interpretaba
        fragmentos de codigo como variables de plantilla
        """

        if not texto:
            return texto

        return (
            texto
            .replace("{", "⦃")
            .replace("}", "⦄")
        )


    def _escapar_config(self, config: dict) -> dict:
        """
        Hace una copia del config de una tarea y protege
        description y expected_output
        """

        config = dict(config)

        if "description" in config:
            config["description"] = self._escapar_llaves(
                config["description"]
            )

        if "expected_output" in config:
            config["expected_output"] = self._escapar_llaves(
                config["expected_output"]
            )

        return config


    def resume_crew(self) -> Crew:
        """
        Va a ejecutar:

        1. integrar_borrador
        2. probar_sistema
        3. corregir_y_finalizar
        4. generar_readme

        Reutilizando los artefactos que ya fueron generados
        """

        # LEER ARTEFACTOS ANTERIORES

        arquitectura = self._escapar_llaves(
            self._leer_artefacto(
                "artifacts/01_arquitectura.md"
            )
        )

        algoritmos = self._escapar_llaves(
            self._leer_artefacto(
                "artifacts/02_algoritmos.md"
            )
        )

        backend = self._escapar_llaves(
            self._leer_artefacto(
                "artifacts/03_backend.md"
            )
        )

        interfaz = self._escapar_llaves(
            self._leer_artefacto(
                "artifacts/04_pyqt.md"
            )
        )


        # CONTEXTO PREVIO

        contexto_previo = f"""
------------------------------------------------------------
ARQUITECTURA YA GENERADA
------------------------------------------------------------

{arquitectura}

------------------------------------------------------------
ALGORITMOS YA GENERADOS
------------------------------------------------------------

{algoritmos}

------------------------------------------------------------
BACKEND YA GENERADO
------------------------------------------------------------

{backend}

------------------------------------------------------------
INTERFAZ PYQT YA GENERADA
------------------------------------------------------------

{interfaz}

------------------------------------------------------------
INSTRUCCION IMPORTANTE
------------------------------------------------------------

Las cuatro fases anteriores YA FUERON EJECUTADAS.

NO debes volver a diseñarlas desde cero.

Utiliza el contenido anterior como contexto técnico.

Tu responsabilidad ahora es integrar, verificar y corregir
el proyecto final.

Si alguno de los documentos anteriores contiene código
incompleto, inconsistencias, respuestas genéricas o errores,
NO debes copiarlo ciegamente.

Debes implementar tú mismo cualquier parte faltante para
producir una aplicación completamente funcional.

Debes mantener todos los requisitos del proyecto:

- Python 3.12
- PyQt6
- laberinto procedural
- Randomized DFS con backtracking
- apertura adicional de paredes para generar ciclos
- grafo no dirigido y no ponderado
- BFS real utilizando FIFO
- DFS real utilizando LIFO
- entre 5 y 7 comidas
- búsqueda multiobjetivo
- remaining_foods
- found_target
- recolección secuencial de comidas
- búsqueda final hacia la salida
- QTimer
- interfaz no bloqueante
- árbol de búsqueda
- estadísticas acumuladas
- drag and drop de la hormiga
- validación de posición al soltar la hormiga
- impedir colocar la hormiga sobre paredes
- impedir colocar la hormiga sobre comidas
- impedir colocar la hormiga sobre la salida
- bloquear drag and drop durante la simulación
- dibujo reconocible de hormiga mediante QPainter
- cabeza
- tórax
- abdomen
- seis patas
- dos antenas
"""


        # INTEGRAR BORRADOR

        integrar_config = self._escapar_config(
            self.tasks_config["integrar_borrador"]
        )

        integrar_config["description"] = (
            integrar_config["description"]
            + "\n\n"
            + contexto_previo
            + """

------------------------------------------------------------
VALIDACIONES EXTRA DE INTEGRACION
------------------------------------------------------------

Debes producir un único archivo Python autocontenido.

Antes de entregar el borrador verifica:

- todos los imports existen
- todas las clases existen
- las clases están definidas antes de utilizarse cuando sea necesario
- no existen referencias a nombres inexistentes
- todos los métodos llamados están implementados
- QMouseEvent se importa desde PyQt6.QtGui
- QPainter se importa desde PyQt6.QtGui
- QTimer se importa desde PyQt6.QtCore
- no utilizar time.sleep() en la interfaz
- no dejar TODO
- no dejar pass provisional
- no entregar explicaciones
- no entregar Markdown
- no utilizar bloques ```python

El archivo debe poder ejecutarse posteriormente con:

python hormiga/main_draft.py
"""
        )

        tarea_integrar = Task(
            config=integrar_config,
            agent=self.integrador(),
            output_file="hormiga/main_draft.py",
            create_directory=True,
        )


        # QA

        probar_config = self._escapar_config(
            self.tasks_config["probar_sistema"]
        )

        probar_config["description"] = (
            probar_config["description"]
            + """

------------------------------------------------------------
MODO AHORRADOR
------------------------------------------------------------

Las fases de arquitectura, algoritmos, backend e interfaz
ya fueron ejecutadas anteriormente.

Debes auditar específicamente el archivo generado ahora
por el integrador.

No asumas que funciona solamente porque fue generado.

Comprueba especialmente:

1. Sintaxis Python válida.
2. Imports válidos.
3. PyQt6 correctamente importado.
4. QMouseEvent desde PyQt6.QtGui.
5. Ausencia de NameError.
6. Ausencia de AttributeError.
7. Ausencia de clases utilizadas antes de existir.
8. Type hints válidos.
9. Todos los métodos invocados existen.
10. BFS utiliza deque y FIFO real.
11. DFS utiliza pila y LIFO real.
12. BFS y DFS aceptan múltiples objetivos.
13. La condición de objetivo permite encontrar cualquiera
    de las comidas restantes.
14. found_target identifica la comida encontrada.
15. remaining_foods se actualiza correctamente.
16. Se generan entre 5 y 7 comidas.
17. Todas las comidas son alcanzables.
18. La salida es alcanzable.
19. La salida solamente se busca después de recoger
    todas las comidas.
20. La hormiga se mueve visualmente por el camino.
21. La animación utiliza QTimer.
22. No existe time.sleep() en el hilo de UI.
23. El drag and drop funciona.
24. La hormiga puede agarrarse con el mouse.
25. La hormiga puede moverse visualmente durante el drag.
26. Un drop válido actualiza ant_position.
27. Un drop inválido conserva la posición anterior.
28. No puede soltarse sobre paredes.
29. No puede soltarse sobre comida.
30. No puede soltarse sobre la salida.
31. No puede soltarse fuera del tablero.
32. El drag está bloqueado durante BFS o DFS.
33. La hormiga tiene cabeza.
34. La hormiga tiene tórax.
35. La hormiga tiene abdomen.
36. La hormiga tiene seis patas.
37. La hormiga tiene dos antenas.
38. El dibujo escala con el tamaño de la celda.
39. El botón Nuevo Laberinto funciona.
40. Reiniciar búsqueda funciona.
41. Pausar funciona.
42. Reanudar funciona.
43. El selector BFS/DFS funciona.
44. Las estadísticas se actualizan.
45. El árbol de búsqueda se muestra correctamente.

Para cada problema encontrado indica:

- gravedad
- causa
- ubicación aproximada
- corrección necesaria
"""
        )

        tarea_probar = Task(
            config=probar_config,
            agent=self.tester(),
            context=[
                tarea_integrar
            ],
            output_file="artifacts/05_qa_report.md",
            create_directory=True,
        )


        # CORREGIR Y FINALIZAR

        corregir_config = self._escapar_config(
            self.tasks_config["corregir_y_finalizar"]
        )

        corregir_config["description"] = (
            corregir_config["description"]
            + """

------------------------------------------------------------
CORRECCION DESPUES DE REANUDAR
------------------------------------------------------------

Debes utilizar:

1. El código completo del borrador integrado.
2. El reporte completo generado por QA.

Corrige TODOS los errores detectados.

No ignores errores aunque parezcan pequeños.

Antes de entregar verifica especialmente:

- que ningún type hint haga referencia a una clase inexistente
- que las clases estén declaradas correctamente
- que no haya imports incorrectos
- que QMouseEvent venga de PyQt6.QtGui
- que QPainter venga de PyQt6.QtGui
- que QTimer venga de PyQt6.QtCore
- que todas las clases utilizadas existan
- que todos los métodos llamados existan
- que no haya variables sin definir
- que no haya NameError
- que no haya AttributeError
- que no haya código Markdown
- que no existan bloques ```python
- que no haya TODO
- que no haya pass provisional
- que no haya pseudocódigo dentro del archivo final

------------------------------------------------------------
HORMIGA INTERACTIVA FINAL
------------------------------------------------------------

La versión final debe permitir:

- hacer click sobre la hormiga
- arrastrarla
- verla moverse con el cursor
- soltarla sobre una celda válida

Una celda válida debe:

- estar dentro del tablero
- ser transitable
- no ser pared
- no contener comida
- no ser la salida

Si el destino no es válido:

la hormiga debe permanecer en la posición anterior.

El drag and drop debe estar bloqueado mientras una
simulación BFS o DFS esté activa.

------------------------------------------------------------
FORMA DE HORMIGA
------------------------------------------------------------

La hormiga debe dibujarse utilizando QPainter.

Debe ser reconocible visualmente.

Debe contener:

- cabeza
- tórax
- abdomen
- seis patas
- dos antenas

No debe ser solamente un círculo, cuadrado o emoji.

Debe escalar proporcionalmente con la celda.

------------------------------------------------------------
ARCHIVO FINAL
------------------------------------------------------------

El resultado debe ser únicamente código Python válido.

Debe contener:

def main()

y:

if __name__ == "__main__":

Debe poder ejecutarse mediante:

python hormiga/main.py
"""
        )

        tarea_corregir = Task(
            config=corregir_config,
            agent=self.integrador(),
            context=[
                tarea_integrar,
                tarea_probar,
            ],
            output_file="hormiga/main.py",
            create_directory=True,
        )


            # README

        readme_config = self._escapar_config(
            self.tasks_config["generar_readme"]
        )

        readme_config["description"] = (
            readme_config["description"]
            + """

------------------------------------------------------------
README FINAL
------------------------------------------------------------

Documenta también:

- cómo mover manualmente la hormiga
- restricciones del drag and drop
- cómo iniciar BFS
- cómo iniciar DFS
- cómo pausar
- cómo reanudar
- cómo reiniciar
- cómo generar un nuevo laberinto
- significado de los colores
- funcionamiento de las comidas
- funcionamiento de la salida
- funcionamiento del árbol de búsqueda
- estadísticas mostradas

Incluye una sección:

"Explicación"

explicando claramente que existen dos usos distintos de DFS:

1. DFS aleatorio con backtracking para generar el laberinto.
2. DFS como algoritmo de búsqueda seleccionado por el usuario.

También explica la diferencia entre BFS y DFS.
"""
        )

        tarea_readme = Task(
            config=readme_config,
            agent=self.integrador(),
            context=[
                tarea_probar,
                tarea_corregir,
            ],
            output_file="hormiga/README.md",
            create_directory=True,
        )


        # CREW REDUCIDA

        return Crew(
            agents=[
                self.integrador(),
                self.tester(),
            ],
            tasks=[
                tarea_integrar,
                tarea_probar,
                tarea_corregir,
                tarea_readme,
            ],
            process=Process.sequential,
            verbose=True,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )