"""Analytics service — pre-computed analytics queries (stub for Phase 2/4)."""


class AnalyticsService:
    """Provides pre-computed analytics for the dashboard endpoints."""

    def __init__(self):
        pass

    async def get_opportunities(self):
        """Return the opportunity comparison matrix."""
        raise NotImplementedError("Analytics will be implemented in Phase 2/4")

    async def get_memory_cues(self):
        """Return aggregated memory cue frequency data."""
        raise NotImplementedError("Analytics will be implemented in Phase 2/4")

    async def get_failure_modes(self):
        """Return failure mode distribution."""
        raise NotImplementedError("Analytics will be implemented in Phase 2/4")

    async def get_archetypes(self):
        """Return retrieval archetype profiles."""
        raise NotImplementedError("Analytics will be implemented in Phase 2/4")
