import gradio as gr
import functools

from modules import scripts, sd_samplers, sd_schedulers, shared
from modules.infotext_utils import PasteField
from modules.ui_components import FormRow, FormGroup


def get_sampler_from_infotext(d: dict):
    return get_sampler_and_scheduler(d.get("Sampler"), d.get("Schedule type"))[0]


def get_scheduler_from_infotext(d: dict):
    return get_sampler_and_scheduler(d.get("Sampler"), d.get("Schedule type"))[1]


@functools.cache
def get_sampler_and_scheduler(sampler_name, scheduler_name):
    default_sampler = sd_samplers.samplers[0]
    found_scheduler = sd_schedulers.schedulers_map.get(scheduler_name, sd_schedulers.schedulers[0])

    name = sampler_name or default_sampler.name

    for scheduler in sd_schedulers.schedulers:
        name_options = [scheduler.label, scheduler.name, *(scheduler.aliases or [])]

        for name_option in name_options:
            if name.endswith(" " + name_option):
                found_scheduler = scheduler
                name = name[0:-(len(name_option) + 1)]
                break

    sampler = sd_samplers.all_samplers_map.get(name, default_sampler)

    # revert back to Automatic if it's the default scheduler for the selected sampler
    if sampler.options.get('scheduler', None) == found_scheduler.name:
        found_scheduler = sd_schedulers.schedulers[0]

    return sampler.name, found_scheduler.label


class ScriptSampler(scripts.ScriptBuiltinUI):
    section = "sampler"

    def __init__(self):
        self.steps = None
        self.sampler_name = None
        self.scheduler = None

    def title(self):
        return "Sampler"

    def ui(self, is_img2img):
        sampler_names = [x.name for x in sd_samplers.visible_samplers()]
        scheduler_names = [x.label for x in sd_schedulers.schedulers]

        if shared.opts.samplers_in_dropdown:
            with FormRow(elem_id=f"sampler_selection_{self.tabname}"):
                self.sampler_name = gr.Dropdown(label='Sampling method', elem_id=f"{self.tabname}_sampling", choices=sampler_names, value=sampler_names[0])
                self.scheduler = gr.Dropdown(label='Schedule type', elem_id=f"{self.tabname}_scheduler", choices=scheduler_names, value=scheduler_names[0])
                self.steps = gr.Slider(minimum=1, maximum=150, step=1, elem_id=f"{self.tabname}_steps", label="Sampling steps", value=20)
        else:
            with FormGroup(elem_id=f"sampler_selection_{self.tabname}"):
                self.steps = gr.Slider(minimum=1, maximum=150, step=1, elem_id=f"{self.tabname}_steps", label="Sampling steps", value=20)
                self.sampler_name = gr.Radio(label='Sampling method', elem_id=f"{self.tabname}_sampling", choices=sampler_names, value=sampler_names[0])
                self.scheduler = gr.Dropdown(label='Schedule type', elem_id=f"{self.tabname}_scheduler", choices=scheduler_names, value=scheduler_names[0])

        self.infotext_fields = [
            PasteField(self.steps, "Steps", api="steps"),
            PasteField(self.sampler_name, get_sampler_from_infotext, api="sampler_name"),
            PasteField(self.scheduler, get_scheduler_from_infotext, api="scheduler"),
        ]

        return self.steps, self.sampler_name, self.scheduler

    def setup(self, p, steps, sampler_name, scheduler):
        p.steps = steps
        p.sampler_name = sampler_name
        p.scheduler = scheduler
