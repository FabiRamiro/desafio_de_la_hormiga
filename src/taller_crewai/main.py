#!/usr/bin/env python

import os
import sys
import warnings

from datetime import datetime

from taller_crewai.crew import TallerCrewai


warnings.filterwarnings(
    "ignore",
    category=SyntaxWarning,
    module="pysbd"
)


def get_inputs():
    return {
        "project_name": "Desafío de la Hormiga",
        "current_year": str(datetime.now().year),
    }


def run():
    inputs = get_inputs()

    resume_mode = os.getenv(
        "CREW_RESUME",
        "0"
    ).lower() in {
        "1",
        "true",
        "yes",
        "si",
        "sí"
    }

    try:

        # MODO AHORRADOR DE TOKENS

        if resume_mode:

            print("\n")
            print("=" * 70)
            print("MODO AHORRADOR ACTIVADO")
            print("=" * 70)

            print(
                "\nSe reutilizaran los artefactos existentes:"
            )

            print(
                "  artifacts/01_arquitectura.md"
            )

            print(
                "  artifacts/02_algoritmos.md"
            )

            print(
                "  artifacts/03_backend.md"
            )

            print(
                "  artifacts/04_pyqt.md"
            )

            print("\nSe ejecutaran solamente:")

            print(
                "  1. integrar_borrador"
            )

            print(
                "  2. probar_sistema"
            )

            print(
                "  3. corregir_y_finalizar"
            )

            print(
                "  4. generar_readme"
            )

            print("=" * 70)

            result = (
                TallerCrewai()
                .resume_crew()
                .kickoff(
                    inputs=inputs
                )
            )

        # MODO COMPLETO

        else:

            print("\n")
            print("=" * 70)
            print("MODO COMPLETO")
            print("=" * 70)

            result = (
                TallerCrewai()
                .crew()
                .kickoff(
                    inputs=inputs
                )
            )

        print("\n")
        print("=" * 70)
        print("CREW FINALIZADA CORRECTAMENTE")
        print("=" * 70)

        print("\nArchivos finales:")

        print(
            "  hormiga/main.py"
        )

        print(
            "  hormiga/README.md"
        )

        print("\nReporte QA:")

        print(
            "  artifacts/05_qa_report.md"
        )

        print("\nPara ejecutar la aplicacion:")

        print(
            "  python hormiga/main.py"
        )

        print("=" * 70)

        return result

    except Exception as e:

        raise Exception(
            f"Error al ejecutar la crew: {e}"
        ) from e


def train():
    inputs = get_inputs()

    try:
        TallerCrewai().crew().train(
            n_iterations=int(sys.argv[1]),
            filename=sys.argv[2],
            inputs=inputs,
        )

    except Exception as e:
        raise Exception(
            f"Error durante el entrenamiento: {e}"
        ) from e


def replay():
    try:
        TallerCrewai().crew().replay(
            task_id=sys.argv[1]
        )

    except Exception as e:
        raise Exception(
            f"Error durante replay: {e}"
        ) from e


def test():
    inputs = get_inputs()

    try:
        TallerCrewai().crew().test(
            n_iterations=int(sys.argv[1]),
            eval_llm=sys.argv[2],
            inputs=inputs,
        )

    except Exception as e:
        raise Exception(
            f"Error durante test: {e}"
        ) from e


if __name__ == "__main__":
    run()