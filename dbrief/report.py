import dataclasses
import pathlib
import re
from typing import Optional, Union

import hvplot.pandas
import jinja2
import omegaconf
import pandas as pd
from bokeh.embed import file_html
from bokeh.resources import CDN

DEFAULT_ROWS = 7
DEFAULT_LEGEND = "bottom"
HERE = pathlib.Path(__file__)
PKG = HERE.parent
TEMPLATES = PKG.joinpath("templates")


def default_id(title: str) -> str:
    """Create a default HTML ID from a given title."""
    return re.sub("[^0-9a-zA-Z]+", "-", title).lower()


def make_figure(data: pd.DataFrame, cols: list):

    if data.shape[1] >= 2:
        fig = data.hvplot(y=cols, value_label="Value", width=600).opts(
            legend_position=DEFAULT_LEGEND
        )
    else:
        fig = data.hvplot(y=cols, value_label="Value", width=600)

    bk_fig = hvplot.render(fig, backend="bokeh")
    return file_html(bk_fig, CDN)


def make_table(
    data: pd.DataFrame, cols: list, n_rows: int
):
    table = data[cols].tail(n_rows).hvplot.table()
    bk_table = hvplot.render(table, backend="bokeh")
    return file_html(bk_table, CDN)


@dataclasses.dataclass()
class Section:
    title: str
    html_id: str
    components: list


@dataclasses.dataclass()
class Component:
    title: str
    html_id: str
    data: Optional[str] = None
    text: Optional[str] = None
    html: Optional[str] = None


@dataclasses.dataclass()
class Logo:
    image: str
    width: int
    height: int


@dataclasses.dataclass()
class Report:
    name: str

    def __post_init__(self):
        self.schema: omegaconf.DictConfig = omegaconf.OmegaConf.create()
        self.logo: Optional[Logo] = None

    def add_logo(self, image: str, width: int, height: int):
        self.schema.logo = Logo(image=image, width=width, height=height)

    def add_section(self, title: str, html_id: Optional[str] = None):
        self.schema[title] = Section(
            title=title,
            html_id=html_id if html_id else default_id(title),
            components=[],
        )

    def add_subsection(self, section: str, title: str, html_id: Optional[str] = None):
        self.schema[section].components.append(
            Section(
                title=title,
                html_id=html_id if html_id else default_id(title),
                components=[],
            )
        )

    def add_component(
        self,
        section: str,
        title: str,
        html_id: Optional[str] = None,
        data: Optional[str] = None,
        text: Optional[str] = None,
        html: Optional[str] = None,
    ):
        self.schema[section].components.append(
            Component(
                title=title,
                html_id=html_id if html_id else default_id(title),
                data=data,
                text=text,
                html=html,
            )
        )

    def add_figure(
        self,
        section: str,
        title: str,
        data: pd.DataFrame,
        cols: Optional[list] = None,
        html_id: Optional[str] = None,
        include_data: Optional[Union[bool, int]] = None,
        caption: Optional[str] = None,
    ):
        html_id = html_id if html_id else default_id(title)
        fig_path = make_figure(
            data=data, cols=cols if cols else data.columns
        )
        if isinstance(include_data, bool):
            table_path = make_table(
                data=data,
                cols=cols if cols else data.columns,
                n_rows=DEFAULT_ROWS,
            )
        elif isinstance(include_data, int):
            table_path = make_table(
                data=data,
                cols=cols if cols else data.columns,
                n_rows=include_data,
            )
        else:
            table_path = None
        self.add_component(
            section=section,
            title=title,
            html_id=html_id,
            data=table_path,
            text=caption,
            html=fig_path,
        )

    def to_yaml(self, filepath: str):
        meta = omegaconf.OmegaConf.create(
            {"name": self.name, "logo": self.logo.__dict__ if self.logo else None}
        )
        out = omegaconf.OmegaConf.merge(meta, self.schema)
        with open(filepath, "w") as writer:
            writer.write(omegaconf.OmegaConf.to_yaml(out))

    def to_html(self, filepath: str):
        environment = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATES))
        template = environment.get_template("default.html")
        html = template.render(**self.__dict__)
        with open(filepath, "w") as fp:
            fp.write(html)
