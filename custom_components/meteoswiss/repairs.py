"""Native confirmation for removing obsolete forecast statistics."""

from homeassistant.components.repairs import RepairsFlow, RepairsFlowResult
from homeassistant.core import HomeAssistant
import voluptuous as vol

from .const import DOMAIN
from .hgt_cleanup import ISSUE, async_confirm_cleanup, async_plan_cleanup


class HgtCleanupRepairFlow(RepairsFlow):
    """Recommend full removal and show the exact rows before consent."""

    def __init__(self, entry_id: str) -> None:
        self.entry_id = entry_id
        self._plan = None

    async def async_step_init(self, user_input=None) -> RepairsFlowResult:
        # Core may supply issue_id as init data. Opening the repair is never consent.
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input=None) -> RepairsFlowResult:
        errors = {}
        try:
            if self._plan is None:
                self._plan = await async_plan_cleanup(self.hass, self.entry_id)
            if user_input is not None:
                await async_confirm_cleanup(self.hass, self.entry_id, self._plan)
                return self.async_create_entry(data={})
        except Exception:
            # A timed-out native write may still finish. Never repeat it here.
            self._plan = None
            errors["base"] = "cleanup_not_verified"
        return self.async_show_form(
            step_id="confirm", data_schema=vol.Schema({}), errors=errors,
            description_placeholders={
                "statistic_ids": "\n".join(sorted(self._plan.metadata)) if self._plan is not None else "",
            },
        )


async def async_create_fix_flow(
    hass: HomeAssistant, issue_id: str, data: dict | None
) -> HgtCleanupRepairFlow:
    """Bind the flow to the actual entry and issue; no CLI or arbitrary ID input."""
    if not data or issue_id != f"{ISSUE}_{data.get('entry_id')}":
        raise ValueError("unknown_cleanup_issue")
    entry_id = data["entry_id"]
    entry = hass.config_entries.async_get_entry(entry_id)
    if entry is None or entry.domain != DOMAIN:
        raise ValueError("entry_unavailable")
    return HgtCleanupRepairFlow(entry_id)
