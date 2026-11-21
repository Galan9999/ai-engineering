from app.context.models import Estimation, RateCard


def _number(value: float) -> str:
    return f"{value:,.0f}".replace(",", ".")


def render_markdown(estimation: Estimation, rate_card: RateCard) -> str:
    currency = rate_card.currency
    lines = [
        f"## Estimación: {estimation.title}",
        "",
        "### Desglose de tareas",
        "",
        "| Tarea | Rol | Horas | Coste |",
        "|---|---|---:|---:|",
    ]
    for task in estimation.tasks:
        lines.append(
            f"| {task.name} | {task.role} | {_number(task.hours)} | "
            f"{_number(task.cost(rate_card))} {currency} |"
        )
    lines += [
        "",
        f"**Total estimado: {_number(estimation.total_hours)} horas · "
        f"{_number(estimation.total_cost(rate_card))} {currency}**",
        "",
        "### Equipo recomendado",
        "",
    ]
    for member in estimation.team:
        lines.append(f"- {member.count} × {member.role} ({member.dedication:.0%} de dedicación)")
    duration = estimation.duration_weeks
    weeks = str(duration.min) if duration.min == duration.max else f"{duration.min}-{duration.max}"
    lines += ["", f"**Duración estimada: {weeks} semanas**"]
    if estimation.notes:
        lines += ["", "### Notas", "", estimation.notes.strip()]
    return "\n".join(lines) + "\n"
