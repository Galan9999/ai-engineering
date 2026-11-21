import json
from collections.abc import Iterable
from typing import Any

from app.context.models import Estimation, EstimationExample, RateCard

TOOL_NAME = "submit_estimation"
TOOL_DESCRIPTION = (
    "Entrega la estimación del proyecto con su desglose de tareas, equipo y duración."
)


def estimation_schema(rate_card: RateCard) -> dict[str, Any]:
    schema = Estimation.model_json_schema()
    roles = sorted(rate_card.rates)
    for model in ("Task", "TeamMember"):
        schema["$defs"][model]["properties"]["role"]["enum"] = roles
    return schema


def render_example(example: EstimationExample) -> str:
    estimation = example.estimation_only().model_dump(exclude_none=True)
    return "\n".join(
        [
            f'<example id="{example.id}">',
            f"<sector>{example.sector}</sector>",
            f"<meeting_summary>\n{example.meeting_summary.strip()}\n</meeting_summary>",
            f"<estimation>\n{json.dumps(estimation, ensure_ascii=False)}\n</estimation>",
            "</example>",
        ]
    )


def build_system_prompt(examples: Iterable[EstimationExample], rate_card: RateCard) -> str:
    roles = ", ".join(sorted(rate_card.rates))
    rendered = "\n\n".join(render_example(example) for example in examples)
    return f"""<role>
Eres un estimador senior de proyectos de software en una consultora. Conviertes la
transcripción de una reunión con un cliente en una estimación de esfuerzo que un jefe de
proyecto pueda presentar.
</role>

<instructions>
1. Identifica el alcance que pide el cliente, sus plazos y sus restricciones.
2. Desglosa el trabajo en tareas concretas y asigna cada una a un único rol.
3. Propón el equipo (rol, número de personas y dedicación entre 0 y 1) y una duración en
   semanas (mínimo y máximo) coherentes con las horas de cada rol a
   {rate_card.hours_per_week} horas por semana.
4. En notes, explica los supuestos, lo que queda fuera del alcance y los riesgos.
5. Usa los ejemplos como referencia de granularidad, horas y criterio. No los copies: estima el
   proyecto de la transcripción.
6. Entrega la estimación llamando a la herramienta {TOOL_NAME}.
</instructions>

<rate_card>
Roles disponibles: {roles}.
</rate_card>

<examples>
{rendered}
</examples>

<constraints>
- No calcules costes ni totales: los calcula el sistema a partir de tus horas.
- No inventes requisitos que no aparezcan en la transcripción. Si falta información, estímala con un
  supuesto razonable y escríbelo en notes.
- Cada tarea debe tener su rol en el equipo.
- Escribe en español.
</constraints>"""


def build_user_message(transcription: str) -> str:
    return f"<transcription>\n{transcription.strip()}\n</transcription>"
