from pydantic import BaseModel, ConfigDict, Field, PositiveFloat, PositiveInt, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class RateCard(StrictModel):
    currency: str
    hours_per_week: PositiveInt
    rates: dict[str, PositiveFloat] = Field(min_length=1)

    def rate_for(self, role: str) -> float:
        return self.rates[role]


class Task(StrictModel):
    name: str = Field(min_length=1)
    role: str
    hours: PositiveFloat

    def cost(self, rate_card: RateCard) -> float:
        return self.hours * rate_card.rate_for(self.role)


class TeamMember(StrictModel):
    role: str
    count: PositiveInt = 1
    dedication: float = Field(default=1.0, gt=0, le=1)

    @property
    def fte(self) -> float:
        return self.count * self.dedication


class DurationWeeks(StrictModel):
    min: PositiveInt
    max: PositiveInt

    @model_validator(mode="after")
    def check_range(self) -> "DurationWeeks":
        if self.min > self.max:
            raise ValueError(f"min ({self.min}) no puede ser mayor que max ({self.max})")
        return self


class Estimation(StrictModel):
    title: str
    tasks: list[Task] = Field(min_length=1)
    team: list[TeamMember] = Field(min_length=1)
    duration_weeks: DurationWeeks
    notes: str | None = None

    @property
    def total_hours(self) -> float:
        return sum(task.hours for task in self.tasks)

    @property
    def task_roles(self) -> set[str]:
        return {task.role for task in self.tasks}

    def total_cost(self, rate_card: RateCard) -> float:
        return sum(task.cost(rate_card) for task in self.tasks)

    def hours_by_role(self) -> dict[str, float]:
        hours: dict[str, float] = {}
        for task in self.tasks:
            hours[task.role] = hours.get(task.role, 0) + task.hours
        return hours

    def fte_by_role(self) -> dict[str, float]:
        fte: dict[str, float] = {}
        for member in self.team:
            fte[member.role] = fte.get(member.role, 0) + member.fte
        return fte

    @model_validator(mode="after")
    def check_team_covers_tasks(self) -> "Estimation":
        missing = self.task_roles - {member.role for member in self.team}
        if missing:
            raise ValueError(f"el equipo no cubre los roles: {sorted(missing)}")
        return self

    def check_roles(self, rate_card: RateCard) -> None:
        roles = self.task_roles | {member.role for member in self.team}
        unknown = roles - rate_card.rates.keys()
        if unknown:
            raise ValueError(f"roles sin tarifa: {sorted(unknown)}")

    def capacity_issues(self, rate_card: RateCard) -> list[str]:
        weeks = self.duration_weeks.max
        fte = self.fte_by_role()
        issues = []
        for role, hours in self.hours_by_role().items():
            capacity = fte[role] * rate_card.hours_per_week * weeks
            if capacity < hours:
                issues.append(
                    f"el equipo no llega en {role}: {capacity:.0f} h de capacidad en "
                    f"{weeks} semanas para {hours:.0f} h de trabajo"
                )
        return issues


class EstimationExample(Estimation):
    id: str
    sector: str
    meeting_summary: str = Field(min_length=50)

    def estimation_only(self) -> Estimation:
        return Estimation.model_validate(self.model_dump(include=set(Estimation.model_fields)))
